"""
Keep Alive Server for Replit
This creates a simple HTTP server that external services can ping
to keep the Replit running 24/7
"""
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Auto Drop Bot is running!"

@app.route('/health')
def health():
    return {"status": "healthy", "service": "auto_drop"}

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Start the keep-alive server in a background thread"""
    t = Thread(target=run, daemon=True)
    t.start()
    print("[OK] Keep-alive server started on port 8080")
