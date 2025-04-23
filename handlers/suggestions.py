from telegram import Update
from telegram.ext import ContextTypes
import random

TIPS = [
    "Tailor your resume for each job application.",
    "Highlight measurable achievements, not just responsibilities.",
    "Keep your LinkedIn profile updated and active.",
    "Use AI tools to analyze job descriptions and optimize your resume.",
    "Practice common interview questions and STAR method answers.",
    "Network with professionals in your field via LinkedIn or events.",
    "Keep learning: take online courses and earn certifications.",
    "Showcase your projects and skills on GitHub or a personal website."
]

async def suggestions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('DEBUG: suggestions handler triggered')
    tip = random.choice(TIPS)
    msg = f"<b>💡 Career/Resume Tip</b>\n{tip}\n\nNeed more help? Try uploading your resume for a detailed review!"
    await update.message.reply_text(msg, parse_mode='HTML')
