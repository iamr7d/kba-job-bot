import os
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Bot

# --- Config ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Set in Railway or .env
CHAT_ID = os.environ.get("ALERT_CHAT_ID")  # Set this to your Telegram user or group/channel ID
HEADERS = {'User-Agent': 'Mozilla/5.0'}
KW, LOC = "AI Engineer", "India"
ROLES = [
    "AI Engineer", "ML Engineer", "Data Scientist", "NLP Engineer", "Generative AI Engineer",
    "AI Research Intern", "Deep Learning Engineer", "Computer Vision Engineer", "AI Developer", "AI Researcher"
]
RESUME = """Rahulraj P V | AI R&D | M.Tech AI\nSkills: Python, ML, DL, GenAI, NLP, CV, Film Analytics\nExp: AI film tool, GenAI radio, Blockchain farming\nSeeking: AI/ML roles, research, generative media"""

bot = Bot(token=BOT_TOKEN)

def score(title, resume):
    # Dummy scorer for now. Integrate with LLM if needed.
    for r in ROLES:
        if r.lower() in title.lower():
            return 80
    return 50

def summarize(job):
    # Dummy summary. Integrate with LLM if needed.
    return f"1. 🔎 {job['title']} at {job['company']}\n2. 💡 {job['location']}\n3. ✅ {job['source']}\n4. ⚠️ Check job link."

def get_desc(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        s = BeautifulSoup(r.text, 'html.parser')
        d = s.find('section') or s.find('div', class_='description') or s.find('div', class_='jobsearch-jobDescriptionText')
        return d.get_text(strip=True)[:1500] if d else "N/A"
    except: return "N/A"

def scrape_linkedin():
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
                "link": j.select_one('a')['href']
            })
        except: continue
    return jobs

def scrape_indeed():
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
                "link": 'https://in.indeed.com' + j.select_one('h2 a')['href']
            })
        except: continue
    return jobs

def send_telegram_message(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram config missing. Set BOT_TOKEN and ALERT_CHAT_ID.")
        return
    try:
        bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='Markdown')
    except Exception as e:
        print(f"❌ Telegram send fail: {e}")

def notify():
    jobs = scrape_linkedin() + scrape_indeed()
    print(f"🔍 Found {len(jobs)} jobs at {datetime.now().strftime('%H:%M:%S')}")
    for j in jobs:
        j["desc"] = get_desc(j["link"])
        s = score(j["title"], RESUME)
        if s >= 70:
            summary = summarize(j)
            msg = f"""🚀 *New Job Match!*\n📌 *{j['title']}*\n🏢 {j['company']}\n📍 {j['location']}\n🌐 {j['source']}\n📊 *AI Score:* {s}%\n🔗 {j['link']}\n\n{summary}"""
            send_telegram_message(msg)
            print(f"✅ Sent: {j['title']} ({s}%)")
            time.sleep(2)
        else:
            print(f"⏭️ Skipped: {j['title']} ({s}%)")

if __name__ == "__main__":
    print("💼 Starting Smart Job Alerts...\n")
    notify()
