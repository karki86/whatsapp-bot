"""
FoodieBot Chennai — SuperBot v4.0
NexoraAI | nexoraaiagen@gmail.com | +91 7010624989
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEW in v4:
  ✅ CART CRUD — add / remove / update / clear individual items
  ✅ MINIMUM ORDER GUARD — blocks checkout if total < ₹100, shows shortfall
  ✅ VOICE COMMAND ORDERING — "2 idly 1 vada" / "biryani 1 chicken 65 2"
  ✅ 4 KM RADIUS FILTER — food search only shows restaurants within 4 km
  ✅ ALL RESTAURANTS WITHIN 4 KM — "all" command respects radius

Retained from v3:
  ✅ WhatsApp Location Pin (lat/lng → zone)
  ✅ 60-zone Chennai map + text_to_zone()
  ✅ Proactive AI greetings by time-of-day
  ✅ Admin APIs, payout ledger, GPT fallback
"""

import os, re, math, time, uuid, random, datetime
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ════════════════════════════════════════════════════════════════════════════
#  ENV
# ════════════════════════════════════════════════════════════════════════════
TWILIO_SID   = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH  = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM  = os.environ.get("TWILIO_FROM", "whatsapp:+14155238886")
OPENAI_KEY   = os.environ.get("OPENAI_API_KEY", "")
ADMIN_KEY    = os.environ.get("ADMIN_KEY", "NEXORAAI2026")

PLATFORM = {
    "name":       "FoodieBot Chennai",
    "upi":        "nexoraai@upi",
    "phone":      "+91 7010624989",
    "powered":    "NexoraAI",
    "commission": 0.10,
}

MIN_ORDER_GLOBAL = 100   # ₹ — absolute floor across all restaurants

NEARBY_RADIUS_KM = 4.0  # km — radius for food search & "all" command

# ════════════════════════════════════════════════════════════════════════════
#  CHENNAI ZONES
# ════════════════════════════════════════════════════════════════════════════
CHENNAI_ZONES = {
    "tiruvottiyur": (13.1670,80.3020,"Tiruvottiyur"),
    "manali":       (13.1680,80.2620,"Manali"),
    "madhavaram":   (13.1490,80.2290,"Madhavaram"),
    "kolathur":     (13.1190,80.2200,"Kolathur"),
    "perambur":     (13.1140,80.2460,"Perambur"),
    "vyasarpadi":   (13.1060,80.2490,"Vyasarpadi"),
    "tondiarpet":   (13.1090,80.2810,"Tondiarpet"),
    "royapuram":    (13.1080,80.2930,"Royapuram"),
    "egmore":       (13.0790,80.2610,"Egmore"),
    "park town":    (13.0810,80.2750,"Park Town"),
    "central":      (13.0827,80.2707,"Chennai Central"),
    "chennai central":(13.0827,80.2707,"Chennai Central"),
    "choolai":      (13.0920,80.2580,"Choolai"),
    "aminjikarai":  (13.0890,80.2370,"Aminjikarai"),
    "kilpauk":      (13.0890,80.2420,"Kilpauk"),
    "chetpet":      (13.0800,80.2450,"Chetpet"),
    "purasaiwakkam":(13.0850,80.2480,"Purasaiwakkam"),
    "vepery":       (13.0860,80.2620,"Vepery"),
    "sowcarpet":    (13.0900,80.2740,"Sowcarpet"),
    "parrys":       (13.0920,80.2820,"Parrys Corner"),
    "george town":  (13.0940,80.2880,"George Town"),
    "t nagar":      (13.0418,80.2341,"T Nagar"),
    "tnagar":       (13.0418,80.2341,"T Nagar"),
    "pondy bazaar": (13.0418,80.2341,"T Nagar"),
    "kodambakkam":  (13.0530,80.2220,"Kodambakkam"),
    "ashok nagar":  (13.0370,80.2120,"Ashok Nagar"),
    "vadapalani":   (13.0530,80.2130,"Vadapalani"),
    "koyambedu":    (13.0720,80.1950,"Koyambedu"),
    "arumbakkam":   (13.0720,80.2130,"Arumbakkam"),
    "virugambakkam":(13.0550,80.1940,"Virugambakkam"),
    "valasaravakkam":(13.0370,80.1760,"Valasaravakkam"),
    "saligramam":   (13.0470,80.1870,"Saligramam"),
    "anna nagar":   (13.0850,80.2100,"Anna Nagar"),
    "anna nagar east":(13.0840,80.2200,"Anna Nagar East"),
    "mylapore":     (13.0340,80.2690,"Mylapore"),
    "mandaveli":    (13.0270,80.2650,"Mandaveli"),
    "royapettah":   (13.0530,80.2610,"Royapettah"),
    "nungambakkam": (13.0620,80.2430,"Nungambakkam"),
    "alwarpet":     (13.0380,80.2540,"Alwarpet"),
    "teynampet":    (13.0400,80.2490,"Teynampet"),
    "gopalapuram":  (13.0420,80.2570,"Gopalapuram"),
    "boat club":    (13.0290,80.2550,"Boat Club"),
    "adyar":        (13.0063,80.2574,"Adyar"),
    "kotturpuram":  (13.0150,80.2470,"Kotturpuram"),
    "thiruvanmiyur":(12.9839,80.2592,"Thiruvanmiyur"),
    "besant nagar": (13.0002,80.2698,"Besant Nagar"),
    "neelankarai":  (12.9520,80.2527,"Neelankarai"),
    "palavakkam":   (12.9450,80.2500,"Palavakkam"),
    "sholinganallur":(12.9010,80.2278,"Sholinganallur"),
    "perungudi":    (12.9650,80.2430,"Perungudi"),
    "taramani":     (12.9850,80.2400,"Taramani"),
    "velachery":    (12.9788,80.2204,"Velachery"),
    "nanganallur":  (12.9950,80.1970,"Nanganallur"),
    "pallikaranai": (12.9370,80.2040,"Pallikaranai"),
    "chromepet":    (12.9516,80.1426,"Chromepet"),
    "tambaram":     (12.9249,80.1000,"Tambaram"),
    "guindy":       (13.0067,80.2206,"Guindy"),
    "ekkatuthangal":(13.0160,80.2070,"Ekkatuthangal"),
    "saidapet":     (13.0220,80.2290,"Saidapet"),
    "little mount": (13.0200,80.2230,"Little Mount"),
    "porur":        (13.0370,80.1570,"Porur"),
    "poonamallee":  (13.0480,80.0970,"Poonamallee"),
    "ambattur":     (13.1140,80.1620,"Ambattur"),
    "avadi":        (13.1150,80.0980,"Avadi"),
    "mogappair":    (13.0930,80.1680,"Mogappair"),
    "padi":         (13.1080,80.1990,"Padi"),
    "omr":          (12.9010,80.2278,"OMR"),
    "siruseri":     (12.8560,80.2180,"Siruseri"),
    "navalur":      (12.8420,80.2270,"Navalur"),
    "kelambakkam":  (12.7870,80.2100,"Kelambakkam"),
}

