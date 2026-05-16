"""
FoodieBot Chennai - Minimal Test Version
Use this to confirm Twilio sending works, then swap back to full bot.py
"""
import os
import threading
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TWILIO_SID   = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH  = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM  = os.environ.get("TWILIO_FROM", "whatsapp:+14155238886")


def send_whatsapp(to, body):
    if not TWILIO_SID or not TWILIO_AUTH:
        print(f"[DRY RUN] to={to}\n{body}")
        return
    to_num = f"whatsapp:{to}" if not to.startswith("whatsapp:") else to
    try:
        resp = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json",
            auth=(TWILIO_SID, TWILIO_AUTH),
            data={"From": TWILIO_FROM, "To": to_num, "Body": body},
            timeout=15
        )
        print(f"[SENT] status={resp.status_code} response={resp.text[:100]}")
    except Exception as e:
        print(f"[SEND ERROR] {e}")


def get_reply(body):
    lower = (body or "").lower().strip()
    if lower in ("hi", "hello", "hey"):
        return (
            "👋 *Welcome to FoodieBot Chennai!* 🍽️\n"
            "_Powered by NexoraAI — SuperBot v4_\n\n"
            "🌆 Good evening! Time for *dinner*!\n"
            "Try: _biryani_ | _chicken_ | _dosa_ | _idly_\n\n"
            "📍 Share location → restaurants within 4 km!\n"
            "🎙️ Voice order: '2 idly 1 vada'\n\n"
            "*Commands:* nearby · veg · top · all"
        )
    elif "biryani" in lower:
        return (
            "🔍 *Biryani* found at:\n\n"
            "1️⃣ 🍗 Anjappar Chettinad — Chicken Biryani ₹280\n"
            "2️⃣ 🍖 Buhari Restaurant — Special Biryani ₹350\n"
            "3️⃣ 🍛 Kaaraikudi — Mutton Biryani ₹400\n\n"
            "Type *1*, *2* or *3* to order!"
        )
    elif "idly" in lower or "idli" in lower or "dosa" in lower:
        return (
            "🔍 Found!\n\n"
            "1️⃣ 🥣 Hotel Saravana Bhavan — Idly ₹50\n"
            "2️⃣ 🥣 Murugan Idli Shop — Soft Idly ₹80\n\n"
            "Type *1* or *2* to order!"
        )
    elif lower in ("veg", "veg only"):
        return (
            "🟢 *Veg Restaurants:*\n\n"
            "1️⃣ 🥣 Hotel Saravana Bhavan — T Nagar\n"
            "2️⃣ 🥣 Murugan Idli Shop — Mylapore\n"
            "3️⃣ 🍕 Cream Centre — Nungambakkam\n"
            "4️⃣ 🥐 Bombay Bakery — Adyar\n\n"
            "Type *1-4* to order!"
        )
    elif lower in ("all", "top", "nearby"):
        return (
            "🍽️ *All Restaurants — Chennai:*\n\n"
            "1️⃣ 🥣 Saravana Bhavan · T Nagar 🟢\n"
            "2️⃣ 🍗 Anjappar · Anna Nagar 🔴\n"
            "3️⃣ 🥣 Murugan Idli · Mylapore 🟢\n"
            "4️⃣ 🍖 Buhari · Egmore 🔴\n"
            "5️⃣ 🍕 Cream Centre · Nungambakkam 🟢\n"
            "6️⃣ 🍛 Kaaraikudi · Velachery 🔴\n"
            "7️⃣ 🥐 Bombay Bakery · Adyar 🟢\n"
            "8️⃣ 🦐 Seafood Bay · Besant Nagar 🔴\n\n"
            "Type *1-8* to order! 📍 Share location for 4 km filter"
        )
    else:
        return (
            f"🔍 Searching for *{body}*...\n\n"
            "Try: _biryani_ · _idly_ · _dosa_ · _chicken_ · _veg_ · _all_\n\n"
            "📍 Share location for nearest restaurants!"
        )


@app.route("/")
def index():
    return "FoodieBot SuperBot v4 is live! 🚀", 200


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "version": "SuperBot v4.0 (minimal)",
        "twilio_sid_set":  bool(TWILIO_SID),
        "twilio_auth_set": bool(TWILIO_AUTH),
        "twilio_from":     TWILIO_FROM
    })


@app.route("/debug/env")
def debug_env():
    return jsonify({
        "TWILIO_ACCOUNT_SID": TWILIO_SID[:8] + "..." if TWILIO_SID else "MISSING",
        "TWILIO_AUTH_TOKEN":  TWILIO_AUTH[:8] + "..." if TWILIO_AUTH else "MISSING",
        "TWILIO_FROM":        TWILIO_FROM,
        "status": "ok" if TWILIO_SID and TWILIO_AUTH else "MISSING CREDENTIALS"
    })


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return "FoodieBot webhook is live!", 200

    sender    = request.form.get("From", "").replace("whatsapp:", "")
    body      = request.form.get("Body", "").strip()
    latitude  = request.form.get("Latitude")
    longitude = request.form.get("Longitude")

    print(f"[WEBHOOK] from={sender!r} body={body!r} lat={latitude} lng={longitude}")

    if not sender:
        return jsonify({"status": "no sender"}), 400

    # Location pin shared
    if latitude and longitude:
        reply = f"📍 Got your location! ({latitude}, {longitude})\n\nFinding restaurants near you within 4 km... 🔍"
    else:
        reply = get_reply(body)

    print(f"[REPLY] {reply[:80]}...")

    # Send in background — return 200 to Twilio immediately
    def bg():
        send_whatsapp(sender, reply)
    threading.Thread(target=bg, daemon=True).start()

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(debug=True, port=10000)
