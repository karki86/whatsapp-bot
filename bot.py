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

SYSTEM_PROMPT = """You are a helpful WhatsApp assistant for Thenmanan Restaurant in Chennai.
MENU: Chicken Biryani Rs.280, Mutton Biryani Rs.320, Fish Fry Rs.240, Pepper Chicken Rs.280, Samosa Rs.80, Falooda Rs.120
LOCATION: T Nagar Chennai. HOURS: 11AM-11PM. PHONE: 90000 11223.
Reply in customer language. Collect name, items, address for orders. Keep replies short with emojis."""

conversations = {}

def send_whatsapp(to, message):
    url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": message}}
    r = requests.post(url, headers=headers, json=payload)
    print(f"Sent: {r.status_code}")
    return r

def get_ai_reply(sender, text):
    if sender not in conversations:
        conversations[sender] = []
    conversations[sender].append({"role": "user", "content": text})
    if len(conversations[sender]) > 10:
        conversations[sender] = conversations[sender][-10:]
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + conversations[sender],
            max_tokens=300
        )
        reply = response.choices[0].message.content
        conversations[sender].append({"role": "assistant", "content": reply})
        print(f"Reply: {reply}")
        return reply
    except Exception as e:
        print(f"Error: {e}")
        return "Sorry please call +91 90000 11223"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Forbidden", 403
    data = request.get_json()
    print(f"Incoming: {data}")
    try:
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
        sender = msg["from"]
        if msg["type"] == "text":
            text = msg["text"]["body"]
            print(f"From {sender}: {text}")
            reply = get_ai_reply(sender, text)
            send_whatsapp(sender, reply)
    except Exception as e:
        print(f"Error: {e}")
    return "OK", 200

@app.route("/")
def home():
    return "NexoraAI Bot Live!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