# ════════════════════════════════════════════════════════════════════════════
#  RESTAURANTS
# ════════════════════════════════════════════════════════════════════════════
RESTAURANTS = {
    "saravana": {
        "name":"Hotel Saravana Bhavan","emoji":"🥣","cuisine":"South Indian Veg","type":"veg",
        "area":"T Nagar","lat":13.0400,"lng":80.2330,
        "address":"No 77, Usman Rd, T Nagar","phone":"+91 44 28340000",
        "rating":4.6,"reviews":2340,"delivery_time":"25-35 min",
        "delivery_charge":30,"min_order":150,"timing":"6 AM – 11 PM","subscription":"active",
        "menu":{
            "Breakfast":{
                "Idly (2 pcs)":       {"price":50, "veg":True},
                "Masala Dosa":        {"price":90, "veg":True},
                "Pongal":             {"price":70, "veg":True},
                "Rava Upma":          {"price":60, "veg":True},
                "Mini Tiffin Combo":  {"price":120,"veg":True},
                "Vada":               {"price":30, "veg":True},
                "Sambar Vada":        {"price":50, "veg":True},
            },
            "Meals":{
                "Full Meals":         {"price":180,"veg":True},
                "Mini Meals":         {"price":140,"veg":True},
                "Curd Rice":          {"price":80, "veg":True},
            },
            "Drinks":{
                "Filter Coffee":      {"price":40, "veg":True},
                "Buttermilk":         {"price":30, "veg":True},
            }
        },
        "offers":{
            "SB10":   {"type":"percent","discount":10,"min":200,"desc":"10% off on ₹200+"},
            "MORNING":{"type":"flat",   "discount":30,"min":150,"desc":"₹30 off breakfast"},
        },
        "delivery_partners":[
            {"name":"Rajan K", "phone":"+91 9876500001","rating":4.8},
            {"name":"Muthu S", "phone":"+91 9876500002","rating":4.7},
        ]
    },
    "anjappar":{
        "name":"Anjappar Chettinad","emoji":"🍗","cuisine":"Chettinad Non-Veg","type":"nonveg",
        "area":"Anna Nagar","lat":13.0840,"lng":80.2100,
        "address":"Shop 7, 2nd Ave, Anna Nagar","phone":"+91 44 26261616",
        "rating":4.5,"reviews":1820,"delivery_time":"35-50 min",
        "delivery_charge":40,"min_order":300,"timing":"11 AM – 11 PM","subscription":"active",
        "menu":{
            "Biryani":{
                "Chicken Biryani":    {"price":280,"veg":False},
                "Mutton Biryani":     {"price":380,"veg":False},
                "Egg Biryani":        {"price":220,"veg":False},
                "Prawn Biryani":      {"price":420,"veg":False},
            },
            "Gravy":{
                "Chicken Chettinad":  {"price":320,"veg":False},
                "Mutton Pepper Fry":  {"price":420,"veg":False},
                "Fish Curry":         {"price":300,"veg":False},
            },
            "Starters":{
                "Chicken 65":         {"price":260,"veg":False},
                "Mutton Sukka":       {"price":360,"veg":False},
                "Prawn Fry":          {"price":340,"veg":False},
            }
        },
        "offers":{
            "CHETTINAD15":{"type":"percent","discount":15,"min":500,"desc":"15% off ₹500+"},
            "FREEDEL":    {"type":"delivery","discount":40,"min":400,"desc":"Free delivery ₹400+"},
        },
        "delivery_partners":[
            {"name":"Kumar R",   "phone":"+91 9876500003","rating":4.6},
            {"name":"Pradeep M", "phone":"+91 9876500004","rating":4.9},
        ]
    },
    "murugan":{
        "name":"Murugan Idli Shop","emoji":"🫕","cuisine":"Traditional Tiffin","type":"veg",
        "area":"Mylapore","lat":13.0340,"lng":80.2690,
        "address":"77, Luz Church Rd, Mylapore","phone":"+91 44 28113455",
        "rating":4.7,"reviews":3100,"delivery_time":"20-30 min",
        "delivery_charge":25,"min_order":100,"timing":"6 AM – 10 PM","subscription":"active",
        "menu":{
            "Signature":{
                "Soft Idly (4 pcs)":  {"price":80, "veg":True},
                "Ghee Idly (2 pcs)":  {"price":90, "veg":True},
                "Sambar Vada":        {"price":70, "veg":True},
                "Set Dosa":           {"price":100,"veg":True},
                "Podi Idly":          {"price":90, "veg":True},
                "Vada":               {"price":35, "veg":True},
                "Medu Vada":          {"price":40, "veg":True},
            },
            "Combos":{
                "Idly Vada Combo":    {"price":130,"veg":True},
                "Dosa Sambar Combo":  {"price":140,"veg":True},
                "Breakfast Thali":    {"price":180,"veg":True},
            },
        },
        "offers":{
            "MURUGAN20":{"type":"flat","discount":20,"min":150,"desc":"₹20 off on ₹150+"},
        },
        "delivery_partners":[
            {"name":"Selvam T","phone":"+91 9876500005","rating":4.7},
        ]
    },
    "buhari":{
        "name":"Buhari Restaurant","emoji":"🍖","cuisine":"Mughlai & Biryani","type":"nonveg",
        "area":"Egmore","lat":13.0790,"lng":80.2610,
        "address":"83, Anna Salai, Egmore","phone":"+91 44 28521001",
        "rating":4.4,"reviews":2780,"delivery_time":"40-55 min",
        "delivery_charge":45,"min_order":350,"timing":"12 PM – 12 AM","subscription":"active",
        "menu":{
            "Biryani":{
                "Buhari Special Biryani":  {"price":350,"veg":False},
                "Mutton Dum Biryani":      {"price":420,"veg":False},
                "Chicken Dum Biryani":     {"price":320,"veg":False},
                "Veg Biryani":             {"price":220,"veg":True},
            },
            "Kebab":{
                "Chicken Seekh Kebab":     {"price":340,"veg":False},
                "Tandoori Chicken (half)": {"price":360,"veg":False},
            },
            "Gravy":{
                "Butter Chicken":          {"price":320,"veg":False},
                "Dal Makhani":             {"price":200,"veg":True},
            }
        },
        "offers":{
            "BUHARI50":{"type":"flat",   "discount":50,"min":500,"desc":"₹50 off on ₹500+"},
            "NIGHTOWL":{"type":"percent","discount":20,"min":400,"desc":"20% off after 9 PM"},
        },
        "delivery_partners":[
            {"name":"Arjun P", "phone":"+91 9876500006","rating":4.5},
            {"name":"Dinesh K","phone":"+91 9876500007","rating":4.6},
        ]
    },
    "cream_centre":{
        "name":"Cream Centre","emoji":"🍕","cuisine":"Multi-Cuisine Veg","type":"veg",
        "area":"Nungambakkam","lat":13.0620,"lng":80.2430,
        "address":"7, Khader Nawaz Khan Rd, Nungambakkam","phone":"+91 44 28331234",
        "rating":4.3,"reviews":1560,"delivery_time":"30-45 min",
        "delivery_charge":35,"min_order":250,"timing":"12 PM – 11 PM","subscription":"active",
        "menu":{
            "Starters":{
                "Veg Spring Rolls":     {"price":180,"veg":True},
                "Paneer Tikka":         {"price":260,"veg":True},
            },
            "Mains":{
                "Paneer Butter Masala": {"price":280,"veg":True},
                "Pasta Arrabiata":      {"price":240,"veg":True},
                "Mexican Rice Bowl":    {"price":260,"veg":True},
            },
            "Pizza":{
                "Margherita Pizza":     {"price":260,"veg":True},
                "Veggie Supreme Pizza": {"price":320,"veg":True},
            },
            "Desserts":{
                "Hot Chocolate Fudge":  {"price":220,"veg":True},
                "Brownie Sundae":       {"price":200,"veg":True},
            }
        },
        "offers":{
            "PIZZA20":{"type":"percent","discount":20,"min":300,"desc":"20% off on pizza"},
        },
        "delivery_partners":[
            {"name":"Vinoth S","phone":"+91 9876500008","rating":4.8},
        ]
    },
    "kaaraikudi":{
        "name":"Kaaraikudi Chettinad","emoji":"🍛","cuisine":"Authentic Chettinad","type":"nonveg",
        "area":"Velachery","lat":12.9788,"lng":80.2204,
        "address":"45, 100 Ft Rd, Velachery","phone":"+91 98412 00000",
        "rating":4.6,"reviews":980,"delivery_time":"30-45 min",
        "delivery_charge":35,"min_order":250,"timing":"11 AM – 10:30 PM","subscription":"active",
        "menu":{
            "Biryani":{
                "Kaaraikudi Mutton Biryani":{"price":400,"veg":False},
                "Chicken Biryani":           {"price":280,"veg":False},
            },
            "Specials":{
                "Chettinad Fish Fry":        {"price":320,"veg":False},
                "Chicken Kuzhambu":          {"price":300,"veg":False},
                "Quail (Kaadai) Fry":        {"price":380,"veg":False},
            },
        },
        "offers":{
            "KAAR10":{"type":"percent","discount":10,"min":300,"desc":"10% off ₹300+"},
        },
        "delivery_partners":[
            {"name":"Balu K","phone":"+91 9876500009","rating":4.7},
        ]
    },
    "bombay_bakery":{
        "name":"Bombay Bakery & Café","emoji":"🥐","cuisine":"Bakery, Snacks & Chai","type":"veg",
        "area":"Adyar","lat":13.0063,"lng":80.2574,
        "address":"12, LB Rd, Adyar","phone":"+91 98400 11111",
        "rating":4.5,"reviews":710,"delivery_time":"15-25 min",
        "delivery_charge":20,"min_order":80,"timing":"7 AM – 10 PM","subscription":"active",
        "menu":{
            "Bakery":{
                "Veg Puff":           {"price":35, "veg":True},
                "Egg Puff":           {"price":40, "veg":False},
                "Croissant":          {"price":60, "veg":True},
                "Samosa (2 pcs)":     {"price":50, "veg":True},
                "Bread Toast":        {"price":45, "veg":True},
            },
            "Café":{
                "Masala Chai":        {"price":40, "veg":True},
                "Cold Coffee":        {"price":80, "veg":True},
            },
            "Sweets":{
                "Gulab Jamun (2 pcs)":{"price":60, "veg":True},
                "Carrot Halwa":       {"price":80, "veg":True},
            }
        },
        "offers":{
            "CHAI5":{"type":"flat","discount":20,"min":100,"desc":"₹20 off on ₹100+"},
        },
        "delivery_partners":[
            {"name":"Suresh A","phone":"+91 9876500010","rating":4.9},
        ]
    },
    "seafood_bay":{
        "name":"Chennai Seafood Bay","emoji":"🦐","cuisine":"Coastal Seafood","type":"nonveg",
        "area":"Besant Nagar","lat":13.0002,"lng":80.2698,
        "address":"18, 4th Ave, Besant Nagar","phone":"+91 98765 22222",
        "rating":4.7,"reviews":1240,"delivery_time":"35-50 min",
        "delivery_charge":50,"min_order":400,"timing":"12 PM – 11 PM","subscription":"active",
        "menu":{
            "Starters":{
                "Prawn Masala Fry":       {"price":380,"veg":False},
                "Fish Fingers":           {"price":280,"veg":False},
                "Squid Pepper Fry":       {"price":360,"veg":False},
            },
            "Mains":{
                "Prawn Biryani":          {"price":440,"veg":False},
                "Fish Curry with Rice":   {"price":320,"veg":False},
                "Mixed Seafood Rice Bowl":{"price":420,"veg":False},
            },
        },
        "offers":{
            "SEAFRESH":{"type":"percent","discount":12,"min":500,"desc":"12% off ₹500+"},
            "FREESHIP": {"type":"delivery","discount":50,"min":600,"desc":"Free delivery ₹600+"},
        },
        "delivery_partners":[
            {"name":"Fisher K","phone":"+91 9876500011","rating":4.6},
            {"name":"Mohan G", "phone":"+91 9876500012","rating":4.8},
        ]
    },
}

