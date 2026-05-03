from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
import json
from datetime import datetime
import random

app = Flask(__name__)

OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

# ── Restaurant Configuration ──────────────────────────────────────────────────
RESTAURANT = {
    "name": "Thenmanan Restaurant",
    "location": "23/7, Usman Road, T Nagar, Chennai 600 017",
    "phone": "+91 90000 11223",
    "hours": "11:00 AM to 11:00 PM (Daily)",
    "breakfast": "7:30 AM to 11:00 AM",
    "upi": "thenmanan@upi",
    "delivery_radius": "5 km",
    "delivery_time": "45 minutes",
    "min_order": 150,
    "rating": "4.8",
    "total_reviews": "1,240",
    "established": "1990"
}

# ── Full Menu ─────────────────────────────────────────────────────────────────
MENU = {
    "🍗 Biryani": {
        "Chicken Biryani": {"price": 280, "rating": 4.9, "orders": 2840, "spice": "Medium", "time": "20 mins"},
        "Mutton Biryani": {"price": 320, "rating": 4.8, "orders": 1920, "spice": "Medium", "time": "25 mins"},
        "Prawn Biryani": {"price": 350, "rating": 4.7, "orders": 980, "spice": "Medium-Hot", "time": "25 mins"},
        "Vegetable Biryani": {"price": 180, "rating": 4.5, "orders": 640, "spice": "Mild", "time": "15 mins"},
        "Egg Biryani": {"price": 200, "rating": 4.6, "orders": 760, "spice": "Medium", "time": "15 mins"},
        "Semiya Chicken Biryani": {"price": 260, "rating": 4.8, "orders": 1100, "spice": "Medium", "time": "20 mins"},
    },
    "🥩 Non-Veg Mains": {
        "Pepper Chicken Masala": {"price": 280, "rating": 4.9, "orders": 2100, "spice": "Hot", "time": "15 mins"},
        "Chicken Butter Masala": {"price": 300, "rating": 4.7, "orders": 1400, "spice": "Mild", "time": "15 mins"},
        "Mutton Kulambu": {"price": 340, "rating": 4.8, "orders": 980, "spice": "Hot", "time": "20 mins"},
        "Fish Curry": {"price": 260, "rating": 4.6, "orders": 840, "spice": "Medium-Hot", "time": "15 mins"},
        "Prawn Masala": {"price": 320, "rating": 4.7, "orders": 720, "spice": "Hot", "time": "15 mins"},
        "Chicken 65": {"price": 260, "rating": 4.8, "orders": 1680, "spice": "Hot", "time": "15 mins"},
    },
    "🥬 Veg Mains": {
        "Paneer Butter Masala": {"price": 220, "rating": 4.6, "orders": 840, "spice": "Mild", "time": "15 mins"},
        "Dal Tadka": {"price": 160, "rating": 4.5, "orders": 620, "spice": "Mild", "time": "10 mins"},
        "Mixed Veg Curry": {"price": 180, "rating": 4.4, "orders": 480, "spice": "Mild", "time": "12 mins"},
        "Palak Paneer": {"price": 200, "rating": 4.5, "orders": 560, "spice": "Mild", "time": "15 mins"},
    },
    "🫓 Breads & Rice": {
        "Tandoori Roti": {"price": 30, "rating": 4.5, "orders": 2200, "spice": "None", "time": "10 mins"},
        "Butter Naan": {"price": 40, "rating": 4.6, "orders": 1800, "spice": "None", "time": "10 mins"},
        "Parotta": {"price": 25, "rating": 4.7, "orders": 2400, "spice": "None", "time": "8 mins"},
        "Steamed Rice": {"price": 60, "rating": 4.4, "orders": 1600, "spice": "None", "time": "10 mins"},
        "Ghee Rice": {"price": 80, "rating": 4.6, "orders": 980, "spice": "None", "time": "12 mins"},
    },
    "🥟 Starters": {
        "Chicken Samosa (2pcs)": {"price": 80, "rating": 4.8, "orders": 2100, "spice": "Medium", "time": "10 mins"},
        "Mutton Samosa (2pcs)": {"price": 90, "rating": 4.7, "orders": 1400, "spice": "Medium", "time": "10 mins"},
        "Chicken 65 Starter": {"price": 220, "rating": 4.8, "orders": 1800, "spice": "Hot", "time": "12 mins"},
        "Fish Fry": {"price": 240, "rating": 4.9, "orders": 1600, "spice": "Medium-Hot", "time": "15 mins"},
        "Prawn Fry": {"price": 280, "rating": 4.7, "orders": 920, "spice": "Medium", "time": "15 mins"},
        "Vegetable Soup": {"price": 120, "rating": 4.4, "orders": 480, "spice": "Mild", "time": "10 mins"},
    },
    "🍦 Desserts & Drinks": {
        "Special Falooda": {"price": 120, "rating": 4.9, "orders": 1840, "spice": "None", "time": "5 mins"},
        "Gulab Jamun": {"price": 80, "rating": 4.7, "orders": 1200, "spice": "None", "time": "5 mins"},
        "Ice Cream": {"price": 100, "rating": 4.6, "orders": 960, "spice": "None", "time": "3 mins"},
        "Fresh Lime Soda": {"price": 60, "rating": 4.6, "orders": 1400, "spice": "None", "time": "3 mins"},
        "Mango Lassi": {"price": 80, "rating": 4.7, "orders": 1100, "spice": "None", "time": "5 mins"},
        "Masala Chai": {"price": 40, "rating": 4.5, "orders": 1800, "spice": "None", "time": "3 mins"},
    },
    "🌅 Breakfast (7:30AM-11AM)": {
        "Idiyappam + Paya": {"price": 180, "rating": 4.9, "orders": 2400, "spice": "Medium", "time": "10 mins"},
        "Idly (4pcs) + Sambar": {"price": 80, "rating": 4.7, "orders": 1800, "spice": "Mild", "time": "8 mins"},
        "Dosa + Chutney": {"price": 90, "rating": 4.8, "orders": 2100, "spice": "Mild", "time": "8 mins"},
        "Puri + Masala": {"price": 100, "rating": 4.6, "orders": 1400, "spice": "Mild", "time": "10 mins"},
        "Upma": {"price": 70, "rating": 4.5, "orders": 980, "spice": "Mild", "time": "8 mins"},
    }
}

