const express = require('express');
const AWS = require('aws-sdk');
const cookieParser = require('cookie-parser');
const path = require('path');
const fs = require('fs');

const app = express();
const port = process.env.PORT || 3000;

app.use(cookieParser());
app.use(express.json());
app.use(express.static('public'));  // static files ke liye folder bana lenge

// AWS CloudFront Signer setup
// Environment variables se secure load kar (Heroku config vars me set karna)
const KEY_PAIR_ID = process.env.CLOUDFRONT_KEY_PAIR_ID;
const PRIVATE_KEY = process.env.CLOUDFRONT_PRIVATE_KEY.replace(/\\n/g, '\n');  // PEM file ke newlines fix
const DOMAIN = 'd2pmv2a2n6a6po.cloudfront.net';  // tera domain
const RESOURCE = `https://${DOMAIN}/*`;  // wildcard sab cover

const signer = new AWS.CloudFront.Signer(KEY_PAIR_ID, PRIVATE_KEY);

// Simple auth route (class attend ke liye) - real me JWT ya password add kar
app.post('/generate-cookies', (req, res) => {
  // Yahan real auth check kar (abhi dummy)
  // if (!req.body.authToken) return res.status(401).send('Unauthorized');

  const expireTime = Math.floor(Date.now() / 1000) + 7200;  // 2 hours expiry (class ke liye adjust kar)

  const policy = JSON.stringify({
    Statement: [{
      Resource: RESOURCE,
      Condition: {
        DateLessThan: { 'AWS:EpochTime': expireTime }
      }
    }]
  });

  const cookies = signer.getSignedCookie({
    policy: policy
  });

  // Cookies set kar (domain .cloudfront.net pe set hone chahiye cross-domain ke liye)
  const cookieOptions = {
    domain: `.${DOMAIN}`,  // important: subdomain match ke liye
    path: '/',
    secure: true,
    httpOnly: true,
    sameSite: 'none'  // cross-site ke liye
  };

  res.cookie('CloudFront-Policy', cookies['CloudFront-Policy'], cookieOptions);
  res.cookie('CloudFront-Signature', cookies['CloudFront-Signature'], cookieOptions);
  res.cookie('CloudFront-Key-Pair-Id', cookies['CloudFront-Key-Pair-Id'], cookieOptions);

  res.json({ success: true, message: 'Cookies set! Ab live player use kar sakte ho.' });
});

// Player page serve kar (simple HTML embed)
app.get('/live', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'player.html'));
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