# ════════════════════════════════════════════════════════════════════════════
#  IN-MEMORY STATE
# ════════════════════════════════════════════════════════════════════════════
sessions   = {}   # sender → GPT chat history
user_state = {}   # sender → full state dict
orders     = {}
payouts    = {}


# ════════════════════════════════════════════════════════════════════════════
#  GEO UTILITIES
# ════════════════════════════════════════════════════════════════════════════
def haversine(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def latlong_to_zone(lat, lng):
    best, best_dist = None, 9999
    for key, (zlat, zlng, zname) in CHENNAI_ZONES.items():
        d = haversine(lat, lng, zlat, zlng)
        if d < best_dist:
            best_dist, best = d, zname
    return best or "Chennai"

def text_to_zone(text):
    t = text.lower().strip()
    for key, (zlat, zlng, zname) in CHENNAI_ZONES.items():
        if key in t or t in key:
            return zname, zlat, zlng
    return None

def restaurants_near(lat, lng, limit=8, radius_km=None):
    """Return active restaurants sorted by distance, optionally filtered to radius_km."""
    active = [(rid, r) for rid, r in RESTAURANTS.items() if r.get("subscription") == "active"]
    with_dist = []
    for rid, r in active:
        d = haversine(lat, lng, r["lat"], r["lng"])
        if radius_km is None or d <= radius_km:
            with_dist.append((d, rid, r))
    with_dist.sort(key=lambda x: x[0])
    return with_dist[:limit]


# ════════════════════════════════════════════════════════════════════════════
#  TIME-AWARE PROACTIVE AI
# ════════════════════════════════════════════════════════════════════════════
def time_greeting():
    hour = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).hour
    if 5 <= hour < 12:
        return "Good morning! ☀️", "breakfast", ["idly","vada","dosa","pongal","chai"]
    elif 12 <= hour < 15:
        return "Good afternoon! 🌤️", "lunch", ["biryani","meals","chicken","fish","rice"]
    elif 15 <= hour < 18:
        return "Good evening! ☕", "snacks", ["puff","chai","samosa","coffee","sweets"]
    elif 18 <= hour < 22:
        return "Good evening! 🌆", "dinner", ["biryani","chicken","mutton","seafood","pizza"]
    else:
        return "Hey night owl! 🌙", "late night", ["biryani","chicken","pizza","kebab"]


