from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
import os

ADMIN_IDS = [741029163, int(os.environ.get('ADMIN_ID', '0'))]  # R7D + env var

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("Unauthorized.")
        return
    # Count users
    try:
        from utils.user_data import load_user_data
        user_data = load_user_data()
        n_users = len(user_data)
    except Exception:
        n_users = 'N/A'
    # Count feedback
    try:
        with open("feedback.txt", "r", encoding="utf-8") as f:
            n_feedback = sum(1 for _ in f)
    except Exception:
        n_feedback = 0
    await update.message.reply_text(f"<b>Bot Stats</b>\nUsers: {n_users}\nFeedback: {n_feedback}", parse_mode='HTML')

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("Unauthorized.")
        return
    msg = ' '.join(context.args)
    if not msg:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    from utils.user_data import load_user_data
    user_data = load_user_data()
    count = 0
    for uid in user_data.keys():
        try:
            await context.bot.send_message(chat_id=int(uid), text=msg)
            count += 1
        except Exception:
            pass
    await update.message.reply_text(f"Broadcast sent to {count} users.")

from handlers.export_analytics import export_analytics
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import io

async def admin_graphs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("Unauthorized.")
        return
    from utils.user_data import load_user_data
    user_data = load_user_data()
    df = pd.DataFrame.from_dict(user_data, orient='index')
    # User growth over time (by first key in user_data)
    if 'created_at' in df:
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        growth = df['created_at'].sort_values().value_counts().sort_index().cumsum()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=growth.index, y=growth.values, mode='lines+markers'))
        fig.update_layout(title='User Growth Over Time', xaxis_title='Date', yaxis_title='Total Users')
        buf = io.BytesIO()
        fig.write_image(buf, format='png')
        buf.seek(0)
        await update.message.reply_photo(buf, caption='User Growth Over Time')
    # Resume score distribution
    if 'resume_score' in df:
        fig2 = px.histogram(df, x='resume_score', nbins=20, title='Resume Score Distribution')
        buf2 = io.BytesIO()
        fig2.write_image(buf2, format='png')
        buf2.seek(0)
        await update.message.reply_photo(buf2, caption='Resume Score Distribution')
    # Job alert usage (if tracked)
    if 'job_alerts_used' in df:
        fig3 = px.histogram(df, x='job_alerts_used', nbins=20, title='Job Alerts Usage')
        buf3 = io.BytesIO()
        fig3.write_image(buf3, format='png')
        buf3.seek(0)
        await update.message.reply_photo(buf3, caption='Job Alerts Usage')
    await update.message.reply_text('Graphs generated with Plotly. Add more analytics as needed!')

from telegram import ReplyKeyboardMarkup

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("Unauthorized.")
        return
    admin_keyboard = [
        ["📊 Analytics", "👥 User Management"],
        ["📢 Broadcast", "⬅️ Back"]
    ]
    reply_markup = ReplyKeyboardMarkup(admin_keyboard, resize_keyboard=True)
    msg = (
        "<b>Admin Panel</b>\n"
        "📊 Analytics: View bot usage stats, user growth, and job search analytics.\n"
        "👥 User Management: Export user data, see active users.\n"
        "📢 Broadcast: Send a message to all users.\n"
        "Use the menu below or /stats, /broadcast, /export_analytics."
    )
    await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode='HTML')

admin_handlers = [
    CommandHandler("stats", stats),
    CommandHandler("broadcast", broadcast),
    CommandHandler("export_analytics", export_analytics),
    CommandHandler("admin", admin),
    CommandHandler("admin_graphs", admin_graphs),
]