# ── Customer Reviews Database ─────────────────────────────────────────────────
REVIEWS = {
    "Chicken Biryani": [
        {"name": "Ravi K", "rating": 5, "date": "2 days ago", "review": "Best biryani in Chennai! The aroma is incredible and mutton is so tender. Delivered hot within 40 minutes. Will order again! 🔥", "verified": True},
        {"name": "Priya S", "rating": 5, "date": "1 week ago", "review": "Ordered for office lunch. Everyone loved it! The spice level is perfect. Packaging was also neat. Highly recommend! ⭐", "verified": True},
        {"name": "Arjun M", "rating": 4, "date": "2 weeks ago", "review": "Really good biryani. Portion size is generous. Delivery was on time. Definitely coming back! 👍", "verified": True},
    ],
    "Mutton Biryani": [
        {"name": "Sundar V", "rating": 5, "date": "3 days ago", "review": "Absolutely divine! The mutton was fall-off-the-bone tender. This is authentic Dum Biryani. Worth every rupee! 🍛", "verified": True},
        {"name": "Meena R", "rating": 5, "date": "5 days ago", "review": "Ordered for my husband's birthday. He loved it so much! The flavours are authentic and reminds me of home cooking 💕", "verified": True},
        {"name": "Kumar T", "rating": 4, "date": "1 week ago", "review": "Very tasty. Good quantity. Delivery was slightly delayed but food quality made up for it. Will order again!", "verified": True},
    ],
    "Fish Fry": [
        {"name": "Anand P", "rating": 5, "date": "1 day ago", "review": "Fresh fish, perfectly marinated! Crispy outside, juicy inside. Best fish fry I have had outside of home! 🐟", "verified": True},
        {"name": "Lakshmi N", "rating": 5, "date": "4 days ago", "review": "Outstanding! The spice blend is perfect. You can tell they use fresh fish. Will order every week now! 🌶️", "verified": True},
    ],
    "Idiyappam + Paya": [
        {"name": "Senthil K", "rating": 5, "date": "Today", "review": "I drive 20km every Sunday for this! The Paya broth is so rich and flavorful. Idiyappam is perfectly soft. Legendary! 🙏", "verified": True},
        {"name": "Kavitha M", "rating": 5, "date": "Yesterday", "review": "This is the real deal! Authentic Chennai breakfast. The Paya has that slow-cooked depth of flavour. Simply outstanding!", "verified": True},
    ],
    "Special Falooda": [
        {"name": "Divya R", "rating": 5, "date": "3 days ago", "review": "Best Falooda in T Nagar! The rose syrup is so fragrant and ice cream is fresh. Perfect ending to a meal! 🍦", "verified": True},
        {"name": "Raj Kumar", "rating": 5, "date": "1 week ago", "review": "My kids absolutely love the Falooda here. Always fresh, always perfect. A must-try dessert! ❤️", "verified": True},
    ],
    "Pepper Chicken Masala": [
        {"name": "Babu N", "rating": 5, "date": "2 days ago", "review": "The pepper hits you perfectly without being overwhelming. Chicken is well-cooked and gravy is thick. Pure perfection! 🌶️", "verified": True},
        {"name": "Shanthi K", "rating": 5, "date": "4 days ago", "review": "My favourite dish here! Order it every time with Parotta. The combination is unbeatable. Highly recommend! 👌", "verified": True},
    ],
}

