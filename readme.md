![Image of MUTHER](/images/MUTHER.webp)

# M.U.T.H.E.R.
> "Hello.  Where is... Doctor... Venture?"

![Muther Banner](/images/muther-banner1.png)

*A chatbot bringing ***LOCAL*** LLM and Image Generation AI to discord*

## 📖 About

This bot was created to tie my local AI Lab with discord so I didn't have to make a frontend.

> [!WARNING]
> if you use the Falcon3-abliterated and Dreamshaper as in the .env.example
>  - Falcon3 - The word "Abliterated" in a model means it is uncensored. It *WILL* talk about illegal and/or amoral topics.
>  - Dreamshaper - Is very 'horny'.  If there is any innuendo in your prompt, it will get naughty quick.

---

## ✨ Commands

- !ask
  - will send the prompt to the LLM chat backend
  - in a Direct Message (DM) !ask is assumed and not needed. Just chat away.
- !generate
  - will send the prompt to the Image Generation backend

---

## 🚀 Getting Started

__Software__
- [LocalAI.io](https://localai.io) - for serving the models
- [Python](https://www.python.org) (version 3.10 or higher)

__Discord Key__
- [Discord Token](https://discord.com/developers) - You need this so the app can connect to discord. There is good documentation on how to set it up on their site.

---

### Installation

1. Clone the repository and open the folder in your shell
2. Install Requirements
    ```sh
    pip install -r requirements.txt
    ```
3. Create .env
    ```sh
    cp .env.example .env
    ```
4. Edit .env for to match your setup
5. Start your OpenAI compatible server
6. Run Bot
    ```sh
    python bot.py
    ```
> You'll also have to add the bot to your server.  Consult the documentation on how to setup your Discord permissions. [Discord Developers Documentation](https://discord.com/developers/docs/intro)