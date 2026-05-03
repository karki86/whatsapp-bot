from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
import random
import json
from datetime import datetime, timedelta

app = Flask(__name__)

OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
MASTER_KEY  = os.environ.get("MASTER_KEY", "NEXORAAI2026")   # Admin access

# ════════════════════════════════════════════════════════════════════════════
# MULTI-RESTAURANT DATABASE  (replace with real DB in production)
# Each restaurant pays ₹5,000/month subscription
# ════════════════════════════════════════════════════════════════════════════
RESTAURANTS = {
    # ── Restaurant 1 ──────────────────────────────────────────────────────
    "whatsapp:+917010624989": {
        "id": "R001",
        "name": "Thenmanan Restaurant",
        "tagline": "Authentic Chennai Cuisine Since 1990",
        "location": "23/7, Usman Road, T Nagar, Chennai 600 017",
        "phone": "+91 90000 11223",
        "hours": "11:00 AM – 11:00 PM",
        "breakfast": "7:30 AM – 11:00 AM",
        "gpay": "thenmanan@okicici",
        "phonepe": "thenmanan@ybl",
        "upi": "thenmanan@upi",
        "card_link": "https://rzp.io/l/thenmanan",
        "delivery_km": 5,
        "delivery_mins": 45,
        "delivery_charge": 40,
        "min_order": 150,
        "rating": 4.8,
        "reviews_count": "1,240",
        "established": "1990",
        "cuisine": "South Indian",
        "subscription": "active",
        "plan": "pro",
        "plan_expiry": "2026-06-01",
        "menu": {
            "🍗 Biryani": {
                "Chicken Biryani":        {"price":280,"rating":4.9,"orders":2840,"spice":"Medium","time":"20 mins"},
                "Mutton Biryani":         {"price":320,"rating":4.8,"orders":1920,"spice":"Medium","time":"25 mins"},
                "Prawn Biryani":          {"price":350,"rating":4.7,"orders":980, "spice":"Medium-Hot","time":"25 mins"},
                "Vegetable Biryani":      {"price":180,"rating":4.5,"orders":640, "spice":"Mild","time":"15 mins"},
                "Egg Biryani":            {"price":200,"rating":4.6,"orders":760, "spice":"Medium","time":"15 mins"},
                "Semiya Chicken Biryani": {"price":260,"rating":4.8,"orders":1100,"spice":"Medium","time":"20 mins"},
            },
            "🥩 Non-Veg Mains": {
                "Pepper Chicken Masala":  {"price":280,"rating":4.9,"orders":2100,"spice":"Hot","time":"15 mins"},
                "Chicken Butter Masala":  {"price":300,"rating":4.7,"orders":1400,"spice":"Mild","time":"15 mins"},
                "Mutton Kulambu":         {"price":340,"rating":4.8,"orders":980, "spice":"Hot","time":"20 mins"},
                "Fish Curry":             {"price":260,"rating":4.6,"orders":840, "spice":"Medium-Hot","time":"15 mins"},
                "Chicken 65":             {"price":260,"rating":4.8,"orders":1680,"spice":"Hot","time":"15 mins"},
            },
            "🥬 Veg Mains": {
                "Paneer Butter Masala":   {"price":220,"rating":4.6,"orders":840,"spice":"Mild","time":"15 mins"},
                "Dal Tadka":              {"price":160,"rating":4.5,"orders":620,"spice":"Mild","time":"10 mins"},
                "Palak Paneer":           {"price":200,"rating":4.5,"orders":560,"spice":"Mild","time":"15 mins"},
            },
            "🫓 Breads & Rice": {
                "Parotta":       {"price":25,"rating":4.7,"orders":2400,"spice":"None","time":"8 mins"},
                "Butter Naan":   {"price":40,"rating":4.6,"orders":1800,"spice":"None","time":"10 mins"},
                "Steamed Rice":  {"price":60,"rating":4.4,"orders":1600,"spice":"None","time":"10 mins"},
                "Ghee Rice":     {"price":80,"rating":4.6,"orders":980, "spice":"None","time":"12 mins"},
            },
            "🥟 Starters": {
                "Chicken Samosa (2pcs)":  {"price":80, "rating":4.8,"orders":2100,"spice":"Medium","time":"10 mins"},
                "Fish Fry":               {"price":240,"rating":4.9,"orders":1600,"spice":"Medium-Hot","time":"15 mins"},
                "Chicken 65 Starter":     {"price":220,"rating":4.8,"orders":1800,"spice":"Hot","time":"12 mins"},
            },
            "🍦 Desserts & Drinks": {
                "Special Falooda": {"price":120,"rating":4.9,"orders":1840,"spice":"None","time":"5 mins"},
                "Mango Lassi":     {"price":80, "rating":4.7,"orders":1100,"spice":"None","time":"5 mins"},
                "Masala Chai":     {"price":40, "rating":4.5,"orders":1800,"spice":"None","time":"3 mins"},
            },
            "🌅 Breakfast": {
                "Idiyappam + Paya":       {"price":180,"rating":4.9,"orders":2400,"spice":"Medium","time":"10 mins"},
                "Idly (4pcs) + Sambar":   {"price":80, "rating":4.7,"orders":1800,"spice":"Mild","time":"8 mins"},
                "Dosa + Chutney":         {"price":90, "rating":4.8,"orders":2100,"spice":"Mild","time":"8 mins"},
            },
        },
        "offers": {
            "WELCOME10":    {"discount":10,"type":"percent","desc":"10% off first order","min":200},
            "FLAT50":       {"discount":50,"type":"flat","desc":"₹50 off above ₹300","min":300},
            "BIRYANI20":    {"discount":20,"type":"percent","desc":"20% off Biryani","min":280},
            "THENMANAN":    {"discount":100,"type":"flat","desc":"₹100 off above ₹500","min":500},
            "FREEDELIVERY": {"discount":40,"type":"delivery","desc":"Free delivery","min":200},
        },
        "reviews": {
            "general": [
                {"name":"Ravi K","rating":5,"cat":"Delivery","date":"Yesterday","text":"Ordered at 8pm, arrived at 8:42pm still hot! Packaging excellent 🚀"},
                {"name":"Priya S","rating":5,"cat":"Taste","date":"2 days ago","text":"Authentic Chennai flavours! Reminds me of home cooking 🏠"},
                {"name":"Sundar V","rating":5,"cat":"Quality","date":"3 days ago","text":"Consistent quality every time. Family's favourite restaurant! ⭐⭐⭐⭐⭐"},
                {"name":"Meena R","rating":5,"cat":"Value","date":"5 days ago","text":"Great value for money! Portions generous, quality top notch 💰"},
            ],
            "dishes": {
                "Chicken Biryani": [
                    {"name":"Arjun M","rating":5,"date":"2 days ago","text":"Best biryani in Chennai! Delivered hot within 40 mins 🔥","verified":True},
                    {"name":"Kavitha T","rating":5,"date":"1 week ago","text":"Ordered for office lunch. Everyone loved it! ⭐","verified":True},
                ],
                "Idiyappam + Paya": [
                    {"name":"Senthil K","rating":5,"date":"Today","text":"Drive 20km every Sunday for this! Legendary broth 🙏","verified":True},
                ],
            }
        }
    },

    # ── Restaurant 2 — HelloFoodie ─────────────────────────────────────────
    "whatsapp:+919876543210": {
        "id": "R002",
        "name": "HelloFoodie Restaurant",
        "tagline": "Modern Flavours, Traditional Heart",
        "location": "14/2, 4th Avenue, Anna Nagar, Chennai 600 040",
        "phone": "+91 98765 43210",
        "hours": "10:00 AM – 11:00 PM",
        "breakfast": "8:00 AM – 11:00 AM",
        "gpay": "hellofoodie@okicici",
        "phonepe": "hellofoodie@ybl",
        "upi": "hellofoodie@upi",
        "card_link": "https://rzp.io/l/hellofoodie",
        "delivery_km": 6,
        "delivery_mins": 40,
        "delivery_charge": 35,
        "min_order": 200,
        "rating": 4.6,
        "reviews_count": "860",
        "established": "2018",
        "cuisine": "Multi-Cuisine",
        "subscription": "active",
        "plan": "starter",
        "plan_expiry": "2026-06-01",
        "menu": {
            "🍕 Italian": {
                "Margherita Pizza":  {"price":299,"rating":4.7,"orders":980,"spice":"Mild","time":"20 mins"},
                "Pepperoni Pizza":   {"price":349,"rating":4.8,"orders":1200,"spice":"Medium","time":"20 mins"},
                "Pasta Arrabbiata": {"price":249,"rating":4.6,"orders":740,"spice":"Medium-Hot","time":"15 mins"},
            },
            "🍔 American": {
                "Chicken Burger":    {"price":199,"rating":4.7,"orders":1400,"spice":"Medium","time":"12 mins"},
                "Veg Burger":        {"price":149,"rating":4.5,"orders":840,"spice":"Mild","time":"10 mins"},
                "French Fries":      {"price":99, "rating":4.6,"orders":2100,"spice":"None","time":"8 mins"},
            },
            "🍛 Indian": {
                "Butter Chicken":    {"price":280,"rating":4.8,"orders":1100,"spice":"Mild","time":"15 mins"},
                "Dal Makhani":       {"price":220,"rating":4.6,"orders":680,"spice":"Mild","time":"15 mins"},
                "Chicken Biryani":   {"price":260,"rating":4.7,"orders":1800,"spice":"Medium","time":"20 mins"},
            },
            "🥤 Drinks": {
                "Cold Coffee":       {"price":99, "rating":4.7,"orders":1600,"spice":"None","time":"5 mins"},
                "Fresh Juice":       {"price":80, "rating":4.5,"orders":980,"spice":"None","time":"5 mins"},
                "Milkshake":         {"price":120,"rating":4.6,"orders":760,"spice":"None","time":"5 mins"},
            },
        },
        "offers": {
            "HELLO20":      {"discount":20,"type":"percent","desc":"20% off first order","min":300},
            "FLAT100":      {"discount":100,"type":"flat","desc":"₹100 off above ₹500","min":500},
            "FREEDELIVERY": {"discount":35,"type":"delivery","desc":"Free delivery","min":300},
        },
        "reviews": {
            "general": [
                {"name":"Anand P","rating":5,"cat":"Taste","date":"Yesterday","text":"Amazing pizza! Best in Anna Nagar 🍕"},
                {"name":"Divya R","rating":4,"cat":"Delivery","date":"2 days ago","text":"Fast delivery, food arrived hot and fresh! 🚀"},
            ],
            "dishes": {}
        }
    },
}

