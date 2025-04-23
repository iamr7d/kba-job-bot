# Smart Job Telegram Bot

An AI-powered Telegram bot for personalized job search, resume review, and analytics. Built with [python-telegram-bot](https://python-telegram-bot.org/) and Google Gemini.

## ✨ Features
- **/start**: Welcome message with menu buttons.
- **Resume Upload**: Upload your resume (PDF/DOCX) for instant feedback and AI-powered job matching.
- **AI Job Search**: Get personalized job matches scored and summarized by Gemini LLM. Use the `/ai_job_search` command or the menu button.
- **Interactive Alerts**: Browse jobs one-by-one with Next/Save/Apply buttons.
- **Admin Tools**: `/stats`, `/broadcast`, `/export_analytics` for user stats, mass messaging, and analytics export.
- **Analytics**: Tracks feature usage and job saves for export.

## 🚀 Railway Deployment
1. **Deploy to [Railway](https://railway.app/):**
   - Create a new Railway project and link this repo.
2. **Set environment variables in Railway dashboard:**
   - `BOT_TOKEN` (Telegram Bot Token)
   - `GEMINI_API_KEY` (Google Gemini API Key)
   - `ADMIN_ID` (Your Telegram user ID)
   - *(Optional)* `ALERT_CHAT_ID`, `USER_RESUME`, `ANALYTICS_FILE`
   - **Do NOT use a `.env` file in production. Use Railway's Variables tab.**
3. **Entry point:**
   - Railway will auto-detect `bot.py` as the entry point.
   - Or set the start command to:
     ```sh
     python bot.py
     ```

## 🧪 Local Development
1. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
2. (Optional) Create a `.env` file for local testing:
   ```env
   BOT_TOKEN=your-telegram-bot-token
   GEMINI_API_KEY=your-gemini-api-key
   ADMIN_ID=your-telegram-user-id
   # ...other vars
   ```
3. Run the bot locally:
   ```sh
   python bot.py
   ```

## 🛠️ Troubleshooting
- **Gemini errors:** Make sure you are using `genai.configure(api_key=...)` and not `genai.Client`.
- **Multiple bot instances:** Only run one instance at a time to avoid Telegram 'Conflict' errors.
- **Missing packages:** All dependencies are listed in `requirements.txt`. If Railway build fails, check logs for missing packages and update `requirements.txt` as needed.
- **Environment variables:** All secrets must be set in Railway's Variables tab, not in code or `.env` in production.

## 📦 Features & Dependencies
- Job scraping: `python-jobspy`, `beautifulsoup4`, `requests`, `pandas`
- Resume parsing: `pdfplumber`, `python-docx`
- Gemini AI: `google-generativeai`
- Analytics: `plotly`, `pandas`
- Semantic job matching: `sentence-transformers`, `scikit-learn`
- Telegram bot: `python-telegram-bot`
- See `requirements.txt` for full list.

## 🛠️ Admin & Analytics Commands
- `/stats` — Show user and feedback stats
- `/broadcast <message>` — Send a message to all users
- `/export_analytics` — Download analytics as CSV (admin only)

## ⚙️ Environment Variables
| Variable         | Required | Description                         |
|-----------------|----------|-------------------------------------|
| BOT_TOKEN        | Yes      | Telegram Bot Token                  |
| GEMINI_API_KEY   | Yes      | Google Gemini API Key               |
| ADMIN_ID         | Yes      | Your Telegram user ID (for admin)   |
| ALERT_CHAT_ID    | No       | Chat ID for admin job alerts        |
| USER_RESUME      | No       | Default resume for scoring          |
| ANALYTICS_FILE   | No       | Path for analytics data file        |

## 📦 Project Structure
- `bot.py` — Main bot entrypoint
- `handlers/` — All bot command and callback handlers
- `utils/` — Utilities for analytics, user data, etc.
- `tests/` — Unit tests (mocking LLM calls)

## 📝 Notes
- Do **not** commit your `.env` or `user_data.json` files.
- All secrets should be set as Railway environment variables.
- For analytics and admin features, set your Telegram user ID as `ADMIN_ID` in Railway.

---
Built by R7D | Powered by Google Gemini & python-jobspy
