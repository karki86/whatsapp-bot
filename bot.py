from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import requests, os, random, json
from datetime import datetime

app = Flask(__name__)
OPENAI_KEY  = os.environ.get("OPENAI_API_KEY")
MASTER_KEY  = os.environ.get("MASTER_KEY", "NEXORAAI2026")

# ════════════════════════════════════════════════════════════════════════════
#  PLATFORM PAYMENT DETAILS (NexoraAI collects — pays restaurant later)
# ════════════════════════════════════════════════════════════════════════════
PLATFORM = {
    "name":       "FoodieBot",
    "company":    "NexoraAI",
    "upi":        os.environ.get("PLATFORM_UPI", "nexoraai@upi"),
    "gpay":       os.environ.get("PLATFORM_GPAY", "nexoraai@okicici"),
    "phonepe":    os.environ.get("PLATFORM_PHONEPE", "nexoraai@ybl"),
    "card_link":  os.environ.get("PLATFORM_CARD", "https://rzp.io/l/nexoraai"),
    "phone":      "+91 7010624989",
}

# ════════════════════════════════════════════════════════════════════════════
#  PAYOUT TRACKING SYSTEM
#  Commission: 10% per order + delivery charge
#  Restaurants paid daily via UPI/Bank transfer
# ════════════════════════════════════════════════════════════════════════════
COMMISSION_RATE = 0.10   # 10% platform commission

# In-memory payout ledger (use database in production)
payout_ledger = {}
order_history = []

def calculate_split(order_total, delivery_charge, commission_rate=COMMISSION_RATE):
    """Calculate how much restaurant gets vs platform keeps"""
    platform_commission = int(order_total * commission_rate)
    platform_total      = platform_commission + delivery_charge
    restaurant_amount   = order_total - platform_commission
    return {
        "order_total":          order_total,
        "delivery_charge":      delivery_charge,
        "platform_commission":  platform_commission,
        "platform_total":       platform_total,
        "restaurant_amount":    restaurant_amount,
    }

def record_order_payout(restaurant_id, order_id, order_total, delivery_charge):
    """Record every order in ledger"""
    split = calculate_split(order_total, delivery_charge)
    
    # Add to ledger
    if restaurant_id not in payout_ledger:
        payout_ledger[restaurant_id] = {
            "pending":     0,
            "paid":        0,
            "total_orders": 0,
        }
    
    payout_ledger[restaurant_id]["pending"]      += split["restaurant_amount"]
    payout_ledger[restaurant_id]["total_orders"] += 1
    
    # Record in history
    order_history.append({
        "order_id":           order_id,
        "restaurant_id":      restaurant_id,
        "order_total":        order_total,
        "platform_commission": split["platform_commission"],
        "restaurant_amount":  split["restaurant_amount"],
        "delivery_charge":    delivery_charge,
        "timestamp":          datetime.now().strftime("%Y-%m-%d %H:%M"),
        "payout_status":      "pending",
    })
    
    print(f"Order {order_id}: Total ₹{order_total} | Restaurant gets ₹{split['restaurant_amount']} | Platform keeps ₹{split['platform_total']}")
    return split

def get_payout_summary():
    """Get summary of all pending payouts"""
    summary = []
    total_pending = 0
    total_platform = 0
    
    for rid, data in payout_ledger.items():
        r = RESTAURANTS.get(rid, {})
        summary.append({
            "restaurant_id":   rid,
            "restaurant_name": r.get("name", rid),
            "phone":           r.get("phone", ""),
            "upi":             r.get("upi", ""),
            "pending_payout":  data["pending"],
            "total_orders":    data["total_orders"],
            "paid_so_far":     data["paid"],
        })
        total_pending += data["pending"]
    
    platform_earnings = sum(
        o["platform_commission"] + o["delivery_charge"]
        for o in order_history
    )
    
    return {
        "summary":          summary,
        "total_pending":    total_pending,
        "platform_earnings": platform_earnings,
        "total_orders":     len(order_history),
    }

def mark_restaurant_paid(restaurant_id, amount=None):
    """Mark restaurant as paid after manual transfer"""
    if restaurant_id in payout_ledger:
        pay_amount = amount or payout_ledger[restaurant_id]["pending"]
        payout_ledger[restaurant_id]["paid"]    += pay_amount
        payout_ledger[restaurant_id]["pending"] -= pay_amount
        
        # Update history
        for order in order_history:
            if order["restaurant_id"] == restaurant_id and order["payout_status"] == "pending":
                order["payout_status"] = "paid"
        
        return True
    return False



