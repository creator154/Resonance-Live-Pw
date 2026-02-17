# bot.py
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import base64

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Config vars se token le
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN nahi mila config vars mein!")
    exit()

# Player base URL (tera GitHub wala)
PLAYER_BASE = "https://creator154.github.io/Resonance-Live-Pw/"

# PW API endpoints (Eruda se fresh kar le, yeh example hai)
BATCH_LIST_URL = "https://api.pw.live/v2/batches/my"  # yeh 404 de raha tha, fresh daal
LIVE_SESSION_URL = "https://api.pw.live/v1/live/{batch_id}/session"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Namaste! PW Live Bot mein swagat hai.\n"
        "Apna PW Bearer Token bhej do (Bearer prefix ke saath).\n"
        "Main batches dikhaunga aur live link bana dunga!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.startswith('Bearer '):
        text = 'Bearer ' + text

    headers = {
        'Authorization': text,
        'User-Agent': 'PW-App/1.0 (Android)',
        'Referer': 'https://www.pw.live/'
    }

    try:
        r = requests.get(BATCH_LIST_URL, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            batches = data.get('data', [])  # adjust if key different
            if not batches:
                await update.message.reply_text("Koi batch nahi mila. Token check kar.")
                return

            msg = "Tere Batches:\n\n"
            for b in batches:
                batch_id = b.get('id')
                name = b.get('name', 'Unknown')
                msg += f"• {name} (ID: {batch_id})\n"
                msg += f"Live link chahiye? Reply kar: /live {batch_id}\n\n"

            await update.message.reply_text(msg)
        else:
            await update.message.reply_text(f"API Error {r.status_code}: {r.text[:200]}")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def generate_live(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Batch ID daal do: /live <batch_id>")
        return

    batch_id = context.args[0]
    token = 'Bearer ' + " ".join(context.args[1:]) if len(context.args) > 1 else None

    if not token:
        await update.message.reply_text("Token bhi daal do: /live <batch_id> <token>")
        return

    headers = {
        'Authorization': token,
        'User-Agent': 'PW-App/1.0 (Android)',
        'Referer': 'https://www.pw.live/'
    }

    try:
        r = requests.get(LIVE_SESSION_URL.format(batch_id=batch_id), headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            m3u8 = data.get('stream_url') or data.get('hls_url') or None
            if not m3u8:
                await update.message.reply_text("Live stream URL nahi mila is batch mein.")
                return

            enc = base64.urlsafe_b64encode(m3u8.encode()).decode().rstrip('=')
            live_link = f"{PLAYER_BASE}?enc={enc}"
            await update.message.reply_text(f"Live Link Ready!\n{live_link}\nFullscreen mein dekhna 🔥")
        else:
            await update.message.reply_text(f"Live API Error {r.status_code}: {r.text[:200]}")
    except Exception as e:
        await update.message.reply_text(f"Generate error: {str(e)}")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & \~filters.COMMAND, handle_token))
    application.add_handler(CommandHandler("live", generate_live))

    logger.info("Bot polling start ho raha hai...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
