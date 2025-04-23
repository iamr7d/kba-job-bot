from telegram import Update
from telegram.ext import ContextTypes
from handlers.admin import admin_graphs, admin

ADMIN_MENU_BUTTONS = {"📊 Analytics", "👥 User Management", "📢 Broadcast", "⬅️ Back"}

async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    if user_id != 741029163:
        await update.message.reply_text("Unauthorized.")
        return
    if text not in ADMIN_MENU_BUTTONS:
        return  # Ignore, let other handlers process
    if text == "📊 Analytics":
        await admin_graphs(update, context)
    elif text == "👥 User Management":
        await update.message.reply_text("User management coming soon! (Export, view, and manage users)")
    elif text == "📢 Broadcast":
        await update.message.reply_text("Please type the message to broadcast:")
        context.user_data['awaiting_broadcast'] = True
    elif text == "⬅️ Back":
        await admin(update, context)
