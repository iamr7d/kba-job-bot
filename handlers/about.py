from telegram import Update
from telegram.ext import ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

ABOUT_TEXT = (
    "<b>Smart Job Bot</b>\n"
    "Your AI-powered job search assistant!\n\n"
    "- Upload your resume for instant feedback and career matches.\n"
    "- Get personalized job alerts from top job boards.\n"
    "- All data is private and secure.\n\n"
    "<b>Built by R7D</b> | Powered by Google Gemini & python-jobspy.\n"
    "<a href='https://github.com/r7d-ai/smart-job-bot'>Source Code</a>"
)

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("GitHub", url="https://github.com/r7d-ai/smart-job-bot")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(ABOUT_TEXT, parse_mode='HTML', reply_markup=reply_markup, disable_web_page_preview=False)