# ── General Reviews ───────────────────────────────────────────────────────────
GENERAL_REVIEWS = [
    {"name": "Rajan M", "rating": 5, "date": "Yesterday", "category": "Delivery", "review": "Ordered at 8pm, food arrived at 8:42pm. Still piping hot! Packaging was excellent. Every dish tasted fresh. Impressed! 🚀"},
    {"name": "Anitha S", "rating": 5, "date": "2 days ago", "category": "Quality", "review": "Consistent quality every single time. Ordered 10+ times and never been disappointed. This is our family's go-to restaurant! ⭐⭐⭐⭐⭐"},
    {"name": "Krishnan V", "rating": 5, "date": "3 days ago", "category": "Taste", "review": "Authentic Chennai flavours! Takes me back to my grandmother's cooking. No artificial colours or preservatives. Pure homestyle food! 🏠"},
    {"name": "Nithya P", "rating": 4, "date": "5 days ago", "category": "Value", "review": "Great value for money! Portions are generous and quality is top notch. Better than many expensive restaurants in Chennai! 💰"},
    {"name": "Manoj K", "rating": 5, "date": "1 week ago", "category": "Service", "review": "Called to add an extra item after ordering — they accommodated immediately! Excellent customer service. Rare to find these days! 👏"},
    {"name": "Deepa R", "rating": 5, "date": "1 week ago", "category": "Packaging", "review": "Food arrived perfectly packed. Biryani and curry in separate containers. Nothing spilled. Thoughtful packaging! 📦"},
    {"name": "Suresh B", "rating": 5, "date": "2 weeks ago", "category": "Freshness", "review": "You can taste the freshness in every bite. Vegetables are crisp, meats are tender. Clearly using fresh ingredients daily! 🌿"},
    {"name": "Lakshmi T", "rating": 4, "date": "2 weeks ago", "category": "Overall", "review": "One of the best restaurants in T Nagar. Consistent taste, good delivery speed, reasonable prices. Thoroughly recommend! 🌟"},
]

