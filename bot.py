import logging
import os
import tempfile
import google.generativeai as genai
from telegram import Update, Document
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
from dotenv import load_dotenv

# Load .env for local development
load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN", "7709977067:AAHTpWIA_lxRcQJkyuovuFv57Eq3xLdaHmk")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBX7vWcp12eIX9g8Sa2TE4yYK3imbi2gMM")
WELCOME_MESSAGE = (
    "🚀 Hello R7D! Smart Job Bot is live!\n"
    "Send your resume as a PDF or DOCX file.\n"
    "I'll rate it, suggest improvements, and recommend jobs!"
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

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
    await update.message.reply_text(WELCOME_MESSAGE)

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
        response = model.generate_content(prompt)
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
        formatted = (
            f"<b>Rating:</b> {rating}/100\n"
            f"<b>Improve:</b> {improvement}\n"
            f"<b>Jobs:</b> {', '.join(jobs)}"
        )
        await update.message.reply_text(formatted, parse_mode='HTML')
    except Exception:
        await update.message.reply_text(f"Gemini response:\n{result}")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send your resume as a PDF or DOCX file to get a review, rating, and job suggestions!"
    )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
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

if __name__ == "__main__":
    main()
