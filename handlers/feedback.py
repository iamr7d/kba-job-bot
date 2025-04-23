from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, filters

ASK_FEEDBACK = 1

async def feedback_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("We value your feedback! Please type your comments or suggestions below:")
    return ASK_FEEDBACK

async def feedback_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    feedback = update.message.text
    # Save feedback to a file (or database)
    with open("feedback.txt", "a", encoding="utf-8") as f:
        f.write(f"User {user_id}: {feedback}\n")
    await update.message.reply_text("Thank you for your feedback!")
    return ConversationHandler.END

async def feedback_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Feedback cancelled.")
    return ConversationHandler.END

feedback_handler = ConversationHandler(
    entry_points=[CommandHandler("feedback", feedback_start)],
    states={
        ASK_FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_save)]
    },
    fallbacks=[CommandHandler("cancel", feedback_cancel)],
)