# ════════════════════════════════════════════════════════════════════════════
# SUBSCRIPTION PLANS
# ════════════════════════════════════════════════════════════════════════════
PLANS = {
    "starter": {
        "name": "Starter",
        "price": 2999,
        "features": ["WhatsApp Bot", "Menu Display", "Basic Orders", "1 Payment Method", "Email Support"],
        "max_items": 20,
        "max_offers": 2,
        "ai_replies": False,
    },
    "pro": {
        "name": "Pro",
        "price": 4999,
        "features": ["Everything in Starter", "AI Smart Replies", "All Payment Methods", "Coupon System", "Reviews & Ratings", "Table Booking", "Priority Support"],
        "max_items": 100,
        "max_offers": 10,
        "ai_replies": True,
    },
    "enterprise": {
        "name": "Enterprise",
        "price": 9999,
        "features": ["Everything in Pro", "Multiple Locations", "Custom Bot Name", "Analytics Dashboard", "Dedicated Manager", "White Label"],
        "max_items": 999,
        "max_offers": 999,
        "ai_replies": True,
    },
}

# ════════════════════════════════════════════════════════════════════════════
# SESSION STORAGE
# ════════════════════════════════════════════════════════════════════════════
sessions       = {}
active_orders  = {}
pending_reviews = {}

