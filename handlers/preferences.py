from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from utils.user_data import load_user_data, save_user_data

async def preferences(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prefs_keyboard = [
        ["💼 Full Time", "🕒 Part Time"],
        ["🎓 Internship", "📄 Contract"],
        ["🏠 Remote", "🏢 Onsite"],
        ["➕ Add Keywords"],
        ["⬅️ Back to Menu"]
    ]
    reply_markup = ReplyKeyboardMarkup(prefs_keyboard, resize_keyboard=True)

    # Handle user selection
    text = update.message.text
    user_id = str(update.effective_user.id)
    changed = False
    if text in ["💼 Full Time", "🕒 Part Time", "🎓 Internship", "📄 Contract"]:
        context.user_data['job_type'] = text
        changed = True
    elif text in ["🏠 Remote", "🏢 Onsite"]:
        context.user_data['job_location'] = text
        changed = True
    elif text == "➕ Add Keywords":
        await update.message.reply_text(
            "Please type your keywords for job matching, separated by commas (e.g., Python, NLP, Data Science):"
        )
        return  # Wait for next message
    elif ',' in text and len(text) < 200:
        # Assume user is entering keywords
        keywords = [k.strip() for k in text.split(',') if len(k.strip()) > 0]
        context.user_data['manual_keywords'] = keywords
        # Persist to storage
        all_data = load_user_data()
        all_data.setdefault(user_id, {})
        all_data[user_id]['manual_keywords'] = keywords
        save_user_data(all_data)
        await update.message.reply_text(f"✅ Keywords saved: {', '.join(keywords)}", reply_markup=reply_markup)
        return
    if changed:
        # Persist to user data storage
        all_data = load_user_data()
        all_data.setdefault(user_id, {})
        all_data[user_id]['job_type'] = context.user_data.get('job_type')
        all_data[user_id]['job_location'] = context.user_data.get('job_location')
        save_user_data(all_data)
        await update.message.reply_text(f"✅ Preference saved: {text}", reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            "⚙️ <b>Set your job preferences</b>:\nChoose job type and location. (Toggle by tapping)\nYou can also manually add keywords for better job matching.",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
