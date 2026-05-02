from flask import Flask, request
import openai
import os
import requests

app = Flask(__name__)

# ── PASTE YOUR REAL KEYS HERE ──
openai.api_key = "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"
ACCESS_TOKEN = "EAAcKMsH2f8kBRaETVGz0VEuQuFLxrqEyuDaoIt6Lcr02uA6ZB2vuPvuI4XYR3mfq8asmKVYmoo5UUhvTawKbF0SKLrAHA6X2rEepca8ZBfZC2Sh1jWegCLmMnWRvCMq8oV89R4cajqeEdO9lx6TrImYTBdhaNeZAKptzZArCKjXQSPjjOZBgjJHDb87YYziH4xQ85VzbbZCTt0DnZCLYpdvP48lRT0EFksCUNvnQgDGxPQJjdtktEN6pqDWSZBqUmo0fOYMPmZBTB48QsFkW6In6jhRec4FAZDZD"
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
- Always reply in same language as customer
- For orders collect: name, items, quantity, delivery address
- Keep replies short and friendly
- Add emojis
- For payment say: Pay on delivery or GPay to 90000 11223
- Never make up prices not in menu
"""

conversations = {}

def send_whatsapp(to, message):
    url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    r = requests.post(url, headers=headers, json=payload)
    print(f"Send response: {r.status_code} {r.text}")
    return r

def get_ai_reply(sender, user_message):
    if sender not in conversations:
        conversations[sender] = []
    conversations[sender].append({
        "role": "user",
        "content": user_message
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
        print(f"AI Reply: {reply}")
        return reply
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return "Sorry, please call +91 90000 11223"

@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    print(f"Verify: mode={mode} token={token}")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook verified!")
        return challenge, 200
    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print(f"Incoming data: {data}")
    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        if "messages" in value:
            msg = value["messages"][0]
            sender = msg["from"]
            msg_type = msg["type"]
            print(f"Message from {sender}: type={msg_type}")
            if msg_type == "text":
                text = msg["text"]["body"]
                print(f"Text: {text}")
                reply = get_ai_reply(sender, text)
                result = send_whatsapp(sender, reply)
                print(f"Sent to {sender}: {reply}")
    except Exception as e:
        print(f"Webhook Error: {e}")
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "NexoraAI WhatsApp Bot is Live!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