# ════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════
def get_restaurant(sender):
    return RESTAURANTS.get(sender)

def is_subscription_active(r):
    if r.get("subscription") != "active":
        return False
    expiry = r.get("plan_expiry","2020-01-01")
    return datetime.strptime(expiry, "%Y-%m-%d") >= datetime.now()

def get_stars(rating):
    return "⭐" * int(rating)

def gen_order_id(rid):
    return f"{rid}-{datetime.now().strftime('%d%m%H%M')}{random.randint(10,99)}"

def find_item(r, name):
    name_l = name.lower()
    for cat, items in r["menu"].items():
        for item, d in items.items():
            if name_l in item.lower() or item.lower() in name_l:
                return item, d
    return None, None

def apply_coupon(r, code, subtotal):
    code = code.upper().strip()
    offers = r.get("offers", {})
    if code not in offers:
        return None, "❌ Invalid coupon. Type *offers* to see valid codes."
    o = offers[code]
    if subtotal < o["min"]:
        return None, f"❌ Min order ₹{o['min']} needed. Your total: ₹{subtotal}."
    if o["type"] == "percent":
        disc = int(subtotal * o["discount"] / 100)
        return disc, f"✅ *{code}* applied! {o['discount']}% off = ₹{disc} saved 🎉"
    if o["type"] == "flat":
        return o["discount"], f"✅ *{code}* applied! ₹{o['discount']} flat off 🎉"
    if o["type"] == "delivery":
        return r["delivery_charge"], f"✅ *{code}* applied! Free delivery 🎉"
    return None, "❌ Invalid coupon."

