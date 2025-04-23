import tempfile
from telegram import Update, Document
from telegram.ext import ContextTypes
from utils.file_extract import extract_text_from_file
from utils.user_data import load_user_data, save_user_data
import google.generativeai as genai
import os

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc: Document = update.message.document
    if not doc:
        await update.message.reply_text("Please upload a valid resume file (PDF or DOCX).")
        return
    file = await doc.get_file()
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        await file.download_to_drive(custom_path=tf.name)
        mime_type = doc.mime_type
        try:
            resume_text = extract_text_from_file(tf.name, mime_type)
        except Exception as e:
            await update.message.reply_text(f"Error extracting text: {e}")
            return
    # Gemini resume review logic
    import re, string
    def sanitize_prompt(text):
        # Remove non-printable and non-ASCII characters
        text = ''.join(c for c in text if c in string.printable)
        # Optionally escape problematic characters
        text = text.replace('"', '\"').replace("'", "\'")
        return text
    sanitized_resume = sanitize_prompt(resume_text[:4000])
    review_prompt = f"Review this resume and provide a score (0-100), a short expert tip, and top 3 career matches as a Python dict: {sanitized_resume}\nReply ONLY with a Python dict."
    try:
        print("Gemini review prompt:", repr(review_prompt))
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=review_prompt
        )
        import ast, re
        resp_text = response.text if hasattr(response, 'text') else str(response)
        print("Gemini review response:", resp_text)
        # Remove code block markers and language hints
        cleaned = re.sub(r"```(?:python)?", "", resp_text, flags=re.IGNORECASE).replace("```", "").strip()
        # Parse dict safely
        try:
            review = ast.literal_eval(cleaned)
        except Exception as e:
            print(f"Failed to parse Gemini response: {e}")
            await update.message.reply_text(f"Gemini error: {e}")
            return
        # Accept both 'score' or 'rating', 'tip' or 'expert_tip', 'matches' or 'career_matches'
        rating = review.get('score') or review.get('rating', 0)
        tip = review.get('tip') or review.get('expert_tip', '')
        if not tip or len(tip.strip()) < 10:
            tip = (
                "Highlight your impact with measurable results (e.g., 'Improved model accuracy by 15%' or 'Reduced inference time by 30%'). "
                "Showcase projects using current AI tools (like HuggingFace, PyTorch, or LLM APIs). "
                "Tailor your resume for each role by matching keywords from the job description, and demonstrate how you solve real-world problems."
            )
        # Accept all possible Gemini keys for job matches
        jobs = (
            review.get('matches')
            or review.get('career_matches')
            or review.get('top_3_career_matches')
            or []
        )
        if isinstance(jobs, dict):
            jobs = list(jobs.values())
        if isinstance(jobs, str):
            jobs = re.findall(r"[A-Za-z/ ]+", jobs)
            jobs = [j.strip() for j in jobs if len(j.strip()) > 3]
        if isinstance(jobs, list):
            jobs = [str(j).strip() for j in jobs if len(str(j).strip()) > 3][:3]
        else:
            jobs = []
    except Exception as e:
        await update.message.reply_text(f"Gemini error: {e}")
        print("Gemini review error:", e)
        return
    # Store Gemini job roles for this user for /jobalerts
    user_id = str(update.effective_user.id)
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
    # Persist user data
    all_data = load_user_data()
    all_data[user_id] = {
        "gemini_jobs": context.user_data['gemini_jobs'],
        "gemini_keywords": context.user_data['gemini_keywords']
    }
    save_user_data(all_data)
    formatted = (
        f"🚀 <b>Your Resume Review</b>\n\n"
        f"<b>⭐ Score:</b> {rating}/100\n\n"
        f"<b>🧠 Expert Tip:</b> {tip}\n\n"
        f"🎯 <b>Top Career Matches:</b>\n• " + "\n• ".join(jobs) + "\n\n"
        "<i>Keep pushing forward—your next big opportunity awaits!</i>"
    )
    await update.message.reply_text(formatted, parse_mode='HTML', disable_web_page_preview=True)