# ════════════════════════════════════════════════════════════════════════════
#  ✨ NEW: VOICE COMMAND PARSER
#  Parses natural language like:
#    "2 idly 1 vada"
#    "chicken biryani 2 chicken 65 1"
#    "3 masala dosa"
#    "biryani"   → qty 1
# ════════════════════════════════════════════════════════════════════════════
def parse_voice_order(text, r):
    """
    Returns list of (item_name, price, qty) tuples matched from r's menu.
    Handles:
      - leading qty: "2 idly 1 vada"
      - trailing qty: "chicken biryani 2"
      - no qty: "biryani" → 1
    """
    # Build flat item list sorted longest-name-first (greedy match)
    all_items = {}
    for cat, items in r["menu"].items():
        for item_name, d in items.items():
            all_items[item_name.lower()] = (item_name, d["price"])
    sorted_items = sorted(all_items.keys(), key=lambda x: -len(x))

    remaining = text.lower()
    found = []
    used_spans = []

    for item_lower in sorted_items:
        idx = remaining.find(item_lower)
        if idx == -1:
            continue
        # Check not already matched
        end = idx + len(item_lower)
        overlap = any(s <= idx < e or s < end <= e for s, e in used_spans)
        if overlap:
            continue

        # Look for qty before or after the item
        qty = 1
        before = remaining[:idx].strip()
        after  = remaining[end:].strip()

        m_before = re.search(r'(\d+)\s*$', before)
        m_after  = re.match(r'^\s*(\d+)', after)
        if m_before:
            qty = int(m_before.group(1))
        elif m_after:
            qty = int(m_after.group(1))

        item_name, price = all_items[item_lower]
        found.append((item_name, price, max(1, min(qty, 20))))
        used_spans.append((idx, end))

    return found


def is_voice_order(text, r):
    """
    Returns True if text looks like a voice order (contains menu item names).
    Used to distinguish "2 idly 1 vada" from a generic message.
    """
    lower = text.lower()
    for cat, items in r["menu"].items():
        for item_name in items:
            if item_name.lower() in lower:
                return True
    # Also check food keyword aliases
    VOICE_KEYWORDS = ["idly","idli","dosa","vada","biryani","biriyani","chicken","mutton",
                      "fish","prawn","pizza","puff","chai","coffee","rice","meals"]
    for kw in VOICE_KEYWORDS:
        if kw in lower:
            return True
    return False


# ════════════════════════════════════════════════════════════════════════════
#  FOOD SEARCH (with 4 km radius)
# ════════════════════════════════════════════════════════════════════════════
FOOD_ALIASES = {
    "biriyani":"biryani","briyani":"biryani",
    "dosai":"dosa","thosai":"dosa",
    "idli":"idly","idlies":"idly",
    "prawns":"prawn","shrimp":"prawn",
    "c65":"chicken 65","coffee":"cold coffee",
    "vada":"vada","vadai":"vada",
}

def search_food(query, filter_type=None, user_lat=None, user_lng=None, radius_km=NEARBY_RADIUS_KM):
    """Search restaurants by food name. Filters to radius_km if location known."""
    q = FOOD_ALIASES.get(query.lower(), query.lower())
    results = []
    for rid, r in RESTAURANTS.items():
        if r.get("subscription") != "active":
            continue
        if filter_type == "veg"    and r["type"] not in ["veg","both"]:
            continue
        if filter_type == "nonveg" and r["type"] not in ["nonveg","both"]:
            continue

        dist = haversine(user_lat, user_lng, r["lat"], r["lng"]) if user_lat else None

        # 4 km radius filter when location is known
        if dist is not None and dist > radius_km:
            continue

        matched = []
        for cat, items in r["menu"].items():
            for item, d in items.items():
                if q in item.lower() or any(w in item.lower() for w in q.split()):
                    matched.append(f"{item} ₹{d['price']}")
        if matched:
            results.append((dist, rid, r, matched[:3]))

    if user_lat:
        results.sort(key=lambda x: x[0] if x[0] is not None else 9999)
    return results


# ════════════════════════════════════════════════════════════════════════════
#  CART CRUD HELPERS
# ════════════════════════════════════════════════════════════════════════════
def cart_subtotal(cart):
    return sum(d["price"] * d["qty"] for d in cart.values())

def show_cart(r, cart, coupon_discount=0):
    """Full cart display with CRUD instructions."""
    sub   = cart_subtotal(cart)
    total = sub + r["delivery_charge"] - coupon_discount

    t  = f"🛒 *Your Cart — {r['name']}*\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"

    if not cart:
        t += "_Cart is empty. Add items from the menu._\n"
    else:
        for i, (item, d) in enumerate(cart.items(), 1):
            t += f"{i}. {item} × {d['qty']} = ₹{d['price'] * d['qty']}\n"

    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    t += f"Subtotal:  ₹{sub}\n"
    t += f"Delivery:  ₹{r['delivery_charge']}\n"
    if coupon_discount:
        t += f"Discount: -₹{coupon_discount}\n"
    t += f"*Total:    ₹{total}*\n\n"

    # Minimum order check
    if sub < MIN_ORDER_GLOBAL:
        shortage = MIN_ORDER_GLOBAL - sub
        t += f"⚠️ Min order is ₹{MIN_ORDER_GLOBAL}. Add ₹{shortage} more to checkout.\n\n"
    elif sub < r["min_order"]:
        shortage = r["min_order"] - sub
        t += f"⚠️ {r['name']} requires min ₹{r['min_order']}. Add ₹{shortage} more.\n\n"

    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    t += "*Cart actions:*\n"
    t += "• *checkout* — place order\n"
    t += "• *remove Idly* — remove item\n"
    t += "• *update Idly 3* — set new quantity\n"
    t += "• *clear* — empty cart\n"
    t += "• *coupon CODE* — apply discount\n"
    t += "• *more* — back to menu"
    return t

