from telegram import Update
from telegram.ext import ContextTypes
from handlers.job_alerts import job_alerts
from handlers.preferences import preferences
from handlers.start import start

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text == "upload resume":
        await update.message.reply_text("Please upload your resume as a PDF or DOCX file.")
    elif text == "get job alerts":
        await job_alerts(update, context)
    elif text == "preferences":
        await preferences(update, context)
    elif text == "full time":
        context.user_data['job_type'] = 'fulltime'
        await update.message.reply_text("Job type set to Full Time.")
    elif text == "part time":
        context.user_data['job_type'] = 'parttime'
        await update.message.reply_text("Job type set to Part Time.")
    elif text == "internship":
        context.user_data['job_type'] = 'internship'
        await update.message.reply_text("Job type set to Internship.")
    elif text == "contract":
        context.user_data['job_type'] = 'contract'
        await update.message.reply_text("Job type set to Contract.")
    elif text == "remote":
        context.user_data['is_remote'] = True
        await update.message.reply_text("Preference set to Remote jobs.")
    elif text == "onsite":
        context.user_data['is_remote'] = False
        await update.message.reply_text("Preference set to Onsite jobs.")
    elif text == "menu":
        await start(update, context)
    elif text == "help":
        await update.message.reply_text("Use the menu to upload your resume, get job alerts, or set preferences. You can also use /start or /menu at any time.")
    else:
        await update.message.reply_text(
            "Send your resume as a PDF or DOCX file to get a review, rating, and job suggestions!"
        )
