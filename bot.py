from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
import os

app = Flask(__name__)


#client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
client = OpenAI(api_key="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")

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

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.form.get("Body", "").strip()
    sender = request.form.get("From", "")

    if sender not in conversations:
        conversations[sender] = []

    conversations[sender].append({
        "role": "user",
        "content": incoming_msg
    })

    if len(conversations[sender]) > 10:
        conversations[sender] = conversations[sender][-10:]

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT}
            ] + conversations[sender],
            max_tokens=300,
            temperature=0.7
        )
        bot_reply = response.choices[0].message.content
        conversations[sender].append({
            "role": "assistant",
            "content": bot_reply
        })

    except Exception as e:
        print(f"Error: {e}")
        bot_reply = "Sorry, we are busy right now. Please call +91 90000 11223"

    resp = MessagingResponse()
    resp.message(bot_reply)
    return str(resp)

@app.route("/", methods=["GET"])
def home():
    return "WhatsApp Bot is running!"

if __name__ == "__main__":
    app.run(debug=True, port=5000)