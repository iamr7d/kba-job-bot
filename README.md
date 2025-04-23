# Smart Job Telegram Bot

A simple Telegram bot that welcomes users. Built with [python-telegram-bot](https://python-telegram-bot.org/).

## Features
- Responds to /start with a welcome message.

## Setup
1. Clone this repo to Railway.
2. Set the `BOT_TOKEN` environment variable (or use the default in code).
3. Railway will auto-detect `bot.py` as the entry point if you set the start command to:

```
python bot.py
```

## Deploying on Railway
- Add your bot token as an environment variable (`BOT_TOKEN`).
- Deploy!

## Local Testing
Install dependencies:
```
pip install -r requirements.txt
```
Run the bot:
```
python bot.py
```
