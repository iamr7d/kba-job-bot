import os
from telegram import Update
from telegram.ext import ContextTypes
from utils.analytics import export_analytics_csv

ADMIN_ID = os.environ.get("ADMIN_ID")

async def export_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(ADMIN_ID):
        await update.message.reply_text("Unauthorized.")
        return
    path = export_analytics_csv()
    if not path:
        await update.message.reply_text("No analytics data available.")
        return
    with open(path, "rb") as f:
        await update.message.reply_document(f, filename="analytics_export.csv")
        await update.message.reply_text("Analytics exported.")
