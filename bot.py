from flask import Flask, request
import os, requests

app = Flask(__name__)

ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "1245362218657445")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "nexoraai2026")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

PROMPT = "You are WhatsApp assistant for Thenmanan Restaurant Chennai. Menu: Chicken Biryani Rs280, Mutton Biryani Rs320, Fish Fry Rs240, Pepper Chicken Rs280, Samosa Rs80, Falooda Rs120. Hours 11AM-11PM T Nagar. Reply short with emojis."

chats = {}

def ask_gpt(sender, text):
    chats.setdefault(sender, []).append({"role":"user","content":text})
    if len(chats[sender]) > 10:
        chats[sender] = chats[sender][-10:]
    headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
    body = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role":"system","content":PROMPT}] + chats[sender],
        "max_tokens": 200
    }
    r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body)
    print(f"OpenAI status: {r.status_code}")
    reply = r.json()["choices"][0]["message"]["content"]
    chats[sender].append({"role":"assistant","content":reply})
    print(f"Reply: {reply}")
    return reply

def send_wa(to, msg):
    url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product":"whatsapp","to":to,"type":"text","text":{"body":msg}}
    r = requests.post(url, headers=headers, json=data)
    print(f"WA send: {r.status_code}")

@app.route("/webhook", methods=["GET","POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
        return "Forbidden", 403
    try:
        data = request.get_json()
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
        if msg["type"] == "text":
            sender = msg["from"]
            text = msg["text"]["body"]
            print(f"From {sender}: {text}")
            reply = ask_gpt(sender, text)
            send_wa(sender, reply)
    except Exception as e:
        print(f"Error: {e}")
    return "OK", 200

@app.route("/")
def home():
    return "NexoraAI Bot Live!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
