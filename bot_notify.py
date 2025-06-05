
import os, time, json, requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def send_message(text):
    url = f"{API_URL}/sendMessage"
    resp = requests.post(url, json={"chat_id": CHAT_ID, "text": text})
    resp.raise_for_status()

def await_reply(timeout_sec=1800):
    """Polls for a reply that contains numbers like 1 3 4"""
    url = f"{API_URL}/getUpdates"
    start = time.time()
    last_update_id = None
    while time.time() - start < timeout_sec:
        resp = requests.get(url, params={"timeout": 5, "offset": last_update_id or ""})
        resp.raise_for_status()
        data = resp.json()["result"]
        if data:
            last_update_id = data[-1]["update_id"] + 1
            text = data[-1]["message"]["text"].strip()
            if text and all(c.isdigit() or c.isspace() or c == ',' for c in text):
                return text
    return ""
