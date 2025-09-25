import discord
from discord.ext import commands
import aiohttp
import os
import base64
import re
from io import BytesIO
from dotenv import load_dotenv
import asyncio
import functools

# Load your Discord token securely from a .env file
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
LOCALAI_URL = os.getenv('LOCALAI_CHAT_URL')
LOCALAI_IMAGE_URL = os.getenv('LOCALAI_IMAGE_URL')
MODEL_GEMMA = os.getenv('MODEL_GEMMA')
MODEL_FALCON = os.getenv('falcon3-3b-instruct-abliterated')
MODEL_DREAMSHAPER = os.getenv('dreamshaper')

CHAT_TEMPERATURE = os.getenv('CHAT_TEMPERATURE')
MESSAGE_CHARACTER_LIMIT = os.getenv('MESSAGE_CHARACTER_LIMIT')
IMAGE_SIZE = os.getenv('IMAGE_SIZE')

# ANSI escape codes for colors
RESET = os.getenv('RESET')
red = os.getenv('red')
green = os.getenv('green')
yellow = os.getenv('yellow')
blue = os.getenv('blue')
magenta	= os.getenv('magenta')
cyan = os.getenv('cyan')
BOLD = os.getenv('BOLD')

SYSTEM_PROMPT = os.getenv('SYSTEM_PROMPT')

# Discord Bot Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def animate_thinking(message):
    """Animates the "..." message."""
    dots = ""
    while True:
        dots = dots + "." if len(dots) < 3 else ""
        try:
            await message.edit(content=f"Thinking{dots}")
        except (discord.errors.NotFound, discord.errors.Forbidden):
            return
        await asyncio.sleep(1)

def remove_assistant_prefix(text):
    """
    Removes a prefix like '[number] - <|assistant|>' from the beginning of a string.
    If the pattern does not exist, the original string is returned.
    """
    # The `^` anchor ensures the match only happens at the start of the string
    pattern = r'^\d+\s-\s<\|assistant\|>'
    # Replace the pattern with an empty string
    return re.sub(pattern, '', text).strip()


async def fetch_and_encode_image(session, url):
    """Fetches an image from a URL and returns it as a Base64 string using aiohttp."""
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            img_buffer = BytesIO(await response.read())
            base64_encoded_image = base64.b64encode(img_buffer.read()).decode("utf-8")
            return f"data:{response.headers['content-type']};base64,{base64_encoded_image}"
    except aiohttp.ClientError as e:
        print(f"Error fetching image: {e}")
        return None

@bot.event
async def on_ready():
    print(f'{BOLD}{yellow}{bot.user}{RESET} is {BOLD}{green}Online{RESET}')

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself to prevent infinite loops
    if message.author == bot.user:
        return

    # In a DM channel, handle non-command messages as an `ask`
    is_dm = isinstance(message.channel, discord.DMChannel)
    if is_dm and not message.content.startswith('!generate'):
        # Manually create a context and invoke the ask command
        ctx = await bot.get_context(message)
        # Check if the message contains only a prompt or includes attachments
        # We need to pass None for the prompt if it's only attachments
        prompt = message.content or None
        await ask(ctx, prompt=prompt)
        return

    # Let the bot process other commands as usual
    await bot.process_commands(message)

@bot.command(name='ask')
async def ask(ctx, *, prompt: str = None):
    """Handles the core logic for processing messages and images."""
    if ctx.guild and not prompt and not ctx.message.attachments:
        await ctx.send("Where is Dr. Venture?")
        return

    is_dm = isinstance(ctx.channel, discord.DMChannel)
    if is_dm and not prompt and ctx.message.attachments:
        prompt = "What is in this image?"

    if not prompt and not ctx.message.attachments:
        return

    print(f"{cyan}{ctx.guild.name if ctx.guild else 'DM'} - {RESET}{BOLD}{green}{ctx.author.display_name}{RESET} said: {yellow}{prompt}{RESET}")
    sent_message = await ctx.send("Thinking...")
    animation_task = bot.loop.create_task(animate_thinking(sent_message))

    try:
        async with aiohttp.ClientSession() as session:
            content_list = []
            if prompt:
                content_list.append({"type": "text", "text": prompt})

            if ctx.message.attachments:
                for attachment in ctx.message.attachments:
                    if 'image' in attachment.content_type:
                        base64_image = await fetch_and_encode_image(session, attachment.url)
                        if base64_image:
                            content_list.append({"type": "image_url", "image_url": {"url": base64_image}})
                        break
            
            payload = {
                "model": "falcon3-3b-instruct-abliterated",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": content_list}
                ],
                "temperature": CHAT_TEMPERATURE
            }

            headers = {"Content-Type": "application/json"}
            async with session.post(LOCALAI_URL, headers=headers, json=payload) as response:
                response.raise_for_status()
                data = await response.json()

            animation_task.cancel()

            if 'choices' in data and data['choices']:
                llm_response = data['choices'][0]['message']['content']
                llm_response = remove_assistant_prefix(llm_response)
                print(f"{cyan}{ctx.guild.name if ctx.guild else 'DM'} - {RESET}replying to {BOLD}{green}{ctx.author.display_name}{RESET}: {yellow}{len(llm_response)} - {llm_response}")
                if len(llm_response) > MESSAGE_CHARACTER_LIMIT:
                    # Use a Paginator instance for this specific response
                    my_paginator = commands.Paginator(prefix='', suffix='')
                    for line in llm_response.split('\n'):
                        my_paginator.add_line(line)

                    # Edit the 'Thinking...' message with the first page
                    await sent_message.edit(content=my_paginator.pages[0])

                    # Send any remaining pages as new replies
                    for page in my_paginator.pages[1:]:
                        await ctx.reply(page)
                else:
                    # If the response is short enough, edit the original message directly
                    await sent_message.edit(content=f"{llm_response}")
            else:
                print("nothing received")
                await sent_message.edit(content="No, Where is Dr. Venture.")

    except aiohttp.ClientResponseError as e:
        print({e})
        animation_task.cancel()
        await sent_message.edit(content=f"Dr. Venture needs to know: An API error occurred: {e.status} - {e.message}")
    except aiohttp.ClientError as e:
        print({e})
        animation_task.cancel()
        await sent_message.edit(content=f"Dr. Venture needs to know: An error occurred while communicated with another AI: {e}")
    except Exception as e:
        print({e})
        animation_task.cancel()
        await sent_message.edit(content=f"This is unexpected Dr. Venture! {e}")

