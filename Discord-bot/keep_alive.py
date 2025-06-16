from flask import Flask
import threading
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def index():
    return "Discord Bot is alive and running!"

@app.route('/health')
def health():
    return {"status": "service", "version": "Bot is operational"}

@app.route('/status')
def status():
    return {
        "status": "online",
        "service": "scope.",
        "version": "1.0.0"
    }

def run():
    """Run the Flask app"""
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Error running keep-alive server: {e}")

def keep_alive():
    """Start the keep-alive server in a separate thread"""
    try:
        t = threading.Thread(target=run)
        t.daemon = True
        t.start()
        logger.info("Keep-alive server started on port 5000")
    except Exception as e:
        logger.error(f"Error starting keep-alive server: {e}")
