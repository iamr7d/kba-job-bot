import os, requests, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from bs4 import BeautifulSoup
import google.generativeai as genai
from utils.rate_limiter import gemini_rate_limiter
from utils.fallback_llm import openai_completion
from utils.hf_similarity import compute_resume_job_score

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
HEADERS = {'User-Agent': 'Mozilla/5.0'}
ROLES = ["AI Engineer", "ML Engineer", "Data Scientist", "NLP Engineer", "Generative AI Engineer", "AI Research Intern", "Deep Learning Engineer", "Computer Vision Engineer", "AI Developer", "AI Researcher"]

# You may want to load RESUME from user data or env
RESUME_DEFAULT = os.environ.get("USER_RESUME", "Rahulraj P V | AI R&D | M.Tech AI\nSkills: Python, ML, DL, GenAI, NLP, CV, Film Analytics\nExp: AI film tool, GenAI radio, Blockchain farming\nSeeking: AI/ML roles, research, generative media")

from utils.analytics import increment_usage

async def ai_job_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    increment_usage("ai_job_search", update.effective_user.id)
    resume_text = context.user_data.get('resume_text', RESUME_DEFAULT)
    # Send AI animation/sticker (replace with your own file_id or animation)
    try:
        await update.message.reply_animation(
            animation="https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExcnZ4cHJ4OTAzNmRrbXh3amxiem5odmlqdTJudzZyczB0a2ZqcjN5aCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/Ye8n2abV5bBQY/giphy.gif",
            caption="🤖AI is searching for the best jobs for you..."
        )
    except Exception:
        pass
    jobs = await asyncio.get_event_loop().run_in_executor(None, scrape_jobs)
    top_jobs = []
    sent_job_urls = set(context.user_data.get('sent_job_urls', []))
    for job in jobs:
        s = await asyncio.get_event_loop().run_in_executor(None, score, job['title'], resume_text)
        if s >= 70 and job['link'] not in sent_job_urls:
            summary = await asyncio.get_event_loop().run_in_executor(None, summarize, job, resume_text)
            job['score'] = s
            job['summary'] = summary
            top_jobs.append(job)
            sent_job_urls.add(job['link'])
    if not top_jobs:
        await update.message.reply_text("No strong matches found. Try again later or update your resume.")
        return
    # Store resume score and sent jobs
    context.user_data['resume_score'] = top_jobs[0]['score'] if top_jobs else None
    context.user_data['ai_job_results'] = top_jobs
    context.user_data['ai_job_index'] = 0
    context.user_data['sent_job_urls'] = list(sent_job_urls)
    await send_ai_job(update, context, 0)

def scrape_linkedin():
    KW, LOC = ROLES[0], "India"
    url = f'https://www.linkedin.com/jobs/search/?keywords={KW}&location={LOC}'
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, 'html.parser')
    jobs = []
    for j in soup.select('.base-card')[:5]:
        try:
            jobs.append({
                "source": "LinkedIn",
                "title": j.select_one('h3').text.strip(),
                "company": j.select_one('h4').text.strip(),
                "location": j.select_one('.job-search-card__location').text.strip(),
                "link": j.select_one('a')['href'],
                "desc": get_desc(j.select_one('a')['href'])
            })
        except: continue
    return jobs

def scrape_indeed():
    KW, LOC = ROLES[0], "India"
    url = f'https://in.indeed.com/jobs?q={KW.replace(" ", "+")}&l={LOC.replace(" ", "+")}'
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, 'html.parser')
    jobs = []
    for j in soup.select('.job_seen_beacon')[:5]:
        try:
            jobs.append({
                "source": "Indeed",
                "title": j.select_one('h2 a').text.strip(),
                "company": j.select_one('.companyName').text.strip(),
                "location": j.select_one('.companyLocation').text.strip(),
                "link": 'https://in.indeed.com' + j.select_one('h2 a')['href'],
                "desc": get_desc('https://in.indeed.com' + j.select_one('h2 a')['href'])
            })
        except: continue
    return jobs

def scrape_jobs():
    return scrape_linkedin() + scrape_indeed()

