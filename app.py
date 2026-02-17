from flask import Flask, render_template_string, request
import requests
import base64
import os

app = Flask(__name__)

# Tera old GitHub Pages player ka base URL (agar change karna ho to yahan kar)
PLAYER_BASE = "https://creator154.github.io/Resonance-Live-Pw/"

# PW API endpoints (Eruda se confirm kar, change ho sakte hain)
BATCH_LIST_URL = "https://api.pw.live/v1/batches/enrolled"
LIVE_SESSION_URL = "https://api.pw.live/v1/live/{batch_id}/session"  # example

# Simple HTML form + result page
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Resonance PW Live Generator</title>
  <style>
    body {font-family:Arial; background:#111; color:#fff; padding:20px; text-align:center;}
    h1 {color:#ff3366;}
    form {max-width:500px; margin:20px auto;}
    input, button {width:100%; padding:12px; margin:10px 0; font-size:16px;}
    button {background:#ff3366; border:none; color:white; cursor:pointer;}
    ul {list-style:none; padding:0;}
    li {margin:15px 0; background:#222; padding:10px; border-radius:8px;}
    a {color:#ff3366; font-weight:bold;}
  </style>
</head>
<body>
  <h1>PW Live Link Generator (Resonance Batch)</h1>
  
  <form method="POST">
    <input type="text" name="token" placeholder="PW Bearer Token daalo" required>
    <button type="submit">Get My Batches</button>
  </form>

  {% if error %}
    <p style="color:red;">{{ error }}</p>
  {% endif %}

  {% if batches %}
    <h2>Tere Batches:</h2>
    <ul>
      {% for batch in batches %}
        <li>
          {{ batch.name }} (ID: {{ batch.id }})
          <form method="POST" action="/generate" style="display:inline;">
            <input type="hidden" name="token" value="{{ token }}">
            <input type="hidden" name="batch_id" value="{{ batch.id }}">
            <button type="submit">Live Link Banao</button>
          </form>
        </li>
      {% endfor %}
    </ul>
  {% endif %}

  {% if live_link %}
    <h2>Live Class Link Ready!</h2>
    <p>Click kar ke dekh lo:</p>
    <a href="{{ live_link }}" target="_blank">{{ live_link }}</a>
    <p>(Fullscreen mein better lagega)</p>
  {% endif %}
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        token = request.form.get('token').strip()
        if not token.startswith('Bearer '):
            token = 'Bearer ' + token

        headers = {
            'Authorization': token,
            'User-Agent': 'PW-App/1.0 (Android)',
            'Referer': 'https://www.pw.live/',
            'Accept': 'application/json'
        }

        try:
            r = requests.get(BATCH_LIST_URL, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            batches = data.get('data', [])  # adjust key if different
            return render_template_string(HTML, batches=batches, token=token)
        except requests.exceptions.RequestException as e:
            return render_template_string(HTML, error=f"Error: {str(e)} - Token ya endpoint check kar")
    
    return render_template_string(HTML)

@app.route('/generate', methods=['POST'])
def generate():
    token = request.form.get('token')
    batch_id = request.form.get('batch_id')

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

        # .m3u8 URL extract kar (Eruda se check kar exact key)
        m3u8 = data.get('stream_url') or data.get('hls_url') or data.get('playlist_url')
        if not m3u8:
            return render_template_string(HTML, error="Live stream URL nahi mila batch mein")

        # Simple enc (dev-boi jaisa feel)
        enc = base64.urlsafe_b64encode(m3u8.encode()).decode().rstrip('=')
        live_link = f"{PLAYER_BASE}?enc={enc}"

        return render_template_string(HTML, live_link=live_link)
    except Exception as e:
        return render_template_string(HTML, error=f"Generate error: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