# ════════════════════════════════════════════════════════════════════════════
# MENU BUILDER
# ════════════════════════════════════════════════════════════════════════════
def build_menu(r):
    t  = f"🍽️ *{r['name']} — Menu*\n"
    t += f"⭐ {r['rating']}/5 ({r['reviews_count']} reviews)\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for cat, items in r["menu"].items():
        t += f"*{cat}*\n"
        for item, d in items.items():
            t += f"  • {item} — ₹{d['price']} {get_stars(d['rating'])}\n"
        t += "\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    t += "💰 Type *offers* for today's deals!\n"
    t += f"📍 {r['location']}\n"
    return t

def build_offers(r):
    t  = "🎉 *Today's Special Offers*\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for code, o in r.get("offers", {}).items():
        t += f"🏷️ *{code}*\n   {o['desc']}\n   Min order: ₹{o['min']}\n\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    t += "Apply coupon when ordering!\nType *order* to start 🛒"
    return t

def build_payment_msg(r, order_id, subtotal, discount, coupon_type, name):
    delivery = 0 if coupon_type == "delivery" else r["delivery_charge"]
    total = subtotal - discount + delivery

    t  = f"✅ *Order Summary*\n"
    t += f"Order ID: *{order_id}*\n"
    t += f"Customer: {name}\n\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    t += f"📦 Subtotal:    ₹{subtotal}\n"
    if discount > 0:
        t += f"🎉 Discount:   -₹{discount}\n"
    t += f"🛵 Delivery:    ₹{delivery}\n"
    t += f"💰 *Total:      ₹{total}*\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    t += "*Choose Payment Method:*\n\n"
    t += f"1️⃣ *Google Pay*\n"
    t += f"   Send ₹{total} to: `{r['gpay']}`\n\n"
    t += f"2️⃣ *PhonePe*\n"
    t += f"   Send ₹{total} to: `{r['phonepe']}`\n\n"
    t += f"3️⃣ *Paytm / Any UPI*\n"
    t += f"   UPI ID: `{r['upi']}`\n\n"
    t += f"4️⃣ *Credit / Debit Card*\n"
    t += f"   Pay here 👉 {r['card_link']}\n\n"
    t += f"5️⃣ *Cash on Delivery*\n"
    t += f"   Pay ₹{total} to delivery person 💵\n\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    t += "📸 After UPI/Card payment:\nShare screenshot to confirm! ✅\n\n"
    t += f"⏱️ Estimated delivery: {r['delivery_mins']} mins\n"
    t += f"📞 Help: {r['phone']}"
    return t, total

# ════════════════════════════════════════════════════════════════════════════
# REVIEWS
# ════════════════════════════════════════════════════════════════════════════
def build_general_reviews(r, category=None):
    rev_list = r["reviews"]["general"]
    if category:
        rev_list = [x for x in rev_list if category.lower() in x["cat"].lower()] or rev_list[:3]
    else:
        rev_list = random.sample(rev_list, min(3, len(rev_list)))

    t  = f"⭐ *{r['name']} — Reviews*\n"
    t += f"Rating: {r['rating']}/5 ({r['reviews_count']} reviews)\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for rev in rev_list:
        t += f"{get_stars(rev['rating'])} *{rev['name']}* — _{rev['cat']}_\n"
        t += f"_{rev['date']}_\n{rev['text']}\n\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    t += "• *reviews delivery* — Delivery\n"
    t += "• *reviews taste* — Taste\n"
    t += "• *review [dish]* — Dish review\n"
    t += "• *add review* — Share yours 📝\n"
    return t

def build_dish_review(r, dish_name):
    actual, details = find_item(r, dish_name)
    if not actual:
        return None
    dish_reviews = r["reviews"]["dishes"].get(actual, [])
    t  = f"📊 *{actual} — Details*\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    t += f"💰 Price: ₹{details['price']}\n"
    t += f"⭐ Rating: {details['rating']}/5\n"
    t += f"📦 {details['orders']:,}+ orders\n"
    t += f"🌶️ Spice: {details['spice']}\n"
    t += f"⏱️ Prep: {details['time']}\n\n"
    if dish_reviews:
        t += "*Customer Reviews:*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        for rev in dish_reviews[:2]:
            v = "✅ Verified" if rev.get("verified") else ""
            t += f"\n{get_stars(rev['rating'])} *{rev['name']}* {v}\n"
            t += f"_{rev['date']}_\n{rev['text']}\n"
    else:
        t += "⭐ Be the first to review!\n"
    t += f"\n━━━━━━━━━━━━━━━━━━━━━━\n"
    t += f"Type *order {actual}* to add to cart 🛒"
    return t

