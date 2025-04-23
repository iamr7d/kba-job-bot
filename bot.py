import logging
import os
import tempfile
from google import genai
from telegram import Update, Document, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
from dotenv import load_dotenv

# Load .env for local development
load_dotenv()

# IMPORTANT: Set BOT_TOKEN in Railway environment variables after deployment
BOT_TOKEN = os.environ.get("BOT_TOKEN")
# IMPORTANT: Set GEMINI_API_KEY in Railway environment variables after deployment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WELCOME_MESSAGE = (
    "🚀 Hello R7D! Smart Job Bot is live!\n"
    "Send your resume as a PDF or DOCX file.\n"
    "I'll rate it, suggest improvements, and recommend jobs!"
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

client = genai.Client(api_key=GEMINI_API_KEY)

def extract_text_from_file(file_path, mime_type):
    if mime_type == 'application/pdf':
        import pdfplumber
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
        import docx
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        raise ValueError("Unsupported file type. Please upload a PDF or DOCX.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu_keyboard = [["Upload Resume", "Get Job Alerts"], ["Help"]]
    reply_markup = ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True)
    await update.message.reply_text(WELCOME_MESSAGE, reply_markup=reply_markup)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc: Document = update.message.document
    if not doc:
        await update.message.reply_text("Please upload a resume as a PDF or DOCX file.")
        return
    mime_type = doc.mime_type
    if mime_type not in [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword'
    ]:
        await update.message.reply_text("Unsupported file type. Please upload a PDF or DOCX file.")
        return
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        file_path = tf.name
    try:
        telegram_file = await context.bot.get_file(doc.file_id)
        await telegram_file.download_to_drive(file_path)
        resume_text = extract_text_from_file(file_path, mime_type)
        if not resume_text.strip():
            await update.message.reply_text("Could not extract text from your resume. Please check the file.")
            return
    except Exception as e:
        await update.message.reply_text(f"Error reading file: {e}")
        return
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
    prompt = (
        f"You are a professional resume reviewer and job recommender.\n"
        f"Given the following resume, reply in this STRICT JSON format:\n"
        f"{{\n  'rating': <number>,\n  'improvement': <1 line string>,\n  'jobs': [<job1>, <job2>, <job3>]\n}}\n"
        f"Do NOT explain, do NOT add extra keys, do NOT use nested objects.\n"
        f"Example:\n{{'rating': 82, 'improvement': 'Add more quantifiable achievements.', 'jobs': ['AI Engineer', 'Data Scientist', 'ML Researcher']}}\n"
        f"Now, for the following resume:\n{resume_text[:4000]}"
    )
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        result = response.text if hasattr(response, 'text') else str(response)
    except Exception as e:
        await update.message.reply_text(f"[Gemini API Error] {e}")
        return
    import json
    import re
    # Try to extract the JSON block if Gemini adds markdown or text
    match = re.search(r'\{.*\}', result, re.DOTALL)
    json_str = match.group(0) if match else result
    try:
        parsed = json.loads(json_str.replace("'", '"'))
        # Post-process for consistency
        rating = parsed.get('rating', 'N/A')
        improvement = parsed.get('improvement', '')
        jobs = parsed.get('jobs', [])
        # If improvement is a list, use first item
        if isinstance(improvement, list):
            improvement = improvement[0] if improvement else ''
        # If jobs is not a list, try to extract job titles
        if not isinstance(jobs, list):
            jobs = re.findall(r"[A-Za-z ]+", str(jobs))
            jobs = [j.strip() for j in jobs if len(j.strip()) > 3][:3]
        # Store Gemini job roles for this user for /jobalerts
        context.user_data['gemini_jobs'] = jobs
        # Also extract and store keywords using Gemini
        kw_prompt = f"Extract the top 5 most relevant keywords (skills, tech, domains) from this resume as a Python list: {resume_text[:4000]}\nReply ONLY with a Python list of keywords."
        try:
            kw_response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=kw_prompt
            )
            import ast
            keywords = ast.literal_eval(kw_response.text if hasattr(kw_response, 'text') else str(kw_response))
            if isinstance(keywords, list):
                context.user_data['gemini_keywords'] = [str(k) for k in keywords]
            else:
                context.user_data['gemini_keywords'] = []
        except Exception:
            context.user_data['gemini_keywords'] = []
        formatted = (
            f"🚀 <b>Your Resume Review</b>\n\n"
            f"<b>⭐ Score:</b> {rating}/100\n\n"
            f"<b>🔍 Expert Tip:</b> {improvement}\n\n"
            f"<b>🎯 Top Career Matches:</b>\n"
            + "\n".join([f"• {job}" for job in jobs]) + "\n\n"
            f"<i>Keep pushing forward—your next big opportunity awaits!</i>"
        )
        await update.message.reply_text(formatted, parse_mode='HTML')
    except Exception:
        await update.message.reply_text(f"Gemini response:\n{result}")

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
        await menu(update, context)
    elif text == "help":
        await update.message.reply_text("Use the menu to upload your resume, get job alerts, or set preferences. You can also use /start or /menu at any time.")
    else:
        await update.message.reply_text(
            "Send your resume as a PDF or DOCX file to get a review, rating, and job suggestions!"
        )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("preferences", preferences))
    app.add_handler(CommandHandler("jobalerts", job_alerts))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat))
    # --- Webhook support for Railway ---
    port = int(os.environ.get("PORT", 8080))
    url = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    if url:
        webhook_url = f"https://{url}/webhook"
        app.run_webhook(listen="0.0.0.0", port=port, webhook_url=webhook_url)
    else:
        app.run_polling()

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import joblib
from jobspy import scrape_jobs
import pandas as pd