# ── Order Storage ─────────────────────────────────────────────────────────────
orders = {}
sessions = {}
pending_reviews = {}

# ── Helper Functions ──────────────────────────────────────────────────────────
def get_stars(rating):
    full = int(rating)
    return "⭐" * full

def find_item(item_name):
    item_lower = item_name.lower()
    for category, items in MENU.items():
        for item, details in items.items():
            if item_lower in item.lower() or item.lower() in item_lower:
                return item, details
    return None, None

def build_menu_text():
    text = f"🍽️ *{RESTAURANT['name']} — Full Menu*\n"
    text += f"⭐ {RESTAURANT['rating']}/5 ({RESTAURANT['total_reviews']} reviews)\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for category, items in MENU.items():
        text += f"*{category}*\n"
        for item, details in items.items():
            stars = get_stars(details['rating'])
            text += f"  • {item} — ₹{details['price']} {stars}\n"
        text += "\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━\n"
    text += "_Type item name for reviews & details_\n"
    text += f"📍 {RESTAURANT['location']}\n"
    text += f"🕐 {RESTAURANT['hours']}\n"
    return text

def get_item_reviews(item_name):
    actual_name, details = find_item(item_name)
    if not actual_name:
        return None

    reviews = REVIEWS.get(actual_name, [])
    text = f"📊 *{actual_name} — Details & Reviews*\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    text += f"💰 Price: ₹{details['price']}\n"
    text += f"⭐ Rating: {details['rating']}/5\n"
    text += f"📦 Orders: {details['orders']:,}+ served\n"
    text += f"🌶️ Spice Level: {details['spice']}\n"
    text += f"⏱️ Prep Time: {details['time']}\n\n"

    if reviews:
        text += f"*Customer Reviews ({len(reviews)})*\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━\n"
        for rev in reviews[:3]:
            verified = "✅ Verified" if rev["verified"] else ""
            text += f"\n{get_stars(rev['rating'])} *{rev['name']}* {verified}\n"
            text += f"_{rev['date']}_\n"
            text += f"{rev['review']}\n"
    else:
        text += "⭐ Be the first to review this item!\n"

    text += f"\n━━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"Want to order? Reply:\n_'Order {actual_name}'_ 🛒"
    return text

def get_general_reviews(category=None):
    if category:
        filtered = [r for r in GENERAL_REVIEWS if category.lower() in r["category"].lower()]
        reviews_to_show = filtered if filtered else GENERAL_REVIEWS[:4]
    else:
        reviews_to_show = random.sample(GENERAL_REVIEWS, min(4, len(GENERAL_REVIEWS)))

    text = f"⭐ *{RESTAURANT['name']} — Customer Reviews*\n"
    text += f"Overall Rating: {RESTAURANT['rating']}/5 ({RESTAURANT['total_reviews']} reviews)\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━\n\n"

    for rev in reviews_to_show:
        text += f"{get_stars(rev['rating'])} *{rev['name']}* — _{rev['category']}_\n"
        text += f"_{rev['date']}_\n"
        text += f"{rev['review']}\n\n"

    text += "━━━━━━━━━━━━━━━━━━━━━━\n"
    text += "📝 Type:\n"
    text += "• *reviews delivery* — Delivery reviews\n"
    text += "• *reviews taste* — Taste reviews\n"
    text += "• *reviews quality* — Quality reviews\n"
    text += "• *review [dish name]* — Dish reviews\n"
    text += "• *add review* — Share your experience\n"
    return text

