import os
from telegram import Update
from telegram.ext import ContextTypes
from jobspy import scrape_jobs

LOC = os.environ.get("JOB_LOCATION", "India")

async def latest_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('DEBUG: latest_jobs handler triggered')
    # Ask the user for a job keyword
    await update.message.reply_text("Please enter a job keyword (e.g., 'Data Scientist', 'AI Engineer', 'Python Developer'):")
    context.user_data['awaiting_latest_jobs_keyword'] = True

def get_latest_jobs_by_keyword():
    from telegram.ext import MessageHandler, filters
    async def keyword_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        print('DEBUG: keyword_handler triggered')
        if not context.user_data.get('awaiting_latest_jobs_keyword'):
            print('DEBUG: awaiting_latest_jobs_keyword flag not set')
            return
        keyword = update.message.text.strip()
        print(f'DEBUG: Received keyword: {keyword}')
        context.user_data['awaiting_latest_jobs_keyword'] = False
        await fetch_and_send_jobs(update, context, keyword)
    return MessageHandler(filters.TEXT & (~filters.COMMAND), keyword_handler)

async def fetch_and_send_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE, keyword: str):
    print(f'DEBUG: fetch_and_send_jobs called with keyword: {keyword}')
    try:
        jobs_df = scrape_jobs(
            site_name=["indeed", "linkedin", "glassdoor", "google", "naukri"],
            search_term=keyword,
            google_search_term=f"{keyword} jobs near {LOC} since yesterday",
            location=LOC,
            results_wanted=10,
            hours_old=72,
            country_indeed='USA' if 'USA' in LOC or 'United States' in LOC else 'India',
        )
        if hasattr(jobs_df, 'empty') and jobs_df.empty:
            await update.message.reply_text(f"No jobs found for '{keyword}'. Some sites may be rate-limiting or blocking requests. Please try again later.")
            return
        jobs_df = jobs_df.groupby('site').head(2).reset_index(drop=True) if 'site' in jobs_df else jobs_df.head(10)
        msg = f"<b>🔍 Jobs for '{keyword}'</b>\nHere are some recent job listings:\n\n"
        for _, job in jobs_df.iterrows():
            msg += (
                f"<b>{job.get('title','Job')}</b> at {job.get('company','')}\n"
                f"📍 {job.get('location','')}\n"
                f"🌐 {job.get('site','')}\n"
                f"<a href='{job.get('job_url','')}'>Apply Here</a>\n\n"
            )
        msg += "For more, try another keyword or use the AI Job Search!"
        await update.message.reply_text(msg, parse_mode='HTML', disable_web_page_preview=False)
    except Exception as e:
        print(f'DEBUG: Exception in fetch_and_send_jobs: {e}')
        await update.message.reply_text(f"Error fetching jobs for '{keyword}': {e}")