def get_desc(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        s = BeautifulSoup(r.text, 'html.parser')
        d = s.find('section') or s.find('div', class_='description') or s.find('div', class_='jobsearch-jobDescriptionText')
        return d.get_text(strip=True)[:1500] if d else "N/A"
    except: return "N/A"

def clean_resume_text(resume_text):
    if not isinstance(resume_text, str):
        resume_text = str(resume_text)
    # Remove null bytes and non-printable characters
    return ''.join(c for c in resume_text if c.isprintable())

def score(job, resume):
    # Use only the most relevant part of the resume for scoring
    summary = resume.split('\n')[0][:256] if '\n' in resume else resume[:256]
    job_title = job['title'] if isinstance(job, dict) and 'title' in job else str(job)
    # Use HuggingFace model for similarity
    try:
        return compute_resume_job_score(summary, job_title)
    except Exception as e:
        print(f"[HF Similarity Error] {e}")
        return 0

def summarize(job, resume):
    resume = clean_resume_text(resume)
    p = f"Summarize this job for the candidate (resume):\nResume: {resume}\nJob: {job}\nGive a short summary for the candidate."
    print("Gemini summarize prompt:", repr(p))
    # Rate limit for Gemini
    if not gemini_rate_limiter.allow_request():
        # Fallback to OpenAI
        openai_resp = openai_completion(p)
        if "OpenAI Fallback Error" not in openai_resp:
            return openai_resp.strip()
        else:
            return "[Sorry, all AI providers are busy. Please try again in a minute.]"
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=p,
        )
        return response.text.strip()
    except Exception as e:
        # If quota error, fallback to OpenAI
        if 'RESOURCE_EXHAUSTED' in str(e) or 'quota' in str(e).lower():
            openai_resp = openai_completion(p)
            if "OpenAI Fallback Error" not in openai_resp:
                return openai_resp.strip()
            else:
                return "[Sorry, all AI providers are busy. Please try again in a minute.]"
        print(f"Gemini summarize error: {e}")
        return "[Sorry, all AI providers are busy. Please try again in a minute.]"

def get_ai_job_message(job):
    return (
        f"🚀 <b>New Job Match!</b>\n"
        f"📌 <b>{job['title']}</b>\n"
        f"🏢 {job['company']}\n"
        f"📍 {job['location']}\n"
        f"🌐 {job['source']}\n"
        f"📊 <b>AI Score:</b> {job['score']}%\n"
        f"🔗 {job['link']}\n\n"
        f"{job['summary']}"
    )

async def send_ai_job(update, context, idx):
    jobs = context.user_data.get('ai_job_results', [])
    if not jobs or idx < 0 or idx >= len(jobs):
        await update.effective_message.reply_text("No more jobs.")
        return
    job = jobs[idx]
    keyboard = [
        [
            InlineKeyboardButton("Next", callback_data="ai_job_next"),
            InlineKeyboardButton("Save", callback_data="ai_job_save"),
            InlineKeyboardButton("Apply", url=job['link'])
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text(
        get_ai_job_message(job),
        parse_mode='HTML',
        reply_markup=reply_markup,
        disable_web_page_preview=False
    )

from utils.analytics import increment_usage

async def ai_job_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = context.user_data.get('ai_job_index', 0)
    jobs = context.user_data.get('ai_job_results', [])
    if not jobs:
        await query.edit_message_text("No jobs to show.")
        return
    if query.data == "ai_job_next":
        idx += 1
        if idx >= len(jobs):
            await query.edit_message_text("No more jobs.")
            return
        context.user_data['ai_job_index'] = idx
        await send_ai_job(update, context, idx)
    elif query.data == "ai_job_save":
        saved = context.user_data.get('ai_saved_jobs', [])
        saved.append(jobs[idx])
        context.user_data['ai_saved_jobs'] = saved
        increment_usage("ai_job_save", update.effective_user.id)
        await query.answer("Job saved!")
    # No need to handle 'Apply' as it's just a URL button

def get_ai_job_callback_handler():
    return CallbackQueryHandler(ai_job_callback, pattern="^ai_job_(next|save)$")