def apply_coupon(r, code, subtotal):
    offers = r.get("offers", {})
    code   = code.upper().strip()
    o = offers.get(code)
    if not o:
        return None, f"❌ Coupon *{code}* not found. Type *offers* to see valid codes."
    if subtotal < o["min"]:
        return None, f"❌ Min order ₹{o['min']} needed. Current subtotal: ₹{subtotal}."
    if o["type"] == "percent":
        d = int(subtotal * o["discount"] / 100)
        return d, f"✅ *{code}* applied! {o['discount']}% off = ₹{d} saved 🎉"
    if o["type"] == "flat":
        return o["discount"], f"✅ *{code}* applied! ₹{o['discount']} off 🎉"
    if o["type"] == "delivery":
        return r["delivery_charge"], f"✅ *{code}* applied! Free delivery 🎉"
    return None, "❌ Invalid coupon."

def find_item_in_cart(query, cart):
    """Fuzzy match a query string to a cart item name."""
    q = query.lower().strip()
    for item in cart:
        if q in item.lower() or item.lower() in q:
            return item
    return None

def find_item_in_menu(query, r):
    """Fuzzy match query to a menu item. Returns (item_name, price) or None."""
    q = query.lower().strip()
    best = None
    for cat, items in r["menu"].items():
        for item_name, d in items.items():
            if q in item_name.lower() or item_name.lower() in q:
                if best is None or len(item_name) < len(best[0]):
                    best = (item_name, d["price"])
    return best


# ════════════════════════════════════════════════════════════════════════════
#  MESSAGE BUILDERS
# ════════════════════════════════════════════════════════════════════════════
def welcome_msg(zone=None):
    greeting, meal, foods = time_greeting()
    area_tag = f" | 📍 {zone}" if zone else ""
    suggestions = " | ".join([f"_{f}_" for f in foods[:4]])
    total = len([r for r in RESTAURANTS.values() if r.get("subscription") == "active"])
    return (
        f"👋 *Welcome to FoodieBot Chennai!* 🍽️{area_tag}\n"
        f"_Powered by NexoraAI — SuperBot v4_\n\n"
        f"{greeting} Time for *{meal}*!\n"
        f"Try: {suggestions}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 *Share your location* — see restaurants within *4 km*!\n"
        f"_(tap 📎 → Location)_\n\n"
        f"🎙️ *Voice ordering works too!*\n"
        f'   _"2 idly 1 vada"_ or _"chicken biryani 2"_\n\n'
        f"*Quick Commands:*\n"
        f"• *nearby* / *area T Nagar* — by location\n"
        f"• *veg* · *top* · *cheap* · *all*\n\n"
        f"_Type any food name to start!_ 😊"
    )

def location_received_msg(zone, nearby_list):
    if not nearby_list:
        return (
            f"📍 You're near *{zone}*\n\n"
            f"😕 No restaurants found within {NEARBY_RADIUS_KM} km.\n"
            f"Try: *all* to see all restaurants · *area [zone]* to search elsewhere."
        )
    t  = f"📍 You're near *{zone}* — showing within *{NEARBY_RADIUS_KM} km*\n\n"
    t += "🍽️ *Restaurants near you:*\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, (dist, rid, r) in enumerate(nearby_list, 1):
        veg_tag = "🟢" if r["type"]=="veg" else ("🔴" if r["type"]=="nonveg" else "🟡")
        t += f"{i}️⃣ {r['emoji']} *{r['name']}* {veg_tag}\n"
        t += f"   📍 {r['area']} — *{dist:.1f} km*\n"
        t += f"   ⭐ {r['rating']}/5 | 🛵 {r['delivery_time']}\n"
        t += f"   💰 Min ₹{r['min_order']} | Delivery ₹{r['delivery_charge']}\n\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    for i, (dist, rid, r) in enumerate(nearby_list, 1):
        t += f"Type *{i}* to order from {r['name']}\n"
    t += "\n_Search food (e.g. biryani) · Share location for updates_ 🔍"
    return t

def show_search_results(query, results, radius_km=NEARBY_RADIUS_KM):
    has_loc = results and results[0][0] is not None
    radius_note = f" (within {radius_km} km)" if has_loc else ""
    t  = f"🔍 *\"{query}\"* — {len(results)} restaurant(s){radius_note}\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, (dist, rid, r, matched) in enumerate(results, 1):
        veg_tag = "🟢 VEG" if r["type"]=="veg" else ("🔴 NON-VEG" if r["type"]=="nonveg" else "🟡 BOTH")
        dist_str = f" — *{dist:.1f} km*" if dist is not None else ""
        t += f"{i}️⃣ {r['emoji']} *{r['name']}* {veg_tag}\n"
        t += f"   📍 {r['area']}{dist_str} | ⭐ {r['rating']}/5\n"
        t += f"   🛵 {r['delivery_time']} | ₹{r['delivery_charge']} delivery\n"
        t += f"   🍽️ {' · '.join(matched)}\n\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    for i, (dist, rid, r, _) in enumerate(results, 1):
        t += f"Type *{i}* to order from {r['name']}\n"
    return t

def show_no_results_msg(query, zone=None, radius_km=NEARBY_RADIUS_KM):
    area_hint = f" within {radius_km} km of *{zone}*" if zone else ""
    _, meal, foods = time_greeting()
    suggest = " · ".join([f"_{f}_" for f in foods[:3]])
    return (
        f"😕 No result for *\"{query}\"*{area_hint}.\n\n"
        f"Popular *{meal}* picks: {suggest}\n\n"
        f"Or try: *all* to see all restaurants · *area [zone]* to search wider"
    )

def show_all_restaurants_nearby(user_lat=None, user_lng=None, zone=None, radius_km=NEARBY_RADIUS_KM):
    if user_lat:
        nearby = restaurants_near(user_lat, user_lng, limit=20, radius_km=radius_km)
    else:
        nearby = [(None, rid, r) for rid, r in RESTAURANTS.items() if r.get("subscription")=="active"]

    zone_note = f" near *{zone}* within {radius_km} km" if zone else " (all Chennai)"
    t = f"🍽️ *FoodieBot Restaurants*{zone_note}\n"
    t += f"_{len(nearby)} found_\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"

    if not nearby:
        t += f"No restaurants within {radius_km} km. Type *area [zone]* or share location.\n"
        return t, []

    for i, (dist, rid, r) in enumerate(nearby, 1):
        veg_tag = "🟢" if r["type"]=="veg" else ("🔴" if r["type"]=="nonveg" else "🟡")
        dist_str = f" | *{dist:.1f} km*" if dist is not None else ""
        t += f"{i}️⃣ {r['emoji']} *{r['name']}* {veg_tag}\n"
        t += f"   📍 {r['area']}{dist_str} | ⭐ {r['rating']}/5\n"
        t += f"   🛵 {r['delivery_time']} | Min ₹{r['min_order']}\n\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    for i, (dist, rid, r) in enumerate(nearby, 1):
        t += f"Type *{i}* to order from {r['name']}\n"
    return t, nearby

