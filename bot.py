from flask import Flask, request
import openai, os, requests

app = Flask(__name__)

# ── PASTE YOUR REAL KEYS HERE ──
openai.api_key = "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"
ACCESS_TOKEN = "EAAcKMsH2f8kBRaETVGz0VEuQuFLxrqEyuDaoIt6Lcr02uA6ZB2vuPvuI4XYR3mfq8asmKVYmoo5UUhvTawKbF0SKLrAHA6X2rEepca8ZBfZC2Sh1jWegCLmMnWRvCMq8oV89R4cajqeEdO9lx6TrImYTBdhaNeZAKptzZArCKjXQSPjjOZBgjJHDb87YYziH4xQ85VzbbZCTt0DnZCLYpdvP48lRT0EFksCUNvnQgDGxPQJjdtktEN6pqDWSZBqUmo0fOYMPmZBTB48QsFkW6In6jhRec4FAZDZD"
PHONE_NUMBER_ID = "1245362218657445"
VERIFY_TOKEN = "nexoraai2026"

PROMPT = "You are a WhatsApp assistant for Thenmanan Restaurant Chennai. Menu: Chicken Biryani Rs280, Mutton Biryani Rs320, Fish Fry Rs240, Pepper Chicken Rs280, Samosa Rs80, Falooda Rs120. Hours 11AM-11PM. Delivery within 5km. Reply short with emojis."

chats = {}

@app.route("/webhook", methods=["GET","POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
        return "Error", 403
    try:
        msg = request.get_json()["entry"][0]["changes"][0]["value"]["messages"][0]
        if msg["type"] == "text":
            num = msg["from"]
            txt = msg["text"]["body"]
            chats.setdefault(num, []).append({"role":"user","content":txt})
            r = openai.chat.completions.create(model="gpt-3.5-turbo",messages=[{"role":"system","content":PROMPT}]+chats[num][-10:],max_tokens=200)
            reply = r.choices[0].message.content
            chats[num].append({"role":"assistant","content":reply})
            requests.post(f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages",headers={"Authorization":f"Bearer {ACCESS_TOKEN}","Content-Type":"application/json"},json={"messaging_product":"whatsapp","to":num,"type":"text","text":{"body":reply}})
            print(f"Replied to {num}: {reply}")
    except Exception as e:
        print(f"Error: {e}")
    return "OK", 200

@app.route("/")
def home():
    return "NexoraAI Bot Live!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
