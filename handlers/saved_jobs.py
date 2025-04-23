from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from utils.user_data import load_user_data, save_user_data

# Unified saved jobs key for both AI and alerts
SAVED_JOBS_KEY_AI = 'ai_saved_jobs'
SAVED_JOBS_KEY_ALERT = 'saved_jobs'

async def show_saved_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('DEBUG: show_saved_jobs handler triggered')
    user_id = str(update.effective_user.id)
    # Try to load from persistent storage if available
    all_data = load_user_data()
    user_data = all_data.get(user_id, {})
    ai_saved = user_data.get(SAVED_JOBS_KEY_AI, [])
    alert_saved = user_data.get(SAVED_JOBS_KEY_ALERT, [])
    # Also include session jobs (not yet persisted)
    ai_saved += context.user_data.get(SAVED_JOBS_KEY_AI, [])
    alert_saved += context.user_data.get(SAVED_JOBS_KEY_ALERT, [])
    jobs = ai_saved + alert_saved
    if not jobs:
        await update.message.reply_text("⭐ You have no saved jobs yet! Save jobs from search results to view them here.")
        return
    context.user_data['saved_jobs_list'] = jobs
    context.user_data['saved_jobs_index'] = 0
    await send_saved_job(update, context, 0)

async def send_saved_job(update, context, idx):
    print(f'DEBUG: send_saved_job called with idx={idx}')
    jobs = context.user_data.get('saved_jobs_list', [])
    if not jobs or idx < 0 or idx >= len(jobs):
        await update.effective_message.reply_text("No more saved jobs.")
        return
    job = jobs[idx]
    # Try to infer job fields
    title = job.get('title') or job.get('job_title') or 'Job'
    company = job.get('company') or job.get('company_name') or ''
    location = job.get('location', '')
    link = job.get('link') or job.get('job_url') or ''
    summary = job.get('summary', job.get('desc', ''))
    source = job.get('source', job.get('site', ''))
    score = job.get('score', '')
    msg = f"<b>{title}</b>\n🏢 {company}\n📍 {location}\n🌐 {source}\n"
    if score:
        msg += f"AI Score: {score}%\n"
    msg += f"🔗 {link}\n\n{summary}"
    keyboard = [
        [
            InlineKeyboardButton("⬅️ Prev", callback_data="saved_prev"),
            InlineKeyboardButton("🗑 Remove", callback_data="saved_remove"),
            InlineKeyboardButton("Next ➡️", callback_data="saved_next")
        ],
        [InlineKeyboardButton("Apply", url=link)] if link else []
    ]
    reply_markup = InlineKeyboardMarkup([row for row in keyboard if row])
    await update.effective_message.reply_text(
        msg,
        parse_mode='HTML',
        reply_markup=reply_markup,
        disable_web_page_preview=False
    )

async def saved_jobs_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = context.user_data.get('saved_jobs_index', 0)
    jobs = context.user_data.get('saved_jobs_list', [])
    if not jobs:
        await query.edit_message_text("No saved jobs.")
        return
    if query.data == "saved_next":
        idx += 1
        if idx >= len(jobs):
            idx = 0
        context.user_data['saved_jobs_index'] = idx
        await send_saved_job(update, context, idx)
    elif query.data == "saved_prev":
        idx -= 1
        if idx < 0:
            idx = len(jobs) - 1
        context.user_data['saved_jobs_index'] = idx
        await send_saved_job(update, context, idx)
    elif query.data == "saved_remove":
        jobs.pop(idx)
        context.user_data['saved_jobs_list'] = jobs
        # Save removal to persistent storage
        user_id = str(update.effective_user.id)
        all_data = load_user_data()
        user_data = all_data.get(user_id, {})
        # Remove from both lists
        for key in [SAVED_JOBS_KEY_AI, SAVED_JOBS_KEY_ALERT]:
            orig = user_data.get(key, [])
            if idx < len(orig):
                orig.pop(idx)
                user_data[key] = orig
        all_data[user_id] = user_data
        save_user_data(all_data)
        if not jobs:
            await query.edit_message_text("No saved jobs left.")
            return
        if idx >= len(jobs):
            idx = 0
        context.user_data['saved_jobs_index'] = idx
        await send_saved_job(update, context, idx)

# Callback handler for dispatcher registration
def get_saved_jobs_callback_handler():
    return CallbackQueryHandler(saved_jobs_callback, pattern="^saved_(next|prev|remove)$")