def show_restaurant_home(r):
    t  = f"{r['emoji']} *{r['name']}*\n"
    t += f"🍽️ {r['cuisine']}\n"
    t += f"📍 {r['address']}\n"
    t += f"⭐ {r['rating']}/5 ({r['reviews']} reviews)\n"
    t += f"🛵 {r['delivery_time']} | ₹{r['delivery_charge']} delivery | Min ₹{r['min_order']}\n"
    t += f"⏰ {r['timing']}\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for cat, items in r["menu"].items():
        t += f"*{cat}*\n"
        for item, d in items.items():
            tag = "🟢" if d.get("veg") else "🔴"
            t += f"  {tag} {item} — ₹{d['price']}\n"
        t += "\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    t += "🎙️ *Voice order:* _2 idly 1 vada_\n"
    t += "_Or type item names manually_\n\n"
    offers = r.get("offers", {})
    if offers:
        t += "🎁 *Offers:* "
        t += " | ".join([f"*{c}* — {o['desc']}" for c, o in offers.items()])
    return t

def upi_payment_msg(total, r):
    gpay   = f"gpay://upi/pay?pa={PLATFORM['upi']}&pn=FoodieBot&am={total}&cu=INR"
    phonpe = f"phonepe://pay?pa={PLATFORM['upi']}&pn=FoodieBot&am={total}&cu=INR"
    return (
        f"💳 *Payment — ₹{total}*\n\n"
        f"Pay to: *{PLATFORM['upi']}*\nAmount: *₹{total}*\n\n"
        f"📱 Quick Pay:\nGPay: {gpay}\nPhonePe: {phonpe}\n\n"
        f"Type *paid* — UPI done\nType *cod* — Cash on Delivery"
    )

def order_confirmation(oid, r, name, total, payment_type, partner):
    t  = "━━━━━━━━━━━━━━━━━━━━━━\n✅ *Order Confirmed!*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    t += f"Order ID: *{oid}*\nRestaurant: *{r['name']}*\n"
    t += f"Customer: {name}\nAmount: ₹{total}\nPayment: {payment_type}\n\n"
    t += f"🛵 *Delivery Partner:*\n   {partner['name']} | {partner['phone']} | ⭐{partner['rating']}\n\n"
    t += f"⏱️ {r['delivery_time']}\n"
    t += f"📞 Help: {PLATFORM['phone']}\nThank you! 🍛❤️"
    return t

def ask_gpt(r, sender, text):
    if not OPENAI_KEY:
        return f"Please call us: {r['phone']} 📞"
    sessions.setdefault(sender, [])
    sessions[sender].append({"role":"user","content":text})
    if len(sessions[sender]) > 20:
        sessions[sender] = sessions[sender][-20:]
    menu_str = ", ".join([f"{item} ₹{d['price']}" for cat, its in r["menu"].items() for item, d in its.items()])
    system = (
        f"You are FoodieBot Chennai assistant for {r['name']}. "
        f"MENU: {menu_str}. Be friendly, use emojis, reply concisely. "
        f"Suggest combos. Platform UPI: {PLATFORM['upi']}."
    )
    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization":f"Bearer {OPENAI_KEY}","Content-Type":"application/json"},
            json={"model":"gpt-4o-mini","messages":[{"role":"system","content":system}]+sessions[sender],"max_tokens":300},
            timeout=10
        )
        reply = resp.json()["choices"][0]["message"]["content"]
        sessions[sender].append({"role":"assistant","content":reply})
        return reply
    except Exception:
        return f"Sorry, call us: {r['phone']} 📞"


# ════════════════════════════════════════════════════════════════════════════
#  TWILIO SENDER
# ════════════════════════════════════════════════════════════════════════════
def send_whatsapp(to, body):
    if not TWILIO_SID or not TWILIO_AUTH:
        print(f"[DRY RUN → {to}]\n{body}\n")
        return
    to_num = f"whatsapp:{to}" if not to.startswith("whatsapp:") else to
    requests.post(
        f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json",
        auth=(TWILIO_SID, TWILIO_AUTH),
        data={"From": TWILIO_FROM, "To": to_num, "Body": body}
    )