def get_top_dishes():
    all_items = []
    for category, items in MENU.items():
        for item, details in items.items():
            all_items.append((item, details, category))

    top = sorted(all_items, key=lambda x: (x[1]['rating'], x[1]['orders']), reverse=True)[:8]

    text = "🏆 *Top Rated Dishes*\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, (item, details, cat) in enumerate(top, 1):
        text += f"{i}. *{item}*\n"
        text += f"   {get_stars(details['rating'])} {details['rating']}/5 | ₹{details['price']} | {details['orders']:,}+ orders\n"
        text += f"   🌶️ {details['spice']} | ⏱️ {details['time']}\n\n"

    text += "_Type any dish name to see reviews & order!_"
    return text

def get_bestsellers():
    all_items = []
    for category, items in MENU.items():
        for item, details in items.items():
            all_items.append((item, details))

    bestsellers = sorted(all_items, key=lambda x: x[1]['orders'], reverse=True)[:5]

    text = "🔥 *Our Bestsellers*\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for item, details in bestsellers:
        text += f"⭐ *{item}*\n"
        text += f"   ₹{details['price']} | {details['rating']}/5 | {details['orders']:,}+ orders\n\n"

    text += "_These are our most loved dishes!_\n"
    text += "Type dish name to order or see reviews 😊"
    return text

def handle_add_review(sender, text):
    text_lower = text.lower()

    if sender not in pending_reviews:
        pending_reviews[sender] = {"step": "dish"}
        return """📝 *Share Your Review*

We'd love to hear your feedback!

Which dish would you like to review?
(Type the dish name or type *'overall'* for general feedback)"""

    step = pending_reviews[sender].get("step")

    if step == "dish":
        pending_reviews[sender]["dish"] = text
        pending_reviews[sender]["step"] = "rating"
        return f"""Thanks! Reviewing: *{text}*

Please rate your experience:
1️⃣ - Poor
2️⃣ - Below Average
3️⃣ - Good
4️⃣ - Very Good
5️⃣ - Excellent

Reply with a number (1-5) ⭐"""

    if step == "rating":
        try:
            rating = int(text.strip())
            if 1 <= rating <= 5:
                pending_reviews[sender]["rating"] = rating
                pending_reviews[sender]["step"] = "review"
                stars = get_stars(rating)
                return f"""You rated: {stars} ({rating}/5)

Now please share your experience in a few words:
(What did you like? Taste, delivery speed, packaging, freshness?)

_Your honest feedback helps other customers!_ 🙏"""
        except:
            pass
        return "Please reply with a number between 1 and 5 ⭐"

    if step == "review":
        dish = pending_reviews[sender].get("dish", "Overall")
        rating = pending_reviews[sender].get("rating", 5)
        review_text = text
        stars = get_stars(rating)

        del pending_reviews[sender]

        return f"""✅ *Thank You for Your Review!*

*{dish}* — {stars} ({rating}/5)
_{review_text}_

Your feedback has been submitted and helps other customers make better choices! 🙏

*As a token of appreciation, show this message on your next visit for a FREE Masala Chai!* ☕

— Team {RESTAURANT['name']} ❤️"""

    del pending_reviews[sender]
    return "Thank you for your feedback! 🙏"