# ════════════════════════════════════════════════════════════════════════════
#  PLATFORM — RESTAURANT DATABASE
#  Each restaurant pays ₹5,000/month subscription to NexoraAI
# ════════════════════════════════════════════════════════════════════════════
RESTAURANTS = {
    "R001": {
        "id": "R001",
        "name": "Thenmanan Restaurant",
        "emoji": "🍛",
        "cuisine": "South Indian",
        "area": "T Nagar, Chennai",
        "rating": 4.8,
        "reviews": "1,240",
        "delivery_time": "30-45 mins",
        "delivery_charge": 40,
        "min_order": 150,
        "phone": "+91 90000 11223",
        "gpay": "thenmanan@okicici",
        "phonepe": "thenmanan@ybl",
        "upi": "thenmanan@upi",
        "card_link": "https://rzp.io/l/thenmanan",
        "subscription": "active",
        "plan": "pro",
        "plan_expiry": "2026-12-01",
        "tags": ["biryani","chicken","mutton","idly","dosa","parotta","fish","prawn","south indian","breakfast","paya","idiyappam","samosa","falooda"],
        "menu": {
            "🍗 Biryani": {
                "Chicken Biryani":        {"price":280,"rating":4.9,"orders":2840,"spice":"Medium","time":"20 mins"},
                "Mutton Biryani":         {"price":320,"rating":4.8,"orders":1920,"spice":"Medium","time":"25 mins"},
                "Prawn Biryani":          {"price":350,"rating":4.7,"orders":980, "spice":"Medium-Hot","time":"25 mins"},
                "Vegetable Biryani":      {"price":180,"rating":4.5,"orders":640, "spice":"Mild","time":"15 mins"},
                "Egg Biryani":            {"price":200,"rating":4.6,"orders":760, "spice":"Medium","time":"15 mins"},
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
            },
            "🫓 Breads & Rice": {
                "Parotta":       {"price":25, "rating":4.7,"orders":2400,"spice":"None","time":"8 mins"},
                "Butter Naan":   {"price":40, "rating":4.6,"orders":1800,"spice":"None","time":"10 mins"},
                "Steamed Rice":  {"price":60, "rating":4.4,"orders":1600,"spice":"None","time":"10 mins"},
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
            "🌅 Breakfast (7:30AM–11AM)": {
                "Idiyappam + Paya":     {"price":180,"rating":4.9,"orders":2400,"spice":"Medium","time":"10 mins"},
                "Idly (4pcs) + Sambar": {"price":80, "rating":4.7,"orders":1800,"spice":"Mild","time":"8 mins"},
                "Dosa + Chutney":       {"price":90, "rating":4.8,"orders":2100,"spice":"Mild","time":"8 mins"},
                "Puri + Masala":        {"price":100,"rating":4.6,"orders":1400,"spice":"Mild","time":"10 mins"},
            },
        },
        "offers": {
            "WELCOME10":    {"discount":10,"type":"percent","desc":"10% off first order","min":200},
            "FLAT50":       {"discount":50,"type":"flat","desc":"₹50 off above ₹300","min":300},
            "BIRYANI20":    {"discount":20,"type":"percent","desc":"20% off Biryani","min":280},
            "THENMANAN":    {"discount":100,"type":"flat","desc":"₹100 off above ₹500","min":500},
            "FREEDELIVERY": {"discount":40,"type":"delivery","desc":"Free delivery","min":200},
        },
    },

    "R002": {
        "id": "R002",
        "name": "HelloFoodie",
        "emoji": "🍕",
        "cuisine": "Multi-Cuisine",
        "area": "Anna Nagar, Chennai",
        "rating": 4.6,
        "reviews": "860",
        "delivery_time": "25-40 mins",
        "delivery_charge": 35,
        "min_order": 200,
        "phone": "+91 98765 43210",
        "gpay": "hellofoodie@okicici",
        "phonepe": "hellofoodie@ybl",
        "upi": "hellofoodie@upi",
        "card_link": "https://rzp.io/l/hellofoodie",
        "subscription": "active",
        "plan": "pro",
        "plan_expiry": "2026-12-01",
        "tags": ["pizza","burger","pasta","chicken","biryani","cold coffee","milkshake","fries","multi cuisine","sandwich","wraps"],
        "menu": {
            "🍕 Pizza": {
                "Margherita Pizza":      {"price":299,"rating":4.7,"orders":980, "spice":"Mild","time":"20 mins"},
                "Pepperoni Pizza":       {"price":349,"rating":4.8,"orders":1200,"spice":"Medium","time":"20 mins"},
                "BBQ Chicken Pizza":     {"price":379,"rating":4.7,"orders":840, "spice":"Medium","time":"20 mins"},
                "Veg Loaded Pizza":      {"price":319,"rating":4.5,"orders":620, "spice":"Mild","time":"20 mins"},
            },
            "🍔 Burgers": {
                "Chicken Burger":        {"price":199,"rating":4.7,"orders":1400,"spice":"Medium","time":"12 mins"},
                "Veg Burger":            {"price":149,"rating":4.5,"orders":840, "spice":"Mild","time":"10 mins"},
                "Double Patty Burger":   {"price":249,"rating":4.8,"orders":680, "spice":"Medium","time":"15 mins"},
                "Crispy Chicken Burger": {"price":219,"rating":4.6,"orders":960, "spice":"Medium","time":"12 mins"},
            },
            "🍝 Pasta & Wraps": {
                "Pasta Arrabbiata":      {"price":249,"rating":4.6,"orders":740, "spice":"Hot","time":"15 mins"},
                "Chicken Wrap":          {"price":179,"rating":4.6,"orders":980, "spice":"Medium","time":"10 mins"},
                "Veg Sandwich":          {"price":129,"rating":4.4,"orders":640, "spice":"Mild","time":"8 mins"},
            },
            "🍛 Indian": {
                "Butter Chicken":        {"price":280,"rating":4.8,"orders":1100,"spice":"Mild","time":"15 mins"},
                "Chicken Biryani":       {"price":260,"rating":4.7,"orders":1800,"spice":"Medium","time":"20 mins"},
                "Dal Makhani":           {"price":220,"rating":4.6,"orders":680, "spice":"Mild","time":"15 mins"},
            },
            "🍟 Sides": {
                "French Fries":          {"price":99, "rating":4.6,"orders":2100,"spice":"None","time":"8 mins"},
                "Onion Rings":           {"price":119,"rating":4.5,"orders":840, "spice":"None","time":"8 mins"},
                "Coleslaw":              {"price":79, "rating":4.4,"orders":560, "spice":"None","time":"5 mins"},
            },
            "🥤 Drinks": {
                "Cold Coffee":           {"price":99, "rating":4.7,"orders":1600,"spice":"None","time":"5 mins"},
                "Milkshake":             {"price":120,"rating":4.6,"orders":760, "spice":"None","time":"5 mins"},
                "Fresh Juice":           {"price":80, "rating":4.5,"orders":980, "spice":"None","time":"5 mins"},
            },
        },
        "offers": {
            "HELLO20":      {"discount":20,"type":"percent","desc":"20% off first order","min":300},
            "FLAT100":      {"discount":100,"type":"flat","desc":"₹100 off above ₹500","min":500},
            "FREEDELIVERY": {"discount":35,"type":"delivery","desc":"Free delivery","min":300},
            "PIZZA15":      {"discount":15,"type":"percent","desc":"15% off Pizza orders","min":299},
        },
    },

    "R003": {
        "id": "R003",
        "name": "Spice Kingdom",
        "emoji": "🌶️",
        "cuisine": "North Indian & Mughlai",
        "area": "Velachery, Chennai",
        "rating": 4.7,
        "reviews": "1,080",
        "delivery_time": "35-50 mins",
        "delivery_charge": 45,
        "min_order": 250,
        "phone": "+91 91234 56789",
        "gpay": "spicekingdom@okicici",
        "phonepe": "spicekingdom@ybl",
        "upi": "spicekingdom@upi",
        "card_link": "https://rzp.io/l/spicekingdom",
        "subscription": "active",
        "plan": "starter",
        "plan_expiry": "2026-12-01",
        "tags": ["biryani","chicken","mutton","kebab","naan","roti","paneer","north indian","mughlai","tikka","korma","dal"],
        "menu": {
            "🍗 Biryani & Rice": {
                "Chicken Dum Biryani":   {"price":320,"rating":4.8,"orders":1600,"spice":"Medium","time":"25 mins"},
                "Mutton Dum Biryani":    {"price":380,"rating":4.9,"orders":1100,"spice":"Medium","time":"30 mins"},
                "Veg Biryani":           {"price":220,"rating":4.5,"orders":480, "spice":"Mild","time":"20 mins"},
                "Jeera Rice":            {"price":120,"rating":4.4,"orders":840, "spice":"None","time":"15 mins"},
            },
            "🥩 Non-Veg Mains": {
                "Butter Chicken":        {"price":320,"rating":4.9,"orders":1840,"spice":"Mild","time":"20 mins"},
                "Chicken Tikka Masala":  {"price":340,"rating":4.8,"orders":1200,"spice":"Medium","time":"20 mins"},
                "Mutton Rogan Josh":     {"price":380,"rating":4.8,"orders":840, "spice":"Hot","time":"25 mins"},
                "Chicken Kadai":         {"price":300,"rating":4.7,"orders":980, "spice":"Hot","time":"20 mins"},
            },
            "🥬 Veg Mains": {
                "Paneer Tikka Masala":   {"price":280,"rating":4.7,"orders":960, "spice":"Medium","time":"20 mins"},
                "Dal Makhani":           {"price":240,"rating":4.8,"orders":1100,"spice":"Mild","time":"20 mins"},
                "Palak Paneer":          {"price":260,"rating":4.6,"orders":720, "spice":"Mild","time":"15 mins"},
                "Chana Masala":          {"price":200,"rating":4.5,"orders":580, "spice":"Medium","time":"15 mins"},
            },
            "🍢 Kebabs & Starters": {
                "Chicken Seekh Kebab":   {"price":280,"rating":4.8,"orders":1100,"spice":"Medium","time":"15 mins"},
                "Paneer Tikka":          {"price":260,"rating":4.7,"orders":840, "spice":"Medium","time":"15 mins"},
                "Chicken Reshmi Kebab":  {"price":300,"rating":4.8,"orders":760, "spice":"Mild","time":"15 mins"},
            },
            "🫓 Breads": {
                "Butter Naan":           {"price":45, "rating":4.6,"orders":2200,"spice":"None","time":"10 mins"},
                "Garlic Naan":           {"price":55, "rating":4.7,"orders":1800,"spice":"None","time":"10 mins"},
                "Tandoori Roti":         {"price":35, "rating":4.5,"orders":1600,"spice":"None","time":"10 mins"},
                "Lachha Paratha":        {"price":60, "rating":4.6,"orders":980, "spice":"None","time":"12 mins"},
            },
            "🍦 Desserts": {
                "Gulab Jamun":           {"price":80, "rating":4.7,"orders":1200,"spice":"None","time":"5 mins"},
                "Kheer":                 {"price":100,"rating":4.6,"orders":840, "spice":"None","time":"5 mins"},
                "Mango Lassi":           {"price":90, "rating":4.7,"orders":1100,"spice":"None","time":"5 mins"},
            },
        },
        "offers": {
            "KINGDOM10":    {"discount":10,"type":"percent","desc":"10% off first order","min":300},
            "FLAT75":       {"discount":75,"type":"flat","desc":"₹75 off above ₹400","min":400},
            "FREEDELIVERY": {"discount":45,"type":"delivery","desc":"Free delivery","min":350},
        },
    },
}

# ════════════════════════════════════════════════════════════════════════════
#  SESSION STORAGE
# ════════════════════════════════════════════════════════════════════════════
sessions        = {}   # GPT conversation history
active_orders   = {}   # {sender: {step, restaurant_id, items, subtotal...}}
pending_reviews = {}   # {sender: {step, dish, rating}}

# ════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════════════════════
def get_stars(r):
    return "⭐" * int(r)

def gen_order_id(rid):
    return f"{rid}-{datetime.now().strftime('%d%m%H%M')}{random.randint(10,99)}"

def search_restaurants(query):
    """Find restaurants that serve a particular food"""
    q = query.lower()
    results = []
    for rid, r in RESTAURANTS.items():
        if r.get("subscription") != "active":
            continue
        matched_items = []
        # Check tags
        for tag in r.get("tags", []):
            if q in tag or tag in q:
                matched_items.append(tag)
                break
        # Check menu items directly
        for cat, items in r["menu"].items():
            for item_name, details in items.items():
                if q in item_name.lower():
                    matched_items.append(item_name)
        if matched_items:
            results.append((r, matched_items))
    return results

def find_item_in_restaurant(r, name):
    name_l = name.lower()
    for cat, items in r["menu"].items():
        for item, d in items.items():
            if name_l in item.lower() or item.lower() in name_l:
                return item, d, cat
    return None, None, None

def get_restaurant_by_id(rid):
    return RESTAURANTS.get(rid)

def get_session_restaurant(sender):
    """Get the restaurant a user is currently ordering from"""
    if sender in active_orders:
        rid = active_orders[sender].get("restaurant_id")
        if rid:
            return RESTAURANTS.get(rid)
    return None

def apply_coupon(r, code, subtotal):
    code = code.upper().strip()
    offers = r.get("offers", {})
    if code not in offers:
        return None, "❌ Invalid coupon. Type *offers* to see valid codes."
    o = offers[code]
    if subtotal < o["min"]:
        return None, f"❌ Min order ₹{o['min']} required. Your total: ₹{subtotal}."
    if o["type"] == "percent":
        disc = int(subtotal * o["discount"] / 100)
        return disc, f"✅ *{code}* applied! {o['discount']}% off = ₹{disc} saved 🎉"
    if o["type"] == "flat":
        return o["discount"], f"✅ *{code}* applied! ₹{o['discount']} flat off 🎉"
    if o["type"] == "delivery":
        return r["delivery_charge"], f"✅ *{code}* applied! Free delivery 🎉"
    return None, "❌ Invalid coupon."

# ════════════════════════════════════════════════════════════════════════════
#  PLATFORM WELCOME
# ════════════════════════════════════════════════════════════════════════════
def platform_welcome():
    return """👋 *Welcome to FoodieBot Chennai!* 🍽️
_Your WhatsApp Food Ordering Platform_

━━━━━━━━━━━━━━━━━━━━━━

🔍 *Search food instantly!*
Just type what you're craving:

Examples:
• _biryani_ → See all biryani restaurants
• _pizza_ → Find pizza places
• _dosa_ → Breakfast spots
• _chicken_ → Chicken dishes
• _burger_ → Burger joints

━━━━━━━━━━━━━━━━━━━━━━
Or use these commands:

🍽️ *all* — See all restaurants
🏆 *top* — Top rated restaurants
📍 *area [name]* — Restaurants by area
💰 *cheap* — Budget-friendly options
🌶️ *spicy* — Spicy food lovers
🥬 *veg* — Vegetarian options

_Type any food name to start!_ 😊"""

# ════════════════════════════════════════════════════════════════════════════
#  FOOD SEARCH — SHOW RESTAURANTS
# ════════════════════════════════════════════════════════════════════════════
def show_food_search_results(query, results):
    t  = f"🔍 *Results for \"{query}\"*\n"
    t += f"Found in {len(results)} restaurant(s)\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"

    for i, (r, matched) in enumerate(results, 1):
        t += f"{i}️⃣ {r['emoji']} *{r['name']}*\n"
        t += f"   📍 {r['area']}\n"
        t += f"   ⭐ {r['rating']}/5 ({r['reviews']} reviews)\n"
        t += f"   🛵 {r['delivery_time']} | ₹{r['delivery_charge']} delivery\n"
        t += f"   💰 Min order: ₹{r['min_order']}\n"

        # Show matching items with prices
        item_preview = []
        for cat, items in r["menu"].items():
            for item_name, details in items.items():
                if query.lower() in item_name.lower():
                    item_preview.append(f"{item_name} ₹{details['price']}")
        if item_preview:
            t += f"   🍽️ {' | '.join(item_preview[:3])}\n"
        t += "\n"

    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    t += "📲 *How to order:*\n"

    for i, (r, _) in enumerate(results, 1):
        t += f"Type *{i}* to order from {r['name']}\n"

    t += "\n_Or type another food to search again_ 🔍"
    return t

def show_all_restaurants():
    t  = "🍽️ *All Restaurants on FoodieBot*\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    active = [(rid, r) for rid, r in RESTAURANTS.items() if r.get("subscription") == "active"]
    for i, (rid, r) in enumerate(active, 1):
        t += f"{i}️⃣ {r['emoji']} *{r['name']}*\n"
        t += f"   🍽️ {r['cuisine']}\n"
        t += f"   📍 {r['area']}\n"
        t += f"   ⭐ {r['rating']}/5 | 🛵 {r['delivery_time']}\n"
        t += f"   💰 Min: ₹{r['min_order']} | Delivery: ₹{r['delivery_charge']}\n\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    for i, (rid, r) in enumerate(active, 1):
        t += f"Type *{i}* to order from {r['name']}\n"
    return t

# ════════════════════════════════════════════════════════════════════════════
#  RESTAURANT MENU & ORDER FLOW
# ════════════════════════════════════════════════════════════════════════════
def show_restaurant_home(r):
    t  = f"{r['emoji']} *{r['name']}*\n"
    t += f"🍽️ {r['cuisine']} | 📍 {r['area']}\n"
    t += f"⭐ {r['rating']}/5 ({r['reviews']} reviews)\n"
    t += f"🛵 {r['delivery_time']} | ₹{r['delivery_charge']} delivery\n"
    t += f"💰 Min order: ₹{r['min_order']}\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    t += "*What would you like?*\n\n"
    t += "🍽️ *M* — Full Menu\n"
    t += "🏆 *T* — Top Dishes\n"
    t += "🎉 *O* — Today's Offers\n"
    t += "📦 *P* — Place Order\n"
    t += "⭐ *R* — Reviews\n"
    t += "💳 *Y* — Payment Methods\n"
    t += "🔙 *back* — Search Other Restaurants\n\n"
    t += "_Or just tell me what you want to order!_ 😊"
    return t

def show_restaurant_menu(r):
    t  = f"🍽️ *{r['name']} — Full Menu*\n"
    t += f"⭐ {r['rating']}/5 | Min order ₹{r['min_order']}\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for cat, items in r["menu"].items():
        t += f"*{cat}*\n"
        for item, d in items.items():
            t += f"  • {item} — ₹{d['price']} {get_stars(d['rating'])}\n"
        t += "\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    t += "💰 Type *O* for today's offers!\n"
    t += "_Tell me what you want to order_ 🛒"
    return t

def show_top_dishes(r):
    items = [(item, d) for cat, its in r["menu"].items() for item, d in its.items()]
    top   = sorted(items, key=lambda x: (x[1]['rating'], x[1]['orders']), reverse=True)[:8]
    t  = f"🏆 *Top Dishes at {r['name']}*\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, (item, d) in enumerate(top, 1):
        t += f"{i}. *{item}* — ₹{d['price']}\n"
        t += f"   {get_stars(d['rating'])} {d['rating']}/5 | {d['orders']:,}+ orders\n\n"
    t += "_Tell me what you want to order!_ 🛒"
    return t

def show_offers(r):
    t  = f"🎉 *Offers at {r['name']}*\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for code, o in r.get("offers", {}).items():
        t += f"🏷️ *{code}*\n   {o['desc']}\n   Min: ₹{o['min']}\n\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    t += "Apply coupon while ordering!\nType *P* to place order 🛒"
    return t

def show_payment_methods(r):
    return f"""💳 *Payment at {r['name']}*

1️⃣ *Google Pay*
   `{r['gpay']}`

2️⃣ *PhonePe*
   `{r['phonepe']}`

3️⃣ *Any UPI / Paytm*
   `{r['upi']}`

4️⃣ *Credit / Debit Card*
   {r['card_link']}

5️⃣ *Cash on Delivery*
   Pay at your door 💵

📸 After UPI payment share screenshot here!"""

def build_order_summary(r, items_dict, discount=0, coupon_type=None, name="Customer"):
    subtotal = sum(d["price"] * qty for item_name, (d, qty) in items_dict.items())
    delivery = 0 if coupon_type == "delivery" else r["delivery_charge"]
    total    = subtotal - discount + delivery
    order_id = gen_order_id(r["id"])

    t  = f"✅ *Order Summary — {r['name']}*\n"
    t += f"Order ID: *{order_id}*\n"
    t += f"Customer: {name}\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    for item_name, (d, qty) in items_dict.items():
        t += f"• {item_name} x{qty} = ₹{d['price']*qty}\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    t += f"📦 Subtotal:   ₹{subtotal}\n"
    if discount > 0:
        t += f"🎉 Discount:  -₹{discount}\n"
    t += f"🛵 Delivery:   ₹{delivery}\n"
    t += f"💰 *Total:     ₹{total}*\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    # Platform UPI deep links (NexoraAI collects payment)
    gpay_link    = f"gpay://upi/pay?pa={PLATFORM['upi']}&am={total}&tn=FoodOrder-{order_id}&cu=INR"
    phonepe_link = f"phonepe://pay?pa={PLATFORM['upi']}&am={total}&tn=FoodOrder-{order_id}&cu=INR"
    paytm_link   = f"paytmmp://pay?pa={PLATFORM['upi']}&am={total}&tn=FoodOrder-{order_id}&cu=INR"

    t += "*Choose Payment Method:*\n\n"
    t += f"1️⃣ *Google Pay* 📱\n"
    t += f"   Amount: *₹{total}*\n"
    t += f"   👉 {gpay_link}\n\n"
    t += f"2️⃣ *PhonePe* 📱\n"
    t += f"   Amount: *₹{total}*\n"
    t += f"   👉 {phonepe_link}\n\n"
    t += f"3️⃣ *Paytm / Any UPI* 📱\n"
    t += f"   Amount: *₹{total}*\n"
    t += f"   👉 {paytm_link}\n\n"
    t += f"4️⃣ *Credit / Debit Card* 💳\n"
    t += f"   Amount: *₹{total}*\n"
    t += f"   👉 {PLATFORM['card_link']}?amount={total}\n\n"
    t += f"5️⃣ *Cash on Delivery* 💵\n"
    t += f"   Pay *₹{total}* at your door\n"
    t += f"   Type *cod* to confirm instantly\n\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    t += "📸 *After online payment:*\n"
    t += "Share payment screenshot here ✅\n\n"
    t += f"Order ID: *{order_id}*\n"
    t += f"⏱️ Delivery: {r['delivery_time']}\n"
    t += f"📞 Help: {PLATFORM['phone']}"
    return t, order_id, total

# ════════════════════════════════════════════════════════════════════════════
#  GPT ORDER HANDLER
# ════════════════════════════════════════════════════════════════════════════
def ask_gpt_order(r, sender, text):
    sessions.setdefault(sender, [])
    sessions[sender].append({"role":"user","content":text})
    if len(sessions[sender]) > 20:
        sessions[sender] = sessions[sender][-20:]

    menu_str = ""
    for cat, items in r["menu"].items():
        for item, d in items.items():
            menu_str += f"{item} ₹{d['price']}, "

    offers_str = ", ".join([f"{c}: {o['desc']}" for c, o in r.get("offers",{}).items()])

    system = f"""You are a WhatsApp food ordering assistant for {r['name']} ({r['cuisine']}).

MENU: {menu_str}
OFFERS: {offers_str}
PAYMENT: GPay {r['gpay']} | PhonePe {r['phonepe']} | UPI {r['upi']} | Card {r['card_link']} | COD
DELIVERY: {r['delivery_time']} | ₹{r['delivery_charge']} charge | Min ₹{r['min_order']}

ORDERING FLOW:
1. Confirm items ordered + calculate total
2. Suggest applying a coupon (mention 'offers' command)
3. Collect customer name + delivery address
4. Show final bill with discount
5. Show all payment options with exact amounts
6. After payment screenshot or COD selection, confirm order

Be friendly, use emojis, reply in customer's language (Tamil/English).
Always suggest top-selling dishes if customer seems unsure."""

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
    return f"Please call {r['phone']} to complete your order 📞"

# ════════════════════════════════════════════════════════════════════════════
#  MAIN MESSAGE HANDLER
# ════════════════════════════════════════════════════════════════════════════
def handle_message(sender, text):
    t = text.lower().strip()
    order = active_orders.get(sender, {})
    r = get_restaurant_by_id(order.get("restaurant_id")) if order.get("restaurant_id") else None

    # ── BACK TO SEARCH ────────────────────────────────────────────────────
    if t in ["back","search","home","restart","start over"]:
        active_orders.pop(sender, None)
        sessions.pop(sender, None)
        return platform_welcome()

    # ── REVIEW FLOW ───────────────────────────────────────────────────────
    if sender in pending_reviews:
        pr = pending_reviews[sender]
        step = pr.get("step")
        if step == "dish":
            pr["dish"] = text; pr["step"] = "rating"
            return "Rate 1-5:\n1️⃣ Poor  2️⃣ Below Avg  3️⃣ Good\n4️⃣ Very Good  5️⃣ Excellent ⭐"
        if step == "rating":
            try:
                rating = int(t)
                if 1 <= rating <= 5:
                    pr["rating"] = rating; pr["step"] = "review"
                    return f"Rated {get_stars(rating)} ({rating}/5)\nShare your experience 🙏"
            except:
                pass
            return "Reply with 1-5 ⭐"
        if step == "review":
            dish = pr.get("dish","Overall"); rating = pr.get("rating",5)
            rname = pr.get("restaurant","")
            del pending_reviews[sender]
            return f"✅ *Thank You!*\n\n*{dish}* at {rname}\n{get_stars(rating)} ({rating}/5)\n_{text}_\n\n🎁 Free Masala Chai on next visit! ☕"
        del pending_reviews[sender]
        return "Thank you! 🙏"

    # ── COD / PAYMENT CONFIRMATION ────────────────────────────────────────
    if r and order.get("step") == "payment":
        oid   = order.get("oid", gen_order_id(r["id"]))
        total = order.get("total", "?")
        name  = order.get("name", "Customer")

        if any(x in t for x in ["cod","cash","cash on delivery","5"]):
            del active_orders[sender]
            record_order_payout(r["id"], oid, order.get("subtotal",0), r["delivery_charge"])
            return f"""✅ *Order Confirmed — COD!*
Order ID: *{oid}*
Restaurant: {r['name']}
Amount: ₹{total} (pay at door)
Customer: {name}

💵 Keep exact change ready.
🛵 Delivery in {r['delivery_time']}
📞 {r['phone']} ❤️"""

        if any(x in t for x in ["paid","done","sent","payment","screenshot"]):
            del active_orders[sender]
            record_order_payout(r["id"], oid, order.get("subtotal",0), r["delivery_charge"])
            return f"""✅ *Payment Confirmed — Order Placed!*
Order ID: *{oid}*
Restaurant: {r['name']}
Amount: ₹{total}
Customer: {name}

🎉 Preparing your order now!
🛵 Delivery in {r['delivery_time']}
Enjoy your meal! 🍛❤️
📞 {r['phone']}"""

    # ── COUPON STEP ───────────────────────────────────────────────────────
    if r and order.get("step") == "coupon":
        subtotal = order.get("subtotal", 0)
        items_dict = order.get("items_dict", {})
        name = order.get("name","Customer")

        if t in ["skip","no","none","0"]:
            summary, oid, total = build_order_summary(r, items_dict, 0, None, name)
            active_orders[sender].update({"step":"payment","oid":oid,"total":total,"discount":0})
            return summary

        disc, msg = apply_coupon(r, text, subtotal)
        if disc is not None:
            o = r.get("offers",{}).get(text.upper(),{})
            summary, oid, total = build_order_summary(r, items_dict, disc, o.get("type"), name)
            active_orders[sender].update({"step":"payment","oid":oid,"total":total,"discount":disc})
            return f"{msg}\n\n{summary}"
        return f"{msg}\n\nType coupon or *skip* to continue."

    # ── RESTAURANT SELECTED (number from search results) ──────────────────
    if "search_results" in order and t in ["1","2","3","4","5"]:
        idx = int(t) - 1
        results = order["search_results"]
        if 0 <= idx < len(results):
            selected_r, _ = results[idx]
            active_orders[sender] = {"restaurant_id": selected_r["id"]}
            return show_restaurant_home(selected_r)
        return "Please type a valid number from the list."

    # ── ALL RESTAURANTS LIST — SELECT BY NUMBER ───────────────────────────
    if "all_list" in order and t in ["1","2","3","4","5","6"]:
        idx = int(t) - 1
        active_list = [(rid, r) for rid, r in RESTAURANTS.items() if r.get("subscription") == "active"]
        if 0 <= idx < len(active_list):
            rid, selected_r = active_list[idx]
            active_orders[sender] = {"restaurant_id": selected_r["id"]}
            return show_restaurant_home(selected_r)
        return "Please type a valid number."

    # ── IN A RESTAURANT SESSION ───────────────────────────────────────────
    if r:
        # Menu commands
        if t in ["m","menu","show menu","full menu"]:
            return show_restaurant_menu(r)
        if t in ["t","top","top dishes","best"]:
            return show_top_dishes(r)
        if t in ["o","offers","deals","coupon","discount"]:
            return show_offers(r)
        if t in ["y","payment","pay","how to pay"]:
            return show_payment_methods(r)
        if t in ["r","reviews","feedback","ratings"]:
            reviews = r.get("reviews", [])
            t2  = f"⭐ *{r['name']} — Reviews*\n{r['rating']}/5 ({r['reviews']} reviews)\n"
            t2 += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            t2 += "Type *add review* to share your experience! 📝"
            return t2
        if t in ["add review","write review","give review"]:
            pending_reviews[sender] = {"step":"dish","restaurant":r["name"]}
            return f"📝 Review for *{r['name']}*\n\nWhich dish would you like to review?"
        if t in ["p","place order","order","i want to order"]:
            return f"""🛒 *Order from {r['name']}*

Tell me what you'd like! Example:
_"1 Chicken Biryani and 2 Samosa"_

💰 Type *O* to see today's offers first!
Min order: ₹{r['min_order']}"""

        # Order keywords — detect food items and process
        order_kw = ["order","want","give","send","1 ","2 ","3 "]
        food_kw  = any(item.split()[0].lower() in t for cat, items in r["menu"].items() for item in items)

        if food_kw or any(x in t for x in order_kw):
            # Parse items from message
            items_dict = {}
            total_price = 0
            for cat, items in r["menu"].items():
                for item_name, details in items.items():
                    if item_name.lower() in t:
                        # Try to detect quantity
                        qty = 1
                        words = t.split()
                        for i, word in enumerate(words):
                            if word.isdigit() and i+1 < len(words):
                                if item_name.split()[0].lower() in words[i+1].lower():
                                    qty = int(word)
                        items_dict[item_name] = (details, qty)
                        total_price += details["price"] * qty

            if items_dict and total_price >= r["min_order"]:
                # Ask for name and address
                active_orders[sender].update({
                    "items_dict": items_dict,
                    "subtotal": total_price,
                    "step": "name_address"
                })
                items_preview = "\n".join([f"• {name} x{qty} = ₹{d['price']*qty}" for name, (d, qty) in items_dict.items()])
                return f"""🛒 *Your Order:*
{items_preview}
━━━━━━━━━━━━━━━━━━━━━━
Subtotal: ₹{total_price}

Please share your:
👤 *Name* and 📍 *Delivery Address*
(in one message)"""

            elif items_dict and total_price < r["min_order"]:
                return f"❌ Min order is ₹{r['min_order']}. Your total is ₹{total_price}. Please add more items!\n\nType *M* to see menu."

            # Let GPT handle complex orders
            return ask_gpt_order(r, sender, text)

        # Name + Address step
        if order.get("step") == "name_address" and len(text) > 5:
            active_orders[sender]["name"] = text
            active_orders[sender]["address"] = text
            active_orders[sender]["step"] = "coupon"
            subtotal = order.get("subtotal",0)
            offers_list = ", ".join(r.get("offers",{}).keys())
            return f"""✅ Delivery details saved!

🎉 *Do you have a coupon code?*
Available: *{offers_list}*

Type coupon code or *skip* to continue
_(Type *O* to see offer details)_"""

        # GPT fallback for any other message in restaurant
        return ask_gpt_order(r, sender, text)

    # ── PLATFORM LEVEL COMMANDS (no restaurant selected) ─────────────────

    # Greetings — show platform welcome
    if t in ["hi","hello","hey","start","hai","hii","vanakkam","food","order"]:
        return platform_welcome()

    # All restaurants
    if t in ["all","all restaurants","restaurants","list"]:
        active_orders[sender] = {"all_list": True}
        return show_all_restaurants()

    # Top rated
    if t in ["top","top rated","best restaurants"]:
        sorted_r = sorted(RESTAURANTS.values(), key=lambda x: x["rating"], reverse=True)
        t2  = "🏆 *Top Rated Restaurants*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, res in enumerate(sorted_r[:5], 1):
            t2 += f"{i}️⃣ {res['emoji']} *{res['name']}*\n"
            t2 += f"   ⭐ {res['rating']}/5 | {res['cuisine']}\n"
            t2 += f"   📍 {res['area']} | 🛵 {res['delivery_time']}\n\n"
        t2 += "Type number to order!"
        active_orders[sender] = {"all_list": True}
        return t2

    # Budget friendly
    if t in ["cheap","budget","affordable","low price"]:
        sorted_r = sorted(RESTAURANTS.values(), key=lambda x: x["min_order"])
        t2  = "💰 *Budget-Friendly Restaurants*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, res in enumerate(sorted_r[:5], 1):
            t2 += f"{i}️⃣ {res['emoji']} *{res['name']}*\n"
            t2 += f"   Min order: ₹{res['min_order']} | Delivery: ₹{res['delivery_charge']}\n"
            t2 += f"   📍 {res['area']}\n\n"
        active_orders[sender] = {"all_list": True}
        return t2

    # Veg filter
    if t in ["veg","vegetarian","pure veg"]:
        t2  = "🥬 *Vegetarian Options*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, (rid, res) in enumerate(RESTAURANTS.items(), 1):
            veg_items = [item for cat, items in res["menu"].items() for item, d in items.items() if d['spice'] in ['Mild','None']]
            if veg_items:
                t2 += f"{i}️⃣ {res['emoji']} *{res['name']}*\n"
                t2 += f"   {', '.join(veg_items[:3])}\n"
                t2 += f"   📍 {res['area']}\n\n"
        active_orders[sender] = {"all_list": True}
        return t2

    # Area search
    if t.startswith("area "):
        area = t.replace("area ","").strip()
        results = [(r, []) for r in RESTAURANTS.values() if area in r["area"].lower()]
        if results:
            t2  = f"📍 *Restaurants in {area.title()}*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            for i, (res, _) in enumerate(results, 1):
                t2 += f"{i}️⃣ {res['emoji']} *{res['name']}*\n"
                t2 += f"   ⭐ {res['rating']}/5 | {res['cuisine']}\n"
                t2 += f"   🛵 {res['delivery_time']} | Min ₹{res['min_order']}\n\n"
            active_orders[sender] = {"search_results": [(r, []) for r, _ in results]}
            return t2
        return f"No restaurants found in *{area}*. Try: *T Nagar*, *Anna Nagar*, *Velachery*"

    # ── FOOD SEARCH — THE MAIN FEATURE ───────────────────────────────────
    # Strip common words
    food_query = t
    for word in ["i want","i need","show me","give me","order","looking for","want to eat","want"]:
        food_query = food_query.replace(word,"").strip()

    if len(food_query) > 1:
        results = search_restaurants(food_query)
        if results:
            active_orders[sender] = {"search_results": results}
            return show_food_search_results(food_query, results)
        # No results
        return f"""🔍 No restaurants found for *"{food_query}"*

Try searching:
• biryani 🍛
• chicken 🍗
• pizza 🍕
• dosa 🫓
• burger 🍔

Or type *all* to see all restaurants! 🍽️"""

    return platform_welcome()

# ════════════════════════════════════════════════════════════════════════════
#  FLASK ROUTES
# ════════════════════════════════════════════════════════════════════════════
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    sender = request.form.get("From","")
    text   = request.form.get("Body","").strip()
    media  = int(request.form.get("NumMedia","0"))
    print(f"📱 From: {sender} | Msg: {text[:80]}")

    resp = MessagingResponse()

    # Payment screenshot detection
    if media > 0:
        order = active_orders.get(sender, {})
        r = get_restaurant_by_id(order.get("restaurant_id"))
        if r and order.get("step") == "payment":
            oid   = order.get("oid", gen_order_id(r["id"]))
            total = order.get("total","?")
            del active_orders[sender]
            resp.message(f"✅ *Screenshot Received — Order Confirmed!*\nOrder ID: *{oid}*\nRestaurant: {r['name']}\nAmount: ₹{total}\n\n🎉 Preparing now!\n🛵 {r['delivery_time']}\nEnjoy! 🍛❤️")
            return str(resp)

    try:
        reply = handle_message(sender, text)
    except Exception as e:
        print(f"Error: {e}")
        import traceback; traceback.print_exc()
        reply = "Sorry, something went wrong! Try again or type *hi* to restart 🙏"

    resp.message(reply)
    return str(resp)

@app.route("/admin/payouts", methods=["GET"])
def admin_payouts():
    """View all pending restaurant payouts"""
    if request.args.get("key") != MASTER_KEY:
        return jsonify({"error":"Unauthorized"}), 401
    data = get_payout_summary()
    return jsonify(data)

@app.route("/admin/payout/mark-paid", methods=["POST"])
def mark_paid():
    """Mark a restaurant as paid after manual UPI transfer"""
    if request.json.get("key") != MASTER_KEY:
        return jsonify({"error":"Unauthorized"}), 401
    rid    = request.json.get("restaurant_id")
    amount = request.json.get("amount")
    if mark_restaurant_paid(rid, amount):
        return jsonify({"success": True, "message": f"Marked {rid} as paid ₹{amount}"})
    return jsonify({"success": False, "message": "Restaurant not found"}), 404

@app.route("/admin/orders", methods=["GET"])
def admin_orders():
    """View all order history"""
    if request.args.get("key") != MASTER_KEY:
        return jsonify({"error":"Unauthorized"}), 401
    return jsonify({
        "orders": order_history[-50:],
        "total":  len(order_history)
    })

@app.route("/admin/stats", methods=["GET"])
def admin_stats():
    if request.args.get("key") != MASTER_KEY:
        return jsonify({"error":"Unauthorized"}), 401
    if request.args.get("key") != MASTER_KEY:
        return jsonify({"error":"Unauthorized"}), 401
    active = [r for r in RESTAURANTS.values() if r.get("subscription")=="active"]
    mrr    = sum({"starter":2999,"pro":4999,"enterprise":9999}.get(r.get("plan","starter"),2999) for r in active)
    payout = get_payout_summary()
    return jsonify({
        "platform":              "FoodieBot by NexoraAI",
        "total_restaurants":     len(RESTAURANTS),
        "active_subscriptions":  len(active),
        "subscription_revenue":  f"₹{mrr:,}/month",
        "annual_subscription":   f"₹{mrr*12:,}/year",
        "total_orders_today":    len(order_history),
        "platform_commission_earned": f"₹{payout['platform_earnings']:,}",
        "pending_restaurant_payouts": f"₹{payout['total_pending']:,}",
        "restaurants": [{"id":r["id"],"name":r["name"],"plan":r.get("plan"),"area":r["area"]} for r in active]
    })

@app.route("/")
def home():
    active = len([r for r in RESTAURANTS.values() if r.get("subscription")=="active"])
    return f"""
    <h1>🍽️ FoodieBot — WhatsApp Food Platform</h1>
    <h3>by NexoraAI</h3>
    <hr>
    <p>✅ Platform Live!</p>
    <p>🏪 Restaurants: <b>{len(RESTAURANTS)}</b></p>
    <p>✅ Active: <b>{active}</b></p>
    <hr>
    <h3>How it works:</h3>
    <p>Customer types <b>"biryani"</b> → sees all restaurants with biryani → picks one → orders → pays</p>
    <hr>
    <p>📞 NexoraAI: +91 7010624989 | nexoraai.netlify.app</p>
    """, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=False)