# ════════════════════════════════════════════════════════════════════════════
#  CORE MESSAGE HANDLER
# ════════════════════════════════════════════════════════════════════════════
def handle_message(sender, body, latitude=None, longitude=None):
    text  = (body or "").strip()
    lower = text.lower()
    now   = time.time()

    state = user_state.setdefault(sender, {
        "step":"home","cart":{},"restaurant":None,
        "name":None,"address":None,"coupon_discount":0,
        "search_results":[],"location_lat":None,"location_lng":None,
        "zone":None,"order_total":0,"last_active":now
    })
    state["last_active"] = now

    # ── LOCATION PIN ──────────────────────────────────────────────────────────
    if latitude is not None and longitude is not None:
        lat, lng = float(latitude), float(longitude)
        state["location_lat"] = lat
        state["location_lng"] = lng
        zone = latlong_to_zone(lat, lng)
        state["zone"] = zone
        nearby = restaurants_near(lat, lng, limit=8, radius_km=NEARBY_RADIUS_KM)
        state["search_results"] = [(d, rid, r) for d, rid, r in nearby]
        state["step"] = "home"
        return location_received_msg(zone, nearby)

    ulat  = state.get("location_lat")
    ulng  = state.get("location_lng")
    uzone = state.get("zone")

    # ── NUMBER SELECTION (from list) ─────────────────────────────────────────
    if text.isdigit() and state["step"] in ("home","search","area_search","all_list"):
        idx = int(text) - 1
        results = state.get("search_results", [])
        if results and 0 <= idx < len(results):
            entry = results[idx]
            rid = entry[1]; r = entry[2]
            state["restaurant"] = rid
            state["cart"] = {}
            state["coupon_discount"] = 0
            state["step"] = "restaurant"
            return show_restaurant_home(r)
        return "❓ Pick a number from the list above."

    # ── RESTAURANT FLOW ───────────────────────────────────────────────────────
    if state["step"] == "restaurant" and state.get("restaurant"):
        r = RESTAURANTS[state["restaurant"]]

        # ---- CART CRUD ----

        # VIEW CART
        if lower in ("cart","view cart","my cart","show cart"):
            return show_cart(r, state["cart"], state["coupon_discount"])

        # CLEAR CART
        if lower in ("clear","clear cart","empty cart","reset cart"):
            state["cart"] = {}
            state["coupon_discount"] = 0
            return "🗑️ Cart cleared! Type items to start fresh."

        # REMOVE ITEM — "remove idly" / "delete vada" / "cancel biryani"
        m_remove = re.match(r'^(remove|delete|cancel|rm)\s+(.+)$', lower)
        if m_remove:
            query = m_remove.group(2).strip()
            matched = find_item_in_cart(query, state["cart"])
            if matched:
                del state["cart"][matched]
                return (
                    f"✅ *{matched}* removed from cart.\n\n"
                    + show_cart(r, state["cart"], state["coupon_discount"])
                )
            return f"❌ Couldn't find *{query}* in cart. Type *cart* to see items."

        # UPDATE ITEM QTY — "update idly 3" / "change vada 2" / "set biryani 1"
        m_update = re.match(r'^(update|change|set|qty)\s+(.+?)\s+(\d+)$', lower)
        if m_update:
            query = m_update.group(2).strip()
            new_qty = int(m_update.group(3))
            matched = find_item_in_cart(query, state["cart"])
            if not matched:
                # try menu
                menu_match = find_item_in_menu(query, r)
                if menu_match:
                    matched = menu_match[0]
                    state["cart"][matched] = {"price": menu_match[1], "qty": new_qty}
                    return (
                        f"✅ *{matched}* × {new_qty} added.\n\n"
                        + show_cart(r, state["cart"], state["coupon_discount"])
                    )
                return f"❌ Couldn't find *{query}* in menu or cart."
            if new_qty <= 0:
                del state["cart"][matched]
                return f"✅ *{matched}* removed (qty 0).\n\n" + show_cart(r, state["cart"], state["coupon_discount"])
            state["cart"][matched]["qty"] = new_qty
            return (
                f"✅ *{matched}* updated to × {new_qty}.\n\n"
                + show_cart(r, state["cart"], state["coupon_discount"])
            )

        # ---- CHECKOUT ----
        if lower == "checkout":
            if not state["cart"]:
                return "🛒 Cart is empty! Type item names to add."
            sub = cart_subtotal(state["cart"])
            # Global minimum ₹100
            if sub < MIN_ORDER_GLOBAL:
                shortage = MIN_ORDER_GLOBAL - sub
                return (
                    f"⚠️ *Minimum order is ₹{MIN_ORDER_GLOBAL}.*\n"
                    f"Your cart total is ₹{sub}. Add ₹{shortage} more to proceed.\n\n"
                    + show_cart(r, state["cart"], state["coupon_discount"])
                )
            # Restaurant minimum
            if sub < r["min_order"]:
                shortage = r["min_order"] - sub
                return (
                    f"⚠️ *{r['name']} requires min ₹{r['min_order']}.*\n"
                    f"Add ₹{shortage} more.\n\n"
                    + show_cart(r, state["cart"], state["coupon_discount"])
                )
            state["step"] = "get_name"
            return "📦 Almost there! Your *name* please?"

        # COUPON
        if lower.startswith("coupon ") or lower.startswith("apply "):
            code = text.split(" ", 1)[1]
            sub  = cart_subtotal(state["cart"])
            disc, msg = apply_coupon(r, code, sub)
            if disc:
                state["coupon_discount"] = disc
            return msg

        # OFFERS
        if lower in ("offers","discount","coupons"):
            offers = r.get("offers", {})
            if not offers:
                return "No active offers right now."
            t = "🎁 *Active Offers:*\n"
            for code, o in offers.items():
                t += f"  *{code}* — {o['desc']}\n"
            t += "\nType *coupon CODE* to apply."
            return t

        # BACK / MORE MENU
        if lower in ("more","back","menu","show menu"):
            return show_restaurant_home(r)

        # ---- VOICE COMMAND / ITEM ADD ----
        # Try voice order parse first (handles "2 idly 1 vada", "chicken biryani 2")
        voice_items = parse_voice_order(text, r)
        if voice_items:
            added = []
            for item_name, price, qty in voice_items:
                if item_name in state["cart"]:
                    state["cart"][item_name]["qty"] += qty
                else:
                    state["cart"][item_name] = {"price": price, "qty": qty}
                added.append(f"{item_name} × {qty}")

            sub   = cart_subtotal(state["cart"])
            total = sub + r["delivery_charge"] - state["coupon_discount"]
            t  = f"🎙️ *Voice order got it!*\n"
            t += f"✅ Added: {', '.join(added)}\n\n"
            t += f"🛒 Cart: ₹{total} ({len(state['cart'])} item(s))\n"

            if sub < MIN_ORDER_GLOBAL:
                t += f"⚠️ Need ₹{MIN_ORDER_GLOBAL - sub} more for min order.\n"

            t += "\nType *cart* · *checkout* · add more items"
            return t

        # GPT fallback
        return ask_gpt(r, sender, text)

    # ── ORDER FLOW ───────────────────────────────────────────────────────────
    if state["step"] == "get_name":
        state["name"] = text
        state["step"] = "get_address"
        hint = f"\n_(Near {uzone} — confirm or update)_" if uzone else ""
        return f"🏠 Thanks *{text}*! Delivery address?{hint}"

    if state["step"] == "get_address":
        state["address"] = text
        if not uzone:
            match = text_to_zone(text)
            if match:
                state["zone"] = match[0]
                state["location_lat"] = match[1]
                state["location_lng"] = match[2]
        r   = RESTAURANTS[state["restaurant"]]
        sub = cart_subtotal(state["cart"])
        tot = sub + r["delivery_charge"] - state["coupon_discount"]
        state["order_total"] = tot
        state["step"] = "payment"
        return upi_payment_msg(tot, r)

    if state["step"] == "payment":
        if lower in ("paid","done","upi done","gpay","phonepay","phonepe"):
            payment_type = "UPI"
        elif lower in ("cod","cash","cash on delivery"):
            payment_type = "COD"
        else:
            return "💳 Type *paid* after UPI or *cod* for Cash on Delivery."

        r = RESTAURANTS[state["restaurant"]]
        partner = random.choice(r["delivery_partners"])
        oid = "FB" + str(uuid.uuid4())[:6].upper()
        total = state.get("order_total", 0)

        orders[oid] = {
            "restaurant":state["restaurant"],"name":state["name"],
            "address":state["address"],"cart":state["cart"].copy(),
            "total":total,"payment":payment_type,"partner":partner,
            "time":datetime.datetime.now().isoformat(),"sender":sender
        }
        comm = int(total * PLATFORM["commission"])
        payouts[state["restaurant"]] = payouts.get(state["restaurant"], 0) + (total - comm)

        msg = order_confirmation(oid, r, state["name"], total, payment_type, partner)

        # Reset
        state.update({"step":"home","cart":{},"restaurant":None,
                      "coupon_discount":0,"search_results":[]})
        return msg

    # ── HOME COMMANDS ─────────────────────────────────────────────────────────
    if lower in ("hi","hello","hey","start","hii","help","menu"):
        return welcome_msg(uzone)

    if lower in ("nearby","near me","closest"):
        if ulat:
            nearby = restaurants_near(ulat, ulng, limit=8, radius_km=NEARBY_RADIUS_KM)
            state["search_results"] = [(d, rid, r) for d, rid, r in nearby]
            state["step"] = "home"
            return location_received_msg(uzone or "your area", nearby)
        return "📍 Share your WhatsApp location first!\n_(tap 📎 → Location)_\n\nOr: *area T Nagar* / *area Adyar*"

    if lower.startswith("area "):
        area_query = text[5:].strip()
        match = text_to_zone(area_query)
        if match:
            zname, zlat, zlng = match
            state.update({"zone":zname,"location_lat":zlat,"location_lng":zlng})
            nearby = restaurants_near(zlat, zlng, limit=8, radius_km=NEARBY_RADIUS_KM)
            state["search_results"] = [(d, rid, r) for d, rid, r in nearby]
            state["step"] = "area_search"
            return location_received_msg(zname, nearby)
        return f"😕 Couldn't find *{area_query}* in Chennai. Try: T Nagar, Adyar, Velachery, Anna Nagar, OMR…"

    if lower == "all":
        msg, nearby = show_all_restaurants_nearby(ulat, ulng, uzone,
                                                   radius_km=NEARBY_RADIUS_KM if ulat else None)
        state["search_results"] = [(d, rid, r) for d, rid, r in nearby]
        state["step"] = "all_list"
        return msg

    if lower in ("veg","vegetarian","veg only"):
        veg = [(haversine(ulat, ulng, r["lat"], r["lng"]) if ulat else 0, rid, r)
               for rid, r in RESTAURANTS.items()
               if r.get("subscription")=="active" and r["type"] in ("veg","both")
               and (ulat is None or haversine(ulat, ulng, r["lat"], r["lng"]) <= NEARBY_RADIUS_KM)]
        if ulat:
            veg.sort(key=lambda x: x[0])
        state["search_results"] = veg
        state["step"] = "home"
        if not veg:
            return f"No veg restaurants within {NEARBY_RADIUS_KM} km. Type *area [zone]* to search elsewhere."
        t = f"🟢 *Veg Restaurants* (within {NEARBY_RADIUS_KM} km)\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, (dist, rid, r) in enumerate(veg, 1):
            ds = f" | {dist:.1f} km" if ulat else ""
            t += f"{i}️⃣ {r['emoji']} *{r['name']}*{ds} | ⭐{r['rating']}/5\n   📍 {r['area']}\n\n"
        t += "━━━━━━━━━━━━━━━━━━━━━━\n"
        for i, (_, rid, r) in enumerate(veg, 1):
            t += f"Type *{i}* to order from {r['name']}\n"
        return t

    if lower in ("top","best","top rated"):
        ranked = sorted(
            [(rid, r) for rid, r in RESTAURANTS.items() if r.get("subscription")=="active"],
            key=lambda x: x[1]["rating"], reverse=True
        )
        state["search_results"] = [(0, rid, r) for rid, r in ranked]
        state["step"] = "home"
        t = "⭐ *Top Rated Restaurants*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, (rid, r) in enumerate(ranked, 1):
            t += f"{i}️⃣ {r['emoji']} *{r['name']}* — ⭐{r['rating']}/5\n   📍 {r['area']} | {r['cuisine']}\n\n"
        t += "━━━━━━━━━━━━━━━━━━━━━━\n"
        for i, (rid, r) in enumerate(ranked, 1):
            t += f"Type *{i}* to order from {r['name']}\n"
        return t

    if lower in ("cheap","budget"):
        cheap = sorted(
            [(rid, r) for rid, r in RESTAURANTS.items() if r.get("subscription")=="active"],
            key=lambda x: x[1]["min_order"]
        )
        state["search_results"] = [(0, rid, r) for rid, r in cheap]
        state["step"] = "home"
        t = "💰 *Budget Restaurants*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, (rid, r) in enumerate(cheap, 1):
            t += f"{i}️⃣ {r['emoji']} *{r['name']}* — Min ₹{r['min_order']}\n   📍 {r['area']}\n\n"
        t += "━━━━━━━━━━━━━━━━━━━━━━\n"
        for i, (rid, r) in enumerate(cheap, 1):
            t += f"Type *{i}* to order from {r['name']}\n"
        return t

    if lower.startswith("review"):
        return "⭐ Share your review:\nhttps://g.page/foodiebot-chennai\n_Thank you!_ 🙏"

    if lower in ("","?"):
        _, meal, foods = time_greeting()
        suggest = " · ".join([f"_{f}_" for f in foods[:4]])
        return f"🔥 Popular *{meal}* picks: {suggest}\n\nType a food name or *menu* to explore!"

    # ── DEFAULT: FOOD SEARCH ─────────────────────────────────────────────────
    results = search_food(lower, user_lat=ulat, user_lng=ulng, radius_km=NEARBY_RADIUS_KM)
    if results:
        state["search_results"] = results
        state["step"] = "search"
        return show_search_results(lower, results)
    return show_no_results_msg(lower, uzone)


