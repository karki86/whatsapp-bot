from flask import Flask, request
import openai
import os
import json
import requests

app = Flask(__name__)

openai.api_key = "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"
ACCESS_TOKEN = "EAAcKMsH2f8kBRTvTZBOMm4U2kSrbtZBZCxkFm4SlXTKNRT6NSADn8aaK9IGTrvxS5TRTjNUgbjDQPxqWA1AG3FTI8g46FNYOFJC9VNUeili36HJVWGsxAfP5GgymQEbnyLFMs3FeU1RIzB2EYKGpykwvBpVUdS9ZB5pDPXvoZB4DH9BZBZANe8vnZAuCruIOiXA6ZCfZBZATfQ0JVsfcR6uvKr34RZBQsPs5ZCBTTB8KYD1SKQ7aLRqBmWouJW4L58GDx2CoIhERPt38c35yaJWFDcIafq3QQ"
PHONE_NUMBER_ID = "1245362218657445"
VERIFY_TOKEN = "nexoraai2026"

SYSTEM_PROMPT = """
You are a helpful WhatsApp assistant for Thenmanan Restaurant in Chennai.

MENU:
- Chicken Biryani: Rs.280
- Mutton Biryani: Rs.320
- Fish Fry: Rs.240
- Pepper Chicken: Rs.280
- Samosa (2pcs): Rs.80
- Falooda: Rs.120

LOCATION: T Nagar, Chennai
HOURS: 11AM to 11PM daily
PHONE: +91 90000 11223
DELIVERY: Within 5km, 45 minutes

RULES:
- Always reply in the same language the customer uses
- For orders collect: name, items, quantity, delivery address
- Keep replies short and friendly
- Add relevant emojis
- For payment say: Pay on delivery or GPay to 90000 11223
- Never make up prices not in the menu
"""

conversations = {}

def send_message(to, message):
    url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    requests.post(url, headers=headers, json=data)

def get_reply(sender, message):
    if sender not in conversations:
        conversations[sender] = []
    conversations[sender].append({
        "role": "user",
        "content": message
    })
    if len(conversations[sender]) > 10:
        conversations[sender] = conversations[sender][-10:]
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT}
            ] + conversations[sender],
            max_tokens=300,
            temperature=0.7
        )
        reply = response.choices[0].message.content
        conversations[sender].append({
            "role": "assistant",
            "content": reply
        })
        return reply
    except Exception as e:
        print(f"Error: {e}")
        return "Sorry, please call +91 90000 11223"

@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        if "messages" in value:
            msg = value["messages"][0]
            sender = msg["from"]
            if msg["type"] == "text":
                text = msg["text"]["body"]
                reply = get_reply(sender, text)
                send_message(sender, reply)
    except Exception as e:
        print(f"Error: {e}")
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "NexoraAI WhatsApp Bot is Live!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
