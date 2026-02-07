"""
Keep Alive Server for Replit
This creates a simple HTTP server that external services can ping
to keep the Replit running 24/7

Use with UptimeRobot or similar service to ping every 5 minutes
"""
from flask import Flask, jsonify
from threading import Thread
from datetime import datetime
import os

app = Flask(__name__)

# Track stats
start_time = datetime.now()
stats = {"requests": 0}

@app.route('/')
def home():
    stats["requests"] += 1
    uptime = str(datetime.now() - start_time).split('.')[0]
    return f"""
    <html>
    <head><title>Pikadump Auto Gen Drop</title></head>
    <body style="font-family: monospace; background: #1a1a2e; color: #0f0; padding: 20px;">
        <h1>🚀 Pikadump Auto Gen Drop Bot</h1>
        <p>Status: <b style="color: #0f0;">RUNNING</b></p>
        <p>Uptime: {uptime}</p>
        <p>Requests: {stats['requests']}</p>
        <hr>
        <p>Features:</p>
        <ul>
            <li>🔍 Real-time card scraping from Telegram</li>
            <li>🎲 Smart pattern-based card generation</li>
            <li>📤 Auto drop to @pikadump channel</li>
        </ul>
    </body>
    </html>
    """

@app.route('/health')
def health():
    stats["requests"] += 1
    uptime = (datetime.now() - start_time).total_seconds()
    return jsonify({
        "status": "healthy",
        "service": "auto_gen_drop",
        "uptime_seconds": int(uptime),
        "requests": stats["requests"]
    })

@app.route('/ping')
def ping():
    stats["requests"] += 1
    return "pong"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)

def keep_alive():
    """Start the keep-alive server in a background thread"""
    t = Thread(target=run, daemon=True)
    t.start()
    print("[OK] Keep-alive server started on port 8080")
    print("[OK] Add this URL to UptimeRobot for 24/7 uptime")