# ════════════════════════════════════════════════════════════════════════════
#  WEBHOOK
# ════════════════════════════════════════════════════════════════════════════
@app.route("/webhook", methods=["GET","POST"])
def webhook():
    if request.method == "GET":
        return "FoodieBot SuperBot v4 is live! 🚀", 200
    sender    = request.form.get("From","").replace("whatsapp:","")
    body      = request.form.get("Body","").strip()
    latitude  = request.form.get("Latitude")
    longitude = request.form.get("Longitude")
    if not sender:
        return jsonify({"status":"no sender"}), 400
    reply = handle_message(sender, body, latitude, longitude)
    send_whatsapp(sender, reply)
    return jsonify({"status":"ok"}), 200


# ════════════════════════════════════════════════════════════════════════════
#  ADMIN APIs
# ════════════════════════════════════════════════════════════════════════════
def auth():
    return request.args.get("key") == ADMIN_KEY

@app.route("/admin/orders")
def admin_orders():
    if not auth(): return jsonify({"error":"unauthorized"}),401
    return jsonify({"total":len(orders),"orders":orders})

@app.route("/admin/stats")
def admin_stats():
    if not auth(): return jsonify({"error":"unauthorized"}),401
    rev = sum(o["total"] for o in orders.values())
    return jsonify({
        "total_orders":len(orders),"total_revenue":rev,
        "commission":int(rev*PLATFORM["commission"]),
        "restaurants":len([r for r in RESTAURANTS.values() if r.get("subscription")=="active"]),
        "sessions":len(user_state)
    })

@app.route("/admin/payouts")
def admin_payouts():
    if not auth(): return jsonify({"error":"unauthorized"}),401
    return jsonify({"payouts":payouts})

@app.route("/admin/broadcast")
def admin_broadcast():
    if not auth(): return jsonify({"error":"unauthorized"}),401
    _, meal, foods = time_greeting()
    suggest = " · ".join([f"{f}" for f in foods[:3]])
    count = 0
    for sender, state in user_state.items():
        if time.time() - state.get("last_active",0) < 86400:
            send_whatsapp(sender, f"🔥 Craving something for {meal}? Try: {suggest}\n\nReply to order!")
            count += 1
    return jsonify({"broadcast_sent":count})

@app.route("/health")
def health():
    return jsonify({"status":"ok","version":"SuperBot v4.0",
                    "restaurants":len(RESTAURANTS),"radius_km":NEARBY_RADIUS_KM,
                    "min_order_floor":MIN_ORDER_GLOBAL})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
