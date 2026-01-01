from flask import Flask, request
import requests
import os

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def get_all_users():
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    res = requests.get(f"{SUPABASE_URL}/rest/v1/users?select=first_name,last_name,email", headers=headers)
    return res.json()

def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text})

@app.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():
    update = request.json
    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"]["text"]

        if text == "/all_users":
            users = get_all_users()
            msg = "👥 All Users:\n" + "\n".join([f"{u['first_name']} {u['last_name']} ({u['email']})" for u in users])
            send_telegram(chat_id, msg)

    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