def handle_add_review(r, sender, text):
    if sender not in pending_reviews:
        pending_reviews[sender] = {"step": "dish"}
        return "📝 *Share Your Review*\n\nWhich dish would you like to review?\n(Type dish name or *overall*)"
    step = pending_reviews[sender]["step"]
    if step == "dish":
        pending_reviews[sender]["dish"] = text
        pending_reviews[sender]["step"] = "rating"
        return f"Reviewing: *{text}*\n\nRate 1-5:\n1️⃣ Poor  2️⃣ Below Avg  3️⃣ Good\n4️⃣ Very Good  5️⃣ Excellent ⭐"
    if step == "rating":
        try:
            rating = int(text.strip())
            if 1 <= rating <= 5:
                pending_reviews[sender]["rating"] = rating
                pending_reviews[sender]["step"] = "review"
                return f"Rated: {get_stars(rating)} ({rating}/5)\n\nShare your experience in a few words 🙏"
        except:
            pass
        return "Please reply with 1-5 ⭐"
    if step == "review":
        dish   = pending_reviews[sender].get("dish", "Overall")
        rating = pending_reviews[sender].get("rating", 5)
        del pending_reviews[sender]
        return f"""✅ *Thank You for Your Review!*

*{dish}* — {get_stars(rating)} ({rating}/5)
_{text}_

Your feedback helps other customers! 🙏
🎁 *Show this for a FREE Masala Chai on next visit!* ☕

— Team {r['name']} ❤️"""
    del pending_reviews[sender]
    return "Thank you! 🙏"

# ════════════════════════════════════════════════════════════════════════════
# GPT — AI SMART REPLY (Pro plan only)
# ════════════════════════════════════════════════════════════════════════════
def ask_gpt(r, sender, text):
    if not OPENAI_KEY:
        return f"Please call us: {r['phone']} 📞"

    sessions.setdefault(sender, [])
    sessions[sender].append({"role":"user","content":text})
    if len(sessions[sender]) > 20:
        sessions[sender] = sessions[sender][-20:]

    menu_str   = ", ".join([f"{item} Rs{d['price']}" for cat, items in r["menu"].items() for item, d in items.items()])
    offers_str = ", ".join([f"{code}: {o['desc']}" for code, o in r.get("offers",{}).items()])

    system = f"""You are a friendly WhatsApp ordering assistant for {r['name']}, {r['cuisine']} restaurant in Chennai.

MENU: {menu_str}
OFFERS: {offers_str}
PAYMENT: GPay {r['gpay']} | PhonePe {r['phonepe']} | UPI {r['upi']} | Card {r['card_link']} | COD available
DELIVERY: {r['delivery_mins']} mins | ₹{r['delivery_charge']} charge | Min order ₹{r['min_order']}
HOURS: {r['hours']} | PHONE: {r['phone']}

ORDERING STEPS:
1. Confirm items + calculate total
2. Ask for coupon code (mention 'offers' command)
3. Ask name + delivery address
4. Show final bill with discount
5. Show all payment options with amounts
6. Confirm after screenshot or COD selection

RULES: Be friendly, use emojis, reply in customer language (Tamil/English), suggest best-selling dishes, always mention active offers."""

    headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
    body = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role":"system","content":system}] + sessions[sender],
        "max_tokens": 500,
        "temperature": 0.7
    }
    try:
        resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body, timeout=30)
        if resp.status_code == 200:
            reply = resp.json()["choices"][0]["message"]["content"]
            sessions[sender].append({"role":"assistant","content":reply})
            return reply
    except Exception as e:
        print(f"GPT error: {e}")
    return f"Sorry, please call {r['phone']} 🙏"