def ask_gpt(sender, text):
    sessions.setdefault(sender, [])
    sessions[sender].append({"role": "user", "content": text})
    if len(sessions[sender]) > 20:
        sessions[sender] = sessions[sender][-20:]

    menu_str = ""
    for cat, items in MENU.items():
        for item, details in items.items():
            menu_str += f"{item}: Rs{details['price']} (rating {details['rating']}, {details['orders']} orders), "

    prompt = f"""You are a friendly WhatsApp ordering assistant for {RESTAURANT['name']} in Chennai.

FULL MENU WITH RATINGS:
{menu_str}

RESTAURANT INFO:
Location: {RESTAURANT['location']}
Hours: {RESTAURANT['hours']} | Breakfast: {RESTAURANT['breakfast']}
Phone: {RESTAURANT['phone']}
UPI: {RESTAURANT['upi']}
Delivery: Within {RESTAURANT['delivery_radius']} in {RESTAURANT['delivery_time']}
Min Order: Rs{RESTAURANT['min_order']}
Rating: {RESTAURANT['rating']}/5 ({RESTAURANT['total_reviews']} reviews)

TASKS:
- Help browse menu, place orders, book tables
- Share reviews and ratings when asked
- For orders: collect name, items, qty, address
- Show order total and UPI payment details
- Be friendly with emojis
- Reply in customer's language (Tamil/English)
- Recommend dishes based on preferences

PAYMENT: After order confirmed, say:
"Pay Rs[TOTAL] to UPI: {RESTAURANT['upi']} and share screenshot 📸"
"""

    headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
    body = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "system", "content": prompt}] + sessions[sender],
        "max_tokens": 500,
        "temperature": 0.7
    }

    r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body, timeout=30)
    if r.status_code == 200:
        reply = r.json()["choices"][0]["message"]["content"]
        sessions[sender].append({"role": "assistant", "content": reply})
        return reply
    return f"Sorry please call {RESTAURANT['phone']}"