LOC = "India"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def score(title, search_roles):
    for r in search_roles:
        if r.lower() in title.lower():
            return 80
    return 50

def summarize(job):
    return f"1. 🔎 {job['title']} at {job['company']}\n2. 💡 {job['location']}\n3. ✅ {job['source']}\n4. ⚠️ Check job link."

def get_desc(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        s = BeautifulSoup(r.text, 'html.parser')
        d = s.find('section') or s.find('div', class_='description') or s.find('div', class_='jobsearch-jobDescriptionText')
        return d.get_text(strip=True)[:1500] if d else "N/A"
    except: return "N/A"

# Scraping is now handled by python-jobspy in job_alerts

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu_keyboard = [["Upload Resume", "Get Job Alerts"], ["Preferences", "Help"]]
    reply_markup = ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True)
    await update.message.reply_text("Main Menu:", reply_markup=reply_markup)

async def preferences(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prefs_keyboard = [["Full Time", "Part Time"], ["Internship", "Contract"], ["Remote", "Onsite"], ["Menu"]]
    reply_markup = ReplyKeyboardMarkup(prefs_keyboard, resize_keyboard=True)
    await update.message.reply_text("Set your job preferences:\nSelect job type and remote/onsite:", reply_markup=reply_markup)


async def job_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_roles = context.user_data.get('gemini_jobs') or []
    user_keywords = context.user_data.get('gemini_keywords') or []
    search_terms = list(set(user_roles + user_keywords))
    if not search_terms:
        await update.message.reply_text("Please upload your resume first. After review, Gemini's recommended roles and keywords will be used to find jobs for you.")
        return
    await update.message.reply_text(f"🔍 Searching for jobs in {', '.join(search_terms)} ({LOC})...")
    # Use user preferences if set
    job_type = context.user_data.get('job_type', 'fulltime')
    is_remote = context.user_data.get('is_remote', None)
    try:
        jobs_df = scrape_jobs(
            site_name=["indeed", "linkedin", "zip_recruiter", "glassdoor", "google", "bayt", "naukri"],
            search_term=search_terms[0],
            location=LOC,
            results_wanted=20,
            job_type=job_type,
            is_remote=is_remote,
            hours_old=72,
            country_indeed='India',
        )
    except Exception as e:
        await update.message.reply_text(f"Job scraping error: {e}")
        return
    sent = 0
    if not isinstance(jobs_df, pd.DataFrame) or jobs_df.empty:
        await update.message.reply_text("No jobs found right now. Try again later!")
        return
    for _, j in jobs_df.iterrows():
        s = score(j.get("title", ""), search_terms)
        if s > 50:
            msg = (
                f"🚀 <b>New Job Match!</b>\n"
                f"📌 <b>{j.get('title','')}</b>\n"
                f"🏢 {j.get('company','')}\n"
                f"📍 {j.get('location','')}\n"
                f"🌐 {j.get('site_name','')}\n"
                f"📊 <b>AI Score:</b> {s}%\n"
                f"🔗 {j.get('job_url','')}\n\n"
                f"{j.get('description','')[:500]}"
            )
            await update.message.reply_text(msg, parse_mode='HTML', disable_web_page_preview=False)
            sent += 1
    if sent == 0:
        await update.message.reply_text("No strong matches found right now. Try again after uploading your resume!")
    else:
        await update.message.reply_text(f"✅ Sent {sent} job matches!")

if __name__ == "__main__":
    main()

