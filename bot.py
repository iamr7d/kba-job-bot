import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import os
import google.generativeai as genai

BOT_TOKEN = os.environ.get("BOT_TOKEN", "7709977067:AAHTpWIA_lxRcQJkyuovuFv57Eq3xLdaHmk")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBX7vWcp12eIX9g8Sa2TE4yYK3imbi2gMM")
WELCOME_MESSAGE = "🚀 Hello R7D! Your Smart Job Bot is live and ready to roll."

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE)

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    try:
        response = model.generate_content(user_message)
        bot_reply = response.text if hasattr(response, 'text') else str(response)
    except Exception as e:
        bot_reply = f"[Gemini API Error] {e}"
    await update.message.reply_text(bot_reply)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat))
    app.run_polling()

if __name__ == "__main__":
    main()
