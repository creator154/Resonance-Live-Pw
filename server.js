require('dotenv').config();
const express = require('express');
const jwt = require('jsonwebtoken');
const CryptoJS = require('crypto-js');
const cors = require('cors');

const app = express();
app.use(express.json());
app.use(cors());

const JWT_SECRET = process.env.JWT_SECRET;
const ENCRYPTION_SECRET = process.env.ENCRYPTION_SECRET || "your_fallback_strong_key_change_this_2026";

// ====================== JWT Authentication Middleware ======================
const authenticateJWT = (req, res, next) => {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ success: false, message: "Token missing or invalid" });
  }

  const token = authHeader.split(' ')[1];

  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.user = decoded;
    next();
  } catch (err) {
    return res.status(403).json({ success: false, message: "Invalid or expired token" });
  }
};

// ====================== Login Route (Teacher/Admin) ======================
app.post('/login', (req, res) => {
  const { username, password } = req.body;

  // Demo credentials (real mein database use karna)
  if (username === "admin" && password === "yourstrongpassword123") {
    const token = jwt.sign(
      { userId: 1, role: "teacher", username },
      JWT_SECRET,
      { expiresIn: '2h' }
    );
    res.json({ success: true, token: `Bearer ${token}` });
  } else {
    res.status(401).json({ success: false, message: "Invalid username or password" });
  }
});

// ====================== Generate Encrypted Live URL ======================
app.post('/generate-link', authenticateJWT, (req, res) => {
  const { batchId, validMinutes = 240 } = req.body; // Default 4 hours

  if (!batchId) {
    return res.status(400).json({ success: false, message: "Batch ID is required" });
  }

  const payload = {
    batchId: batchId,
    validTill: Date.now() + (validMinutes * 60 * 1000),
    issuedBy: req.user.userId,
    timestamp: Date.now()
  };

  const encrypted = CryptoJS.AES.encrypt(JSON.stringify(payload), ENCRYPTION_SECRET).toString();
  const liveUrl = `https://\( {req.get('host')}/live?enc= \){encodeURIComponent(encrypted)}`;

  res.json({
    success: true,
    batchId: batchId,
    liveUrl: liveUrl,
    expiresIn: `${validMinutes} minutes`,
    message: "Encrypted link generated successfully"
  });
});

// ====================== Live Class Player (Student opens this) ======================
app.get('/live', (req, res) => {
  const enc = req.query.enc;
  if (!enc) return res.status(400).send("<h2>❌ Invalid Link</h2>");

  try {
    const bytes = CryptoJS.AES.decrypt(enc, ENCRYPTION_SECRET);
    const data = JSON.parse(bytes.toString(CryptoJS.enc.Utf8));

    if (data.validTill < Date.now()) {
      return res.send("<h2>❌ Link Expired. Naya link maango teacher se.</h2>");
    }

    // Secure Player (yahan baad mein real slides add kar sakte ho)
    res.send(`
      <!DOCTYPE html>
      <html lang="hi">
      <head>
        <meta charset="UTF-8">
        <title>Live Class - Batch ${data.batchId}</title>
        <style>
          body { margin:0; background:#0f0f0f; color:#fff; font-family:Arial, sans-serif; text-align:center; padding:40px; }
          h1 { color:#00ff00; }
          #player { margin:30px auto; max-width:1000px; background:#1a1a1a; padding:30px; border-radius:12px; min-height:400px; }
        </style>
      </head>
      <body>
        <h1>🔴 Live Class Running</h1>
        <h2>Batch: ${data.batchId}</h2>
        <div id="player">
          <p>Slides yahan load honge (baad mein PPT/images add kar denge)</p>
          <p>Secure mode on - Download blocked</p>
        </div>
        <script>
          // Basic anti-download protection
          document.addEventListener('contextmenu', e => e.preventDefault());
        </script>
      </body>
      </html>
    `);
  } catch (e) {
    res.status(403).send("<h2>❌ Invalid or Tampered Link</h2>");
  }
});

// Root check
app.get('/', (req, res) => {
  res.json({
    message: "PW Live Class Server is Running",
    endpoints: {
      login: "POST /login",
      generate: "POST /generate-link (with JWT)",
      live: "GET /live?enc=..."
    }
  });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`Test: http://localhost:${PORT}`);
});