# ════════════════════════════════════════════════════════════════════════════
# MESSAGE HANDLER
# ════════════════════════════════════════════════════════════════════════════
def handle_message(r, sender, text):
    t = text.lower().strip()

    # Ongoing review
    if sender in pending_reviews:
        return handle_add_review(r, sender, text)

    # Coupon step
    if sender in active_orders and active_orders[sender].get("step") == "coupon":
        order = active_orders[sender]
        if t in ["skip","no","none"]:
            active_orders[sender]["step"]      = "payment"
            active_orders[sender]["discount"]  = 0
            active_orders[sender]["coup_type"] = None
            oid = gen_order_id(r["id"])
            active_orders[sender]["oid"]       = oid
            msg, total = build_payment_msg(r, oid, order["subtotal"], 0, None, order.get("name","Customer"))
            active_orders[sender]["total"]     = total
            return msg
        disc, msg = apply_coupon(r, text, order["subtotal"])
        if disc is not None:
            o = r.get("offers",{}).get(text.upper(),{})
            active_orders[sender].update({"discount":disc,"coup_type":o.get("type"),"step":"payment"})
            oid = gen_order_id(r["id"])
            active_orders[sender]["oid"] = oid
            pay_msg, total = build_payment_msg(r, oid, order["subtotal"], disc, o.get("type"), order.get("name","Customer"))
            active_orders[sender]["total"] = total
            return f"{msg}\n\n{pay_msg}"
        return f"{msg}\n\nType coupon or *skip* to continue."

    # Payment confirmation step
    if sender in active_orders and active_orders[sender].get("step") == "payment":
        order = active_orders[sender]
        oid   = order.get("oid", gen_order_id(r["id"]))
        total = order.get("total","?")
        name  = order.get("name","Customer")

        if any(x in t for x in ["cod","cash","5","cash on delivery"]):
            del active_orders[sender]
            return f"""✅ *Order Confirmed — Cash on Delivery!*
Order ID: *{oid}*
Amount: ₹{total}
Name: {name}

💵 Keep exact change ready.
🛵 Delivery in {r['delivery_mins']} mins.
📞 We'll call before delivery: {r['phone']} ❤️"""

        if any(x in t for x in ["paid","done","sent","transferred","screenshot","payment"]):
            del active_orders[sender]
            return f"""✅ *Payment Received — Order Confirmed!*
Order ID: *{oid}*
Amount: ₹{total}
Name: {name}

🎉 Preparing your order now!
🛵 Delivery in {r['delivery_mins']} mins.
Enjoy your meal! 🍛❤️
📞 {r['phone']}"""

    # ── COMMANDS ────────────────────────────────────────────────────────────
    if t in ["hi","hello","hey","hii","start","hai","vanakkam","வணக்கம்"]:
        plan = r.get("plan","starter").upper()
        return f"""👋 *Welcome to {r['name']}!*
_{r['tagline']}_
⭐ {r['rating']}/5 ({r['reviews_count']} reviews)

How can I help you?

🍽️ *1* — Full Menu
🏆 *2* — Top Rated Dishes
🔥 *3* — Bestsellers
📦 *4* — Place Order
🎉 *5* — Today's Offers
📅 *6* — Book a Table
⭐ *7* — Customer Reviews
📍 *8* — Location & Hours
💳 *9* — Payment Methods

_Serving {r['cuisine']} since {r['established']}_ 🌟"""

    if t in ["1","menu","show menu","full menu"]:
        return build_menu(r)

    if t in ["2","top rated","best dishes"]:
        items = [(item,d) for cat,its in r["menu"].items() for item,d in its.items()]
        top   = sorted(items, key=lambda x: (x[1]['rating'],x[1]['orders']), reverse=True)[:8]
        txt   = "🏆 *Top Rated Dishes*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i,(item,d) in enumerate(top,1):
            txt += f"{i}. *{item}* — ₹{d['price']}\n   {get_stars(d['rating'])} {d['rating']}/5 | {d['orders']:,}+ orders\n\n"
        return txt

    if t in ["3","bestsellers","popular","most ordered"]:
        items = [(item,d) for cat,its in r["menu"].items() for item,d in its.items()]
        top   = sorted(items, key=lambda x: x[1]['orders'], reverse=True)[:5]
        txt   = "🔥 *Our Bestsellers*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for item,d in top:
            txt += f"⭐ *{item}* — ₹{d['price']}\n   {d['orders']:,}+ orders | {d['rating']}/5\n\n"
        return txt

    if t in ["4","order","place order","i want to order","order food"]:
        return f"""🛒 *Place Your Order at {r['name']}*

Tell me what you'd like! Example:
_"1 Chicken Biryani and 2 Samosa"_

💰 Type *offers* to see today's deals first!
Min order: ₹{r['min_order']}
🛵 Delivery in {r['delivery_mins']} mins"""

    if t in ["5","offers","coupon","deals","discount","promo"]:
        return build_offers(r)

    if t in ["6","book table","reservation","book a table","reserve"]:
        return f"""📅 *Book a Table at {r['name']}*

Please share:
1️⃣ Your *Name*
2️⃣ *Date* (e.g. 5 May 2026)
3️⃣ *Time* (e.g. 7:30 PM)
4️⃣ *Number of guests*
5️⃣ *Occasion*? (Birthday/Anniversary etc)

Confirmed within 15 mins! 🎉
Large groups: {r['phone']}"""

    if t in ["7","reviews","review","feedback","ratings"]:
        return build_general_reviews(r)

    if t in ["8","location","address","where","hours","timing"]:
        return f"""📍 *Find {r['name']}*

🏠 {r['location']}
🕐 {r['hours']}
🌅 Breakfast: {r['breakfast']}
🛵 Delivery within {r['delivery_km']}km | {r['delivery_mins']} mins
Min order: ₹{r['min_order']}
📞 {r['phone']}"""

    if t in ["9","payment","pay","how to pay","upi"]:
        return f"""💳 *Payment Methods*

1️⃣ *Google Pay*
   `{r['gpay']}`

2️⃣ *PhonePe*
   `{r['phonepe']}`

3️⃣ *Paytm / Any UPI*
   `{r['upi']}`

4️⃣ *Credit / Debit Card*
   {r['card_link']}

5️⃣ *Cash on Delivery*
   Pay at your door 💵

📸 After UPI payment share screenshot here!"""

    if t.startswith("reviews "):
        return build_general_reviews(r, t.replace("reviews ","").strip())

    if t.startswith("review "):
        result = build_dish_review(r, text[7:].strip())
        return result or ask_gpt(r, sender, text)

    if any(x in t for x in ["add review","write review","give review","leave review"]):
        return handle_add_review(r, sender, text)

    # Dish lookup
    actual, details = find_item(r, text)
    if actual and len(text) > 3:
        result = build_dish_review(r, text)
        if result:
            return result

    if any(x in t for x in ["veg","vegetarian","no meat"]):
        veg = [f"• {item} — ₹{d['price']}" for cat,its in r["menu"].items() for item,d in its.items() if d['spice'] in ['Mild','None']]
        return "🥬 *Mild / Vegetarian Options*\n\n" + "\n".join(veg[:8]) + "\n\n_All veg dishes prepared separately!_ 🙏"

    if any(x in t for x in ["spicy","hot","mild","not spicy"]):
        mild = [f"• {item} (₹{d['price']})" for cat,its in r["menu"].items() for item,d in its.items() if d['spice'] in ['Mild','None']]
        hot  = [f"• {item} (₹{d['price']})" for cat,its in r["menu"].items() for item,d in its.items() if d['spice'] in ['Hot','Medium-Hot']]
        return "🌶️ *By Spice Level*\n\n*Mild:*\n" + "\n".join(mild[:5]) + "\n\n*Hot:*\n" + "\n".join(hot[:5])

    if any(x in t for x in ["track","my order","order status"]):
        return f"📦 Share your *Order ID* or call us:\n📞 {r['phone']}\n🛵 Delivery: {r['delivery_mins']} mins"

    # Order keywords — let GPT handle and trigger payment flow
    order_kw = ["order","want","give me","send","1 ","2 ","3 ","biryani","chicken","mutton","pizza","burger"]
    if any(x in t for x in order_kw):
        plan = r.get("plan","starter")
        if PLANS[plan]["ai_replies"] and OPENAI_KEY:
            reply = ask_gpt(r, sender, text)
            # Auto trigger coupon step if total detected in reply
            if "₹" in reply and ("total" in reply.lower() or "subtotal" in reply.lower()):
                subtotal = 0
                for cat, items in r["menu"].items():
                    for item, d in items.items():
                        if item.lower() in t:
                            subtotal += d["price"]
                if subtotal >= r["min_order"]:
                    active_orders[sender] = {"subtotal": subtotal, "step": "coupon"}
                    return reply + "\n\n🎉 *Do you have a coupon code?*\nType code or *skip*\n_(Type *offers* to see deals)_"
            return reply
        else:
            return f"""🛒 To place your order please call:\n📞 {r['phone']}\n\nOr type *menu* to see our full menu!\n\n_Upgrade to Pro plan for AI ordering 🤖_"""

    # Pro plan — GPT for everything else
    plan = r.get("plan","starter")
    if PLANS[plan]["ai_replies"] and OPENAI_KEY:
        return ask_gpt(r, sender, text)

    return f"Type *menu* to see our menu or call {r['phone']} 📞"

