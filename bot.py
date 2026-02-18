# bot.py - Telegram Bot for PW Live Link Generator (SYNTAX FIXED)
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import base64

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from config var
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN missing in config vars!")
    raise ValueError("TELEGRAM_BOT_TOKEN missing")

# Player base URL
PLAYER_BASE = "https://creator154.github.io/Resonance-Live-Pw/"

# PW API endpoints (CHANGE TO FRESH FROM ERUDA)
BATCH_LIST_URL = "https://api.pw.live/v2/batches/my"  # <-- FRESH ENDPOINT DAAL
LIVE_SESSION_URL = "https://api.pw.live/v1/live/{batch_id}/session"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Namaste! Resonance PW Live Bot chal raha hai.\n\n"
        "PW Bearer Token bhej do (Bearer prefix ke saath ya bina).\n"
        "Main tere enrolled batches dikha dunga.\n"
        "Phir /live <batch_id> se live link milega."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    if not text.startswith('Bearer '):
        text = 'Bearer ' + text

    headers = {
        'Authorization': text,
        'User-Agent': 'PW-App/1.0 (Android)',
        'Referer': 'https://www.pw.live/',
        'Accept': 'application/json'
    }

    try:
        logger.info("Fetching batches...")
        r = requests.get(BATCH_LIST_URL, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        batches = data.get('data', [])  # CHANGE KEY IF DIFFERENT

        if not batches:
            await update.message.reply_text("Koi batch nahi mila. Token check kar.")
            return

        msg = "Tere Batches:\n\n"
        for b in batches:
            batch_id = b.get('id')
            name = b.get('name', 'Unknown Batch')
            msg += f"• {name} (ID: {batch_id})\n"
            msg += f"Live link ke liye: /live {batch_id}\n\n"

        await update.message.reply_text(msg)

    except requests.exceptions.HTTPError as e:
        await update.message.reply_text(f"API Error {e.response.status_code}: {e.response.text[:200]}")
    except Exception as e:
        logger.error(f"Error in handle_message: {str(e)}")
        await update.message.reply_text(f"Error: {str(e)}")

async def generate_live(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Batch ID daal do: /live <batch_id> [token optional]")
        return

    batch_id = context.args[0]
    token = 'Bearer ' + ' '.join(context.args[1:]) if len(context.args) > 1 else None

    if not token:
        await update.message.reply_text("Token bhi daal do: /live <batch_id> Bearer xxxx")
        return

    headers = {
        'Authorization': token,
        'User-Agent': 'PW-App/1.0 (Android)',
        'Referer': 'https://www.pw.live/'
    }

    try:
        url = LIVE_SESSION_URL.format(batch_id=batch_id)
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()

        m3u8 = data.get('stream_url') or data.get('hls_url') or None
        if not m3u8:
            await update.message.reply_text("Live stream nahi mila.")
            return

        enc = base64.urlsafe_b64encode(m3u8.encode()).decode().rstrip('=')
        live_link = f"{PLAYER_BASE}?enc={enc}"
        await update.message.reply_text(f"Live Link Ready!\n{live_link}")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & \~filters.COMMAND, handle_message))
    application.add_handler(CommandHandler("live", generate_live))

    logger.info("Bot polling start ho raha hai...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
