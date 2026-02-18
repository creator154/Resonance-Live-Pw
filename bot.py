# bot.py - Telegram Bot for PW Live Link Generator
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import base64

# Logging setup (debug ke liye)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token config var se le (Heroku/Render mein set karna padega)
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN config var mein nahi mila!")
    raise ValueError("TELEGRAM_BOT_TOKEN missing")

# Tera player base URL (GitHub Pages wala)
PLAYER_BASE = "https://creator154.github.io/Resonance-Live-Pw/"

# PW API endpoints (Yahan fresh endpoint daal, Eruda se nikaal ke)
# Pehle wala 404 de raha tha, isliye yeh change karna padega
BATCH_LIST_URL = "https://api.pw.live/v2/batches/my"  # <-- YEH CHANGE KAR (fresh URL daal)
LIVE_SESSION_URL = "https://api.pw.live/v1/live/{batch_id}/session"  # confirm kar

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Namaste! Resonance PW Live Bot mein swagat hai.\n\n"
        "Apna PW Bearer Token bhej do (Bearer prefix ke saath ya bina).\n"
        "Main tere enrolled batches dikha dunga aur live link bana dunga!"
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
        logger.info(f"Fetching batches with token: {text[:20]}...")
        r = requests.get(BATCH_LIST_URL, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        batches = data.get('data', [])  # agar key alag ho to yahan change kar (Eruda se check)

        if not batches:
            await update.message.reply_text("Koi enrolled batch nahi mila. Token check kar ya PW app mein enrolled ho.")
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
        await update.message.reply_text("Batch ID daal do: /live <batch_id> [token if needed]")
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

        m3u8 = data.get('stream_url') or data.get('hls_url') or data.get('playlist_url')
        if not m3u8:
            await update.message.reply_text("Is batch mein live stream nahi mila.")
            return

        enc = base64.urlsafe_b64encode(m3u8.encode()).decode().rstrip('=')
        live_link = f"{PLAYER_BASE}?enc={enc}"

        await update.message.reply_text(
            f"Live Link Ready!\nBatch ID: {batch_id}\n\n{live_link}\n\nFullscreen mein dekhna 🔥"
        )
    except Exception as e:
        await update.message.reply_text(f"Live generate error: {str(e)}")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & \~filters.COMMAND, handle_message))
    application.add_handler(CommandHandler("live", generate_live))

    logger.info("Bot polling start ho raha hai...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