# ════════════════════════════════════════════════════════════════════════════
# ADMIN — SUBSCRIPTION MANAGEMENT API
# ════════════════════════════════════════════════════════════════════════════
@app.route("/admin/restaurants", methods=["GET"])
def list_restaurants():
    key = request.args.get("key","")
    if key != MASTER_KEY:
        return jsonify({"error":"Unauthorized"}), 401
    summary = []
    for sender, r in RESTAURANTS.items():
        summary.append({
            "id":       r["id"],
            "name":     r["name"],
            "plan":     r.get("plan"),
            "status":   r.get("subscription"),
            "expiry":   r.get("plan_expiry"),
            "active":   is_subscription_active(r),
            "sender":   sender,
        })
    return jsonify({"restaurants": summary, "total": len(summary)})

@app.route("/admin/plans", methods=["GET"])
def show_plans():
    return jsonify(PLANS)

@app.route("/admin/stats", methods=["GET"])
def stats():
    key = request.args.get("key","")
    if key != MASTER_KEY:
        return jsonify({"error":"Unauthorized"}), 401
    active    = sum(1 for r in RESTAURANTS.values() if is_subscription_active(r))
    mrr_total = sum(PLANS[r.get("plan","starter")]["price"] for r in RESTAURANTS.values() if is_subscription_active(r))
    return jsonify({
        "total_restaurants": len(RESTAURANTS),
        "active_subscriptions": active,
        "monthly_revenue": f"₹{mrr_total:,}",
        "annual_revenue": f"₹{mrr_total*12:,}",
    })

