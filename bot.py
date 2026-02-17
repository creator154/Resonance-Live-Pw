import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import requests
import base64

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Tera player base URL
PLAYER_BASE = "https://creator154.github.io/Resonance-Live-Pw/"

# PW API endpoints (Eruda se confirm kar, change ho sakte hain)
BATCH_LIST_URL = "https://api.pw.live/v2/batches/my"  # yeh sahi endpoint daal (pehle 404 tha, fresh nikaal)
LIVE_SESSION_URL = "https://api.pw.live/v1/live/{batch_id}/session"

# Bot token config var se le (Heroku/Render pe set kar)
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable nahi mila!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Namaste! PW Live Link Generator Bot mein swagat hai.\n"
        "Apna PW Bearer Token bhejo (Bearer prefix ke saath).\n"
        "Main tere batches ki list bhej dunga, phir live link bana dunga!"
    )

async def handle_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip()
    if not token.startswith('Bearer '):
        token = 'Bearer ' + token

    headers = {
        'Authorization': token,
        'User-Agent': 'PW-App/1.0 (Android)',
        'Referer': 'https://www.pw.live/'
    }

    try:
        r = requests.get(BATCH_LIST_URL, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        batches = data.get('data', [])  # adjust key if different

        if not batches:
            await update.message.reply_text("Koi batch nahi mila. Token check kar ya PW app mein enrolled ho.")
            return

        keyboard = []
        for batch in batches:
            batch_id = batch.get('id')
            batch_name = batch.get('name', 'Unknown Batch')
            keyboard.append([InlineKeyboardButton(batch_name, callback_data=f"batch_{batch_id}_{token}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Tere Batches:", reply_markup=reply_markup)

    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"Error: {str(e)}\nToken ya endpoint check kar (404 aa raha to endpoint galat hai)")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split('_')
    if data[0] == "batch":
        batch_id = data[1]
        token = '_'.join(data[2:])  # token mein underscore ho sakta hai isliye join

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

            m3u8 = data.get('stream_url') or data.get('hls_url') or "NO_STREAM"
            if m3u8 == "NO_STREAM":
                await query.edit_message_text("Is batch mein live stream nahi mila.")
                return

            enc = base64.urlsafe_b64encode(m3u8.encode()).decode().rstrip('=')
            live_link = f"{PLAYER_BASE}?enc={enc}"

            await query.edit_message_text(
                f"Live Link Ready!\n\n{batch_name} ke liye:\n{live_link}\n\nFullscreen mein dekhna 🔥"
            )
        except Exception as e:
            await query.edit_message_text(f"Live generate error: {str(e)}")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & \~filters.COMMAND, handle_token))
    application.add_handler(CallbackQueryHandler(button_callback))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
