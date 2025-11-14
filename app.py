import os
import json
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
APP_WEBHOOK_SECRET = os.getenv("APP_WEBHOOK_SECRET")
PORT = int(os.environ.get("PORT", 5000))
    

app = Flask(__name__)

# Load rule-based replies
with open("rules.json", "r", encoding="utf-8") as f:
    RULES = json.load(f)

# ✅ Function to send WhatsApp messages
def send_whatsapp(to_number, message):
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, headers=headers, json=payload)
    print("📩 WhatsApp API Response:", response.json())
    return response.json()

# ✅ Health check
@app.route("/", methods=["GET"])
def home():
    return "🚀 WhatsApp Bot is running", 200

# ✅ WhatsApp verification (for webhook setup in Meta dashboard)
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verified")
        return challenge, 200
    else:
        print("❌ Verification failed")
        return "Forbidden", 403

# ✅ WhatsApp incoming messages (rule-based replies)
@app.route("/webhook", methods=["POST"])
def whatsapp_inbox():
    data = request.json
    print("📩 Incoming WhatsApp Message:", data)

    try:
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
        user_text = msg["text"]["body"].strip().lower()
        sender = msg["from"]

        reply = RULES.get(user_text, RULES.get("help", "Sorry, I don’t understand. Type 'help'"))
        send_whatsapp(sender, reply)

    except Exception as e:
        print("⚠️ Incoming webhook error:", e)

    return "ok", 200

# ✅ Webhook for Google Sheet → send delivery details
@app.route("/sheet-webhook", methods=["POST"])
def sheet_webhook():
    try:
        data = request.json
        print("📩 Sheet Trigger:", data)

        customer_name = data.get("customerName")
        customer_number = str(data.get("customerNumber"))
        delivery_boy = data.get("deliveryBoyName")
        delivery_number = data.get("deliveryBoyNumber")

        if customer_name and delivery_boy:
            message = (
                f"Hello {customer_name},\n\n"
                f"Your delivery boy is {delivery_boy} 📦\n"
                f"Contact: {delivery_number}\n\n"
                "Thank you for choosing Quick Ironing Services! 😊"
            )
            send_whatsapp(customer_number, message)

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print("❌ Error:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=PORT, debug=True)
