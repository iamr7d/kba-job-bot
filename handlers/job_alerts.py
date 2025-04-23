import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler
from utils.user_data import load_user_data
from utils.scoring import score
import os
from jobspy import scrape_jobs

LOC = os.environ.get("JOB_LOCATION", "India")

async def job_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    all_data = load_user_data()
    user_roles = []
    user_keywords = []
    if user_id in all_data:
        user_roles = all_data[user_id].get('gemini_jobs', [])
        user_keywords = all_data[user_id].get('gemini_keywords', [])
        context.user_data['gemini_jobs'] = user_roles
        context.user_data['gemini_keywords'] = user_keywords
    else:
        user_roles = context.user_data.get('gemini_jobs', [])
        user_keywords = context.user_data.get('gemini_keywords', [])
    # Only prompt for resume upload if this is the user's very first attempt (no roles/keywords ever saved)
    if not user_roles and not user_keywords:
        if not all_data.get(user_id, {}):
            await update.message.reply_text(
                "Please upload your resume to enable personalized job alerts. You only need to do this once!"
            )
            return
        # If user_data exists (resume uploaded before), do NOT prompt again, just continue silently
        # This ensures that after setting preferences or keywords, the user is not prompted again.
    # Load user preferences from persistent storage if not in context
    user_id = str(update.effective_user.id)
    all_data = load_user_data()
    prefs = all_data.get(user_id, {})
    job_type = context.user_data.get('job_type') or prefs.get('job_type', 'Full Time')
    job_location = context.user_data.get('job_location') or prefs.get('job_location', 'Remote')
    search_terms = list(set(user_roles + user_keywords))
    await update.message.reply_text(f"🔍 Searching for {job_type} jobs in {', '.join(search_terms)} ({job_location}, {LOC})...")
    try:
        # Use jobspy with logic closely following the provided script
        all_sites = ["indeed", "linkedin", "glassdoor", "google", "naukri"]
        scrape_kwargs = {
            "site_name": all_sites,
            "search_term": search_terms[0],
            "google_search_term": f"{search_terms[0]} {job_type} {job_location} jobs near {LOC} since yesterday",
            "location": LOC,
            "results_wanted": 20,
            "hours_old": 72,
            "country_indeed": 'USA' if 'USA' in LOC or 'United States' in LOC else 'India',
            # You can add more parameters as needed
        }
        jobs_df = scrape_jobs(**scrape_kwargs)
        if hasattr(jobs_df, 'empty') and jobs_df.empty:
            await update.message.reply_text("No jobs found. Some sites may be rate-limiting or blocking requests. Please try again later.")
            return
        jobs_df = jobs_df.groupby('site').head(3).reset_index(drop=True) if 'site' in jobs_df else jobs_df.head(10)
    except Exception as e:
        await update.message.reply_text(f"Job scraping error: {e}")
        return
    # Prepare job list for interactive navigation
    jobs = []
    for _, j in jobs_df.iterrows():
        job_url = j.get('job_url', '') or j.get('url', '')
        job_title = j.get('title', 'Job Opportunity')
        company = j.get('company', '')
        location = j.get('location', '')
        desc = j.get('description', '')
        if not isinstance(desc, str):
            if desc is None or (isinstance(desc, float) and str(desc) == 'nan'):
                desc = ''
            else:
                desc = str(desc)
        desc = desc[:500]
        s = score(job_title, search_terms)
        if s > 50:
            jobs.append({
                'job_url': job_url,
                'title': job_title,
                'company': company,
                'location': location,
                'desc': desc,
                'site': j.get('site_name',''),
                'score': s
            })
    if not jobs:
        await update.message.reply_text("No strong matches found right now. Try again after uploading your resume!")
        return
    context.user_data['job_results'] = jobs
    context.user_data['job_index'] = 0
    await send_job_alert(update, context, 0)

def get_job_message(job):
    return (
        f"🚀 <b>New Job Match!</b>\n"
        f"📌 <b>{job['title']}</b>\n"
        f"🏢 {job['company']}\n"
        f"📍 {job['location']}\n"
        f"🌐 {job['site']}\n"
        f"📊 <b>AI Score:</b> {job['score']}%\n"
        f"🔗 {job['job_url']}\n\n"
        f"{job['desc']}"
    )

async def send_job_alert(update, context, idx):
    jobs = context.user_data.get('job_results', [])
    if not jobs or idx < 0 or idx >= len(jobs):
        await update.effective_message.reply_text("No more jobs.")
        return
    job = jobs[idx]
    keyboard = [
        [
            InlineKeyboardButton("Next", callback_data="job_next"),
            InlineKeyboardButton("Save", callback_data="job_save"),
            InlineKeyboardButton("Apply", url=job['job_url'])
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text(
        get_job_message(job),
        parse_mode='HTML',
        reply_markup=reply_markup,
        disable_web_page_preview=False
    )

async def job_alerts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = context.user_data.get('job_index', 0)
    jobs = context.user_data.get('job_results', [])
    if not jobs:
        await query.edit_message_text("No jobs to show.")
        return
    if query.data == "job_next":
        idx += 1
        if idx >= len(jobs):
            await query.edit_message_text("No more jobs.")
            return
        context.user_data['job_index'] = idx
        await send_job_alert(update, context, idx)
    elif query.data == "job_save":
        saved = context.user_data.get('saved_jobs', [])
        saved.append(jobs[idx])
        context.user_data['saved_jobs'] = saved
        await query.answer("Job saved!")
    # No need to handle 'Apply' as it's just a URL button

def get_job_alerts_callback_handler():
    return CallbackQueryHandler(job_alerts_callback, pattern="^job_(next|save)$")