def handle_message(sender, text):
    text_lower = text.lower().strip()

    # Handle ongoing review submission
    if sender in pending_reviews:
        return handle_add_review(sender, text)

    # Greetings
    if text_lower in ["hi", "hello", "hey", "hii", "start", "hai", "vanakkam"]:
        return f"""👋 *Welcome to {RESTAURANT['name']}!*
⭐ Rated {RESTAURANT['rating']}/5 by {RESTAURANT['total_reviews']} customers

How can I help you today?

🍽️ *1* — View Full Menu
🏆 *2* — Top Rated Dishes
🔥 *3* — Our Bestsellers
📦 *4* — Place an Order
📅 *5* — Book a Table
⭐ *6* — Customer Reviews
📍 *7* — Location & Hours
💳 *8* — Payment Info

_Serving authentic Chennai cuisine since {RESTAURANT['established']}_ 🌟"""

    # Menu
    if text_lower in ["1", "menu", "show menu", "full menu"]:
        return build_menu_text()

    # Top rated
    if text_lower in ["2", "top rated", "top dishes", "best dishes", "best food"]:
        return get_top_dishes()

    # Bestsellers
    if text_lower in ["3", "bestseller", "bestsellers", "popular", "most ordered"]:
        return get_bestsellers()

    # Order
    if text_lower in ["4", "order", "place order", "i want to order", "order food"]:
        return f"""🛒 *Place Your Order*

Tell me what you'd like! For example:
_"1 Chicken Biryani and 2 Mutton Samosa"_

Or type *menu* to browse first.

*Minimum order: ₹{RESTAURANT['min_order']}*
🛵 Delivery in {RESTAURANT['delivery_time']} within {RESTAURANT['delivery_radius']}"""

    # Table booking
    if text_lower in ["5", "book table", "book a table", "reservation", "reserve table"]:
        return f"""📅 *Book a Table*

Please share:
1️⃣ Your *Name*
2️⃣ *Date* (e.g. 4 May 2026)
3️⃣ *Time* (e.g. 7:30 PM)
4️⃣ *Number of guests*
5️⃣ *Occasion*? (Birthday/Anniversary/Business)

We'll confirm within 15 minutes! 🎉

For large groups (15+) call: {RESTAURANT['phone']}"""

    # Reviews
    if text_lower in ["6", "reviews", "review", "feedback", "ratings", "what do people say"]:
        return get_general_reviews()

    # Location
    if text_lower in ["7", "location", "address", "where", "timing", "hours", "time"]:
        return f"""📍 *Find Us*

🏠 *Address:*
{RESTAURANT['location']}

🕐 *Hours:*
Lunch & Dinner: {RESTAURANT['hours']}
Breakfast: {RESTAURANT['breakfast']}

🛵 *Delivery:*
Within {RESTAURANT['delivery_radius']} | {RESTAURANT['delivery_time']}
Min order: ₹{RESTAURANT['min_order']}

📞 *Call:* {RESTAURANT['phone']}
🗺️ Maps: https://maps.google.com/?q=T+Nagar+Chennai"""

    # Payment
    if text_lower in ["8", "payment", "pay", "upi", "gpay", "how to pay"]:
        return f"""💳 *Payment Options*

*UPI ID:* `{RESTAURANT['upi']}`

✅ Google Pay
✅ PhonePe
✅ Paytm
✅ Any UPI App
✅ Cash on Delivery

After UPI payment:
📸 Share screenshot here to confirm order!

For cash: Pay at delivery 🚪"""

    # Review by category
    if text_lower.startswith("reviews "):
        category = text_lower.replace("reviews ", "").strip()
        return get_general_reviews(category)

    # Review specific dish
    if text_lower.startswith("review "):
        dish = text[7:].strip()
        result = get_item_reviews(dish)
        if result:
            return result
        return ask_gpt(sender, text)

    # Add review
    if any(x in text_lower for x in ["add review", "write review", "give review", "leave review", "my review"]):
        return handle_add_review(sender, text)

    # Check specific dish details
    actual_name, details = find_item(text)
    if actual_name and len(text) > 3:
        result = get_item_reviews(text)
        if result:
            return result

    # Spice level queries
    if any(x in text_lower for x in ["spicy", "spice", "mild", "hot dish", "not spicy"]):
        mild_items = []
        hot_items = []
        for cat, items in MENU.items():
            for item, details in items.items():
                if details['spice'] in ['Mild', 'None']:
                    mild_items.append(f"{item} (₹{details['price']})")
                elif details['spice'] in ['Hot', 'Medium-Hot']:
                    hot_items.append(f"{item} (₹{details['price']})")

        text_reply = "🌶️ *Dishes by Spice Level*\n\n"
        text_reply += "*Mild/Non-Spicy:*\n"
        for item in mild_items[:6]:
            text_reply += f"• {item}\n"
        text_reply += "\n*Medium-Hot/Hot:*\n"
        for item in hot_items[:6]:
            text_reply += f"• {item}\n"
        return text_reply

    # Vegetarian queries
    if any(x in text_lower for x in ["veg", "vegetarian", "no meat", "veg items"]):
        veg_items = []
        for item, details in MENU.get("🥬 Veg Mains", {}).items():
            veg_items.append(f"• {item} — ₹{details['price']} {get_stars(details['rating'])}")
        for item, details in MENU.get("🫓 Breads & Rice", {}).items():
            veg_items.append(f"• {item} — ₹{details['price']}")

        text_reply = "🥬 *Vegetarian Options*\n\n"
        for item in veg_items:
            text_reply += item + "\n"
        text_reply += "\n_All veg dishes prepared separately!_ 🙏"
        return text_reply

    # Track order
    if any(x in text_lower for x in ["track", "my order", "order status", "where is"]):
        return f"""📦 *Track Your Order*

Share your *order number* or *phone number*.

For urgent help:
📞 Call: {RESTAURANT['phone']}

Estimated delivery: {RESTAURANT['delivery_time']} 🛵"""

    # Use GPT for everything else
    return ask_gpt(sender, text)

# ── Flask Routes ──────────────────────────────────────────────────────────────
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    sender = request.form.get("From", "")
    text = request.form.get("Body", "").strip()
    print(f"\n{'='*50}")
    print(f"From: {sender} | Message: {text}")

    try:
        reply = handle_message(sender, text)
    except Exception as e:
        print(f"Error: {e}")
        reply = f"Sorry, please call {RESTAURANT['phone']} 🙏"

    print(f"Reply sent ({len(reply)} chars)")
    resp = MessagingResponse()
    resp.message(reply)
    return str(resp)

@app.route("/")
def home():
    return f"<h2>✅ {RESTAURANT['name']} WhatsApp Bot is Live!</h2>", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
