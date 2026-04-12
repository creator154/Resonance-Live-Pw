require('dotenv').config();
const express = require('express');
const jwt = require('jsonwebtoken');
const CryptoJS = require('crypto-js');
const cors = require('cors');
const TelegramBot = require('node-telegram-bot-api');

const app = express();
app.use(express.json());
app.use(cors());

const JWT_SECRET = process.env.JWT_SECRET;
const ENCRYPTION_SECRET = process.env.ENCRYPTION_SECRET;
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const HEROKU_URL = process.env.HEROKU_URL;

if (!TELEGRAM_BOT_TOKEN) {
  console.warn("⚠️ TELEGRAM_BOT_TOKEN missing");
}

// ✅ Telegram Bot (Polling Mode)
const bot = new TelegramBot(TELEGRAM_BOT_TOKEN, { polling: true });

console.log("🤖 Telegram Bot Started!");

// ✅ Commands
bot.onText(/\/start/, (msg) => {
  bot.sendMessage(
    msg.chat.id,
    "Welcome! Batch ID daal ke live link generate karne ke liye:\n/generate <batchId>"
  );
});

bot.onText(/\/generate (.+)/, async (msg, match) => {
  const batchId = match[1].trim();
  const chatId = msg.chat.id;

  try {
    const payload = {
      batchId,
      validTill: Date.now() + (240 * 60 * 1000),
      timestamp: Date.now()
    };

    const encrypted = CryptoJS.AES.encrypt(
      JSON.stringify(payload),
      ENCRYPTION_SECRET
    ).toString();

    // ✅ FIXED URL
    const liveUrl = `${HEROKU_URL}/live?enc=${encodeURIComponent(encrypted)}`;

    await bot.sendMessage(
      chatId,
      `✅ Batch: ${batchId}\n🔴 Live Class Link Ready!`,
      {
        reply_markup: {
          inline_keyboard: [[{ text: "▶️ Live Class Join Karo", url: liveUrl }]]
        }
      }
    );

    console.log(`✅ Link sent for batch ${batchId}`);
  } catch (err) {
    console.error(err);
    bot.sendMessage(chatId, "❌ Error: Link generate nahi ho saka");
  }
});

// ====================== JWT Middleware ======================
const authenticateJWT = (req, res, next) => {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ success: false, message: "Token required" });
  }

  const token = authHeader.split(' ')[1];

  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.user = decoded;
    next();
  } catch (err) {
    return res.status(403).json({ success: false, message: "Invalid token" });
  }
};

// ====================== Routes ======================
app.post('/login', (req, res) => {
  const { username } = req.body;

  if (!username) {
    return res.status(400).json({ message: "Username required" });
  }

  const token = jwt.sign({ username }, JWT_SECRET, { expiresIn: '1h' });

  res.json({ token });
});

app.post('/generate-link', authenticateJWT, (req, res) => {
  const { batchId } = req.body;

  if (!batchId) {
    return res.status(400).json({ message: "Batch ID required" });
  }

  const payload = {
    batchId,
    validTill: Date.now() + (240 * 60 * 1000)
  };

  const encrypted = CryptoJS.AES.encrypt(
    JSON.stringify(payload),
    ENCRYPTION_SECRET
  ).toString();

  const link = `${HEROKU_URL}/live?enc=${encodeURIComponent(encrypted)}`;

  res.json({ link });
});

app.get('/live', (req, res) => {
  const enc = req.query.enc;

  if (!enc) return res.send("<h2>❌ Invalid Link</h2>");

  try {
    const bytes = CryptoJS.AES.decrypt(enc, ENCRYPTION_SECRET);
    const data = JSON.parse(bytes.toString(CryptoJS.enc.Utf8));

    if (data.validTill < Date.now()) {
      return res.send("<h2>❌ Link Expired</h2>");
    }

    res.send(`<h1>🔴 Live Class - Batch ${data.batchId}</h1>`);
  } catch {
    res.send("<h2>❌ Invalid Link</h2>");
  }
});

app.get('/', (req, res) => {
  res.json({
    message: "Server + Telegram Bot Running",
    commands: "/start , /generate <batchId>"
  });
});

// ====================== Start Server ======================
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
});
