# bot.py - Telegram Bot for PW Live Link Generator (FIXED & COMPLETE)
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import base64

# Logging setup for debugging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from environment variable (Heroku Config Var)
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not found in config vars!")
    raise ValueError("TELEGRAM_BOT_TOKEN missing")

# Your player base URL (GitHub Pages link)
PLAYER_BASE = "https://creator154.github.io/Resonance-Live-Pw/"

# PW API endpoints - CHANGE THESE TO FRESH ONES FROM ERUDA (404 error fix)
BATCH_LIST_URL = "https://api.pw.live/v2/batches/my"  # REPLACE WITH FRESH URL
LIVE_SESSION_URL = "https://api.pw.live/v1/live/{batch_id}/session"  # CONFIRM THIS TOO

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Namaste! Resonance PW Live Bot chal raha hai.\n\n"
        "PW Bearer Token bhej do (Bearer prefix ke saath ya bina).\n"
        "Main tere enrolled batches dikha dunga.\n"
        "Phir /live <batch_id> se live link milega.\n\n"
        "Example: /live 123456 Bearer eyJhbGciOi... "
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
        batches = data.get('data', [])  # CHANGE KEY IF DIFFERENT (Eruda se check)

        if not batches:
            await update.message.reply_text("Koi enrolled batch nahi mila. Token check kar.")
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
        await update.message.reply_text(f"Error: {str(e)}\nToken ya network check kar.")

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
        if not
