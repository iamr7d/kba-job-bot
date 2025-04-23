from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from utils.user_data import load_user_data

WELCOME_MESSAGE = (
    "🚀 Hello R7D! Smart Job Bot is live!\n"
    "Send your resume as a PDF or DOCX file.\n"
    "I'll rate it, suggest improvements, and recommend jobs!"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu_keyboard = [
        ["📄 Upload Resume", "🔍 Get Job Alerts", "🤖 AI Job Search"],
        ["🔎 Job Search", "💡 Suggestions", "📊 Analytics"],
        ["⭐ Saved Jobs", "⚙️ Preferences", "❓ Help"]
    ]
    reply_markup = ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True)
    resume_score = context.user_data.get('resume_score')
    welcome = WELCOME_MESSAGE
    if resume_score:
        welcome += f"\n\n📝 Your last resume score: <b>{resume_score}</b>"
    welcome += ("\n\n<b>Menu Features:</b>\n"
        "🔎 Job Search: Search for jobs by your own keyword.\n"
        "💡 Suggestions: Get personalized career or resume tips.\n"
        "📊 Analytics: View your job search stats and resume performance.\n"
        "⭐ Saved Jobs: View jobs you have saved for later.\n"
        "Use the menu below to explore all features!")
    await update.message.reply_text(welcome, reply_markup=reply_markup, parse_mode='HTML')
    # Placeholder for AI animation (send sticker or animation on AI actions)