# ════════════════════════════════════════════════════════════════════════════
# WHATSAPP WEBHOOK
# ════════════════════════════════════════════════════════════════════════════
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    sender = request.form.get("From","")
    text   = request.form.get("Body","").strip()
    media  = int(request.form.get("NumMedia","0"))
    print(f"From: {sender} | Msg: {text[:60]} | Media: {media}")

    resp = MessagingResponse()

    # Get restaurant
    r = get_restaurant(sender)

    # ── New restaurant not in system ──────────────────────────────────────
    if not r:
        resp.message(
            "👋 Hello! This number is not registered with our system.\n\n"
            "Are you a *restaurant owner* looking to set up WhatsApp ordering?\n\n"
            "Contact NexoraAI:\n"
            "📞 +91 7010624989\n"
            "🌐 nexoraai.netlify.app\n\n"
            "Plans start at ₹2,999/month! 🚀"
        )
        return str(resp)

    # ── Subscription expired ──────────────────────────────────────────────
    if not is_subscription_active(r):
        resp.message(
            f"⚠️ *{r['name']}* subscription has expired.\n\n"
            f"Please renew to continue using the WhatsApp bot.\n\n"
            f"Contact NexoraAI:\n"
            f"📞 +91 7010624989\n"
            f"🌐 nexoraai.netlify.app"
        )
        return str(resp)

    # ── Payment screenshot received ───────────────────────────────────────
    if media > 0 and sender in active_orders:
        order = active_orders[sender]
        oid   = order.get("oid", gen_order_id(r["id"]))
        del active_orders[sender]
        resp.message(
            f"✅ *Payment Screenshot Received!*\n"
            f"Order ID: *{oid}*\n"
            f"Amount: ₹{order.get('total','')}\n\n"
            f"🎉 Order confirmed! Preparing now...\n"
            f"🛵 Delivery in {r['delivery_mins']} mins\n"
            f"Enjoy your meal! 🍛❤️\n"
            f"📞 {r['phone']}"
        )
        return str(resp)

    # ── Normal message ────────────────────────────────────────────────────
    try:
        reply = handle_message(r, sender, text)
    except Exception as e:
        print(f"Error: {e}")
        reply = f"Sorry, please call {r['phone']} 🙏"

    resp.message(reply)
    return str(resp)

# ════════════════════════════════════════════════════════════════════════════
# HOME
# ════════════════════════════════════════════════════════════════════════════
@app.route("/")
def home():
    active = sum(1 for r in RESTAURANTS.values() if is_subscription_active(r))
    mrr    = sum(PLANS[r.get("plan","starter")]["price"] for r in RESTAURANTS.values() if is_subscription_active(r))
    return f"""
    <h2>🤖 NexoraAI Restaurant WhatsApp Platform</h2>
    <p>✅ Platform is Live!</p>
    <hr>
    <p>🍽️ Restaurants on platform: <b>{len(RESTAURANTS)}</b></p>
    <p>✅ Active subscriptions: <b>{active}</b></p>
    <p>💰 Monthly Revenue: <b>₹{mrr:,}</b></p>
    <hr>
    <p>📞 NexoraAI: +91 7010624989</p>
    <p>🌐 nexoraai.netlify.app</p>
    """, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=False)
