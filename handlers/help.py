from telegram import Update
from telegram.ext import ContextTypes

HELP_MSG = (
    "<b>❓ Help & Guide</b>\n\n"
    "Welcome to Smart Job Bot! Here's what you can do:\n\n"
    "• <b>Upload Resume</b>: Get instant AI-powered resume review and job matches.\n"
    "• <b>Get Job Alerts</b>: Receive job alerts tailored to your profile.\n"
    "• <b>AI Job Search</b>: Search for jobs using AI recommendations.\n"
    "• <b>Latest Jobs</b>: See the most recent job listings.\n"
    "• <b>Suggestions</b>: Get career and resume improvement tips.\n"
    "• <b>Analytics</b>: Track your resume score and job search stats.\n"
    "• <b>Saved Jobs</b>: View and manage your saved jobs.\n\n"
    "If you need more help, use /feedback to contact support.\n\n"
    "<i>Developed by R7D.AI Labs</i>"
    )

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('DEBUG: help_handler triggered')
    await update.message.reply_text(HELP_MSG, parse_mode='HTML', disable_web_page_preview=False)