@bot.command(name='generate')
async def generate_image(ctx, *, prompt: str):
    """Generates an image from a text prompt using LocalAI."""
    if not prompt:
        await ctx.send("Please provide a prompt for the image generation.")
        return

    print(f"{cyan}{ctx.guild.name if ctx.guild else 'DM'} - {RESET}{BOLD}{green}{ctx.author.display_name}{RESET} asked for an image of: {yellow}{prompt}{RESET}")
    sent_message = await ctx.send("Thinking...")
    animation_task = bot.loop.create_task(animate_thinking(sent_message))

    try:
        async with aiohttp.ClientSession() as session:
            session.request = functools.partial(session.request, timeout=600)
            payload = {
                "model": "dreamshaper",
                "prompt": prompt,
                "size": IMAGE_SIZE
            }
            headers = {"Content-Type": "application/json"}
            
            async with session.post(LOCALAI_IMAGE_URL, headers=headers, json=payload) as response:
                response.raise_for_status()
                data = await response.json()

            animation_task.cancel()

            if 'data' in data and data['data']:
                image_data_url = data['data'][0]['url']
                try:
                    max_retries = 5
                    retry_delay_seconds = 1
    
                    for i in range(max_retries):
                        try:
                            async with aiohttp.ClientSession() as session:
                                async with session.get(image_data_url) as resp:
                                    if resp.status == 200:
                                        print(f"{cyan}{ctx.guild.name if ctx.guild else 'DM'} - {RESET}Sending an image of {yellow}{prompt}{RESET} to {BOLD}{green}{ctx.author.display_name}{RESET}")
                                        data = BytesIO(await resp.read())
                                        file_to_send = discord.File(data, filename="generated_image.png")
                                        await sent_message.delete()
                                        await asyncio.sleep(1)
                                        await ctx.send(file=file_to_send)
                                        return # Exit the function after sending
                                    elif resp.status == 404 or resp.status == 403 and i < max_retries - 1:
                                        # 404 is a good sign that the file is not ready yet, retry
                                        print(f"File not found (404), retrying in {retry_delay_seconds}s...")
                                        await asyncio.sleep(retry_delay_seconds)
                                        retry_delay_seconds *= 2  # Exponential backoff
                                    else:
                                        # Handle other error codes or final 404
                                        print(f"{resp.status}")
                                        await ctx.send(content=f"Error: Could not download image (Status {resp.status}).")
                                        return

                        except aiohttp.ClientConnectorError as e:
                            # Catch connection errors and retry
                            print(f"Connection error: {e}, retrying in {retry_delay_seconds}s...")
                    await asyncio.sleep(retry_delay_seconds)
                    retry_delay_seconds *= 2  # Exponential backoff
                except Exception as e:
                    # Catch other unexpected errors
                    await ctx.send(content=f"An unexpected error occurred while downloading the image: {e}")
                    return
            
                # If the loop completes without success
                await ctx.send(content="Failed to download the image after several retries.")
            else:
                await ctx.send(content="Could not generate the image.")

    except aiohttp.ClientResponseError as e:
        print({e})
        animation_task.cancel()
        await sent_message.edit(content=f"Dr. Venture needs to know: An API error occurred: {e.status} - {e.message}")
    except aiohttp.ClientError as e:
        print({e})
        animation_task.cancel()
        await sent_message.edit(content=f"Dr. Venture needs to know: An error occurred while communicated with another AI: {e}")
    except Exception as e:
        print({e})
        animation_task.cancel()
        await sent_message.edit(content=f"This is unexpected Dr. Venture! {e}")

if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("Discord token not found. Please set the DISCORD_TOKEN environment variable.")
