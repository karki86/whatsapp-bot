"""
FoodieBot Chennai — SuperBot v3.0
NexoraAI | nexoraaiagen@gmail.com | +91 7010624989
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEW in v3 (SuperBot):
  ✅ WhatsApp Location Pin detection (lat/lng → Chennai zone)
  ✅ Auto-detect area from any typed address / landmark
  ✅ Nearby restaurants ranked by distance
  ✅ Proactive AI: greets by time-of-day, suggests meals, upsells
  ✅ Re-engagement nudges after 30 min inactivity
  ✅ Smart suggestions if search returns 0 results
  ✅ Full order flow preserved from v2
"""

import os, json, math, time, uuid, random, datetime
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ════════════════════════════════════════════════════════════════════════════
#  ENV
# ════════════════════════════════════════════════════════════════════════════
TWILIO_SID      = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH     = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM     = os.environ.get("TWILIO_FROM", "whatsapp:+14155238886")  # sandbox
OPENAI_KEY      = os.environ.get("OPENAI_API_KEY", "")
ADMIN_KEY       = os.environ.get("ADMIN_KEY", "NEXORAAI2026")

PLATFORM = {
    "name":    "FoodieBot Chennai",
    "upi":     "nexoraai@upi",
    "phone":   "+91 7010624989",
    "powered": "NexoraAI",
    "commission": 0.10
}

# ════════════════════════════════════════════════════════════════════════════
#  CHENNAI ZONE MAP
#  Every major landmark / area mapped to (lat, lng, canonical_zone_name)
# ════════════════════════════════════════════════════════════════════════════
CHENNAI_ZONES = {
    # North
    "tiruvottiyur":      (13.1670, 80.3020, "Tiruvottiyur"),
    "manali":            (13.1680, 80.2620, "Manali"),
    "madhavaram":        (13.1490, 80.2290, "Madhavaram"),
    "kolathur":          (13.1190, 80.2200, "Kolathur"),
    "perambur":          (13.1140, 80.2460, "Perambur"),
    "vyasarpadi":        (13.1060, 80.2490, "Vyasarpadi"),
    "tondiarpet":        (13.1090, 80.2810, "Tondiarpet"),
    "royapuram":         (13.1080, 80.2930, "Royapuram"),
    "korukupet":         (13.1010, 80.2920, "Korukupet"),
    # Central
    "egmore":            (13.0790, 80.2610, "Egmore"),
    "park town":         (13.0810, 80.2750, "Park Town"),
    "central":           (13.0827, 80.2707, "Chennai Central"),
    "chennai central":   (13.0827, 80.2707, "Chennai Central"),
    "choolai":           (13.0920, 80.2580, "Choolai"),
    "aminjikarai":       (13.0890, 80.2370, "Aminjikarai"),
    "kilpauk":           (13.0890, 80.2420, "Kilpauk"),
    "chetpet":           (13.0800, 80.2450, "Chetpet"),
    "purasaiwakkam":     (13.0850, 80.2480, "Purasaiwakkam"),
    "vepery":            (13.0860, 80.2620, "Vepery"),
    "sowcarpet":         (13.0900, 80.2740, "Sowcarpet"),
    "parrys":            (13.0920, 80.2820, "Parrys Corner"),
    "george town":       (13.0940, 80.2880, "George Town"),
    # South-Central
    "t nagar":           (13.0418, 80.2341, "T Nagar"),
    "tnagar":            (13.0418, 80.2341, "T Nagar"),
    "pondy bazaar":      (13.0418, 80.2341, "T Nagar"),
    "kodambakkam":       (13.0530, 80.2220, "Kodambakkam"),
    "ashok nagar":       (13.0370, 80.2120, "Ashok Nagar"),
    "vadapalani":        (13.0530, 80.2130, "Vadapalani"),
    "koyambedu":         (13.0720, 80.1950, "Koyambedu"),
    "arumbakkam":        (13.0720, 80.2130, "Arumbakkam"),
    "virugambakkam":     (13.0550, 80.1940, "Virugambakkam"),
    "valasaravakkam":    (13.0370, 80.1760, "Valasaravakkam"),
    "saligramam":        (13.0470, 80.1870, "Saligramam"),
    "anna nagar":        (13.0850, 80.2100, "Anna Nagar"),
    "anna nagar east":   (13.0840, 80.2200, "Anna Nagar East"),
    # South
    "mylapore":          (13.0340, 80.2690, "Mylapore"),
    "mandaveli":         (13.0270, 80.2650, "Mandaveli"),
    "royapettah":        (13.0530, 80.2610, "Royapettah"),
    "nungambakkam":      (13.0620, 80.2430, "Nungambakkam"),
    "alwarpet":          (13.0380, 80.2540, "Alwarpet"),
    "teynampet":         (13.0400, 80.2490, "Teynampet"),
    "gopalapuram":       (13.0420, 80.2570, "Gopalapuram"),
    "abhiramapuram":     (13.0400, 80.2620, "Abhiramapuram"),
    "boat club":         (13.0290, 80.2550, "Boat Club"),
    "adyar":             (13.0063, 80.2574, "Adyar"),
    "kotturpuram":       (13.0150, 80.2470, "Kotturpuram"),
    "thiruvanmiyur":     (12.9839, 80.2592, "Thiruvanmiyur"),
    "besant nagar":      (13.0002, 80.2698, "Besant Nagar"),
    "elliot's beach":    (13.0002, 80.2698, "Besant Nagar"),
    "neelankarai":       (12.9520, 80.2527, "Neelankarai"),
    "palavakkam":        (12.9450, 80.2500, "Palavakkam"),
    "sholinganallur":    (12.9010, 80.2278, "Sholinganallur"),
    "perungudi":         (12.9650, 80.2430, "Perungudi"),
    "taramani":          (12.9850, 80.2400, "Taramani"),
    "velachery":         (12.9788, 80.2204, "Velachery"),
    "nanganallur":       (12.9950, 80.1970, "Nanganallur"),
    "pallikaranai":      (12.9370, 80.2040, "Pallikaranai"),
    "chromepet":         (12.9516, 80.1426, "Chromepet"),
    "tambaram":          (12.9249, 80.1000, "Tambaram"),
    # West & IT Corridor
    "guindy":            (13.0067, 80.2206, "Guindy"),
    "ekkatuthangal":     (13.0160, 80.2070, "Ekkatuthangal"),
    "saidapet":          (13.0220, 80.2290, "Saidapet"),
    "little mount":      (13.0200, 80.2230, "Little Mount"),
    "maduravoyil":       (13.0590, 80.1780, "Maduravoyil"),
    "porur":             (13.0370, 80.1570, "Porur"),
    "poonamallee":       (13.0480, 80.0970, "Poonamallee"),
    "ambattur":          (13.1140, 80.1620, "Ambattur"),
    "avadi":             (13.1150, 80.0980, "Avadi"),
    "mogappair":         (13.0930, 80.1680, "Mogappair"),
    "padi":              (13.1080, 80.1990, "Padi"),
    # OMR / IT
    "omr":               (12.9010, 80.2278, "OMR"),
    "perungalathur":     (12.8720, 80.0900, "Perungalathur"),
    "siruseri":          (12.8560, 80.2180, "Siruseri"),
    "navalur":           (12.8420, 80.2270, "Navalur"),
    "kelambakkam":       (12.7870, 80.2100, "Kelambakkam"),
    "mahindra city":     (12.7560, 80.0030, "Mahindra City"),
}

# ════════════════════════════════════════════════════════════════════════════
#  RESTAURANTS — expanded to 8, each with real lat/lng
# ════════════════════════════════════════════════════════════════════════════
RESTAURANTS = {
    "saravana": {
        "name": "Hotel Saravana Bhavan", "emoji": "🥣",
        "cuisine": "South Indian Veg", "type": "veg",
        "area": "T Nagar", "lat": 13.0400, "lng": 80.2330,
        "address": "No 77, Usman Rd, T Nagar, Chennai",
        "phone": "+91 44 28340000", "rating": 4.6, "reviews": 2340,
        "delivery_time": "25-35 min", "delivery_charge": 30, "min_order": 150,
        "timing": "6 AM – 11 PM", "subscription": "active",
        "menu": {
            "Breakfast": {
                "Idly (2 pcs)":        {"price": 50,  "veg": True},
                "Masala Dosa":         {"price": 90,  "veg": True},
                "Pongal":              {"price": 70,  "veg": True},
                "Rava Upma":           {"price": 60,  "veg": True},
                "Mini Tiffin Combo":   {"price": 120, "veg": True},
            },
            "Meals": {
                "Full Meals":          {"price": 180, "veg": True},
                "Mini Meals":          {"price": 140, "veg": True},
                "Curd Rice":           {"price": 80,  "veg": True},
                "Sambar Rice":         {"price": 100, "veg": True},
            },
            "Drinks": {
                "Filter Coffee":       {"price": 40,  "veg": True},
                "Buttermilk":          {"price": 30,  "veg": True},
                "Fresh Lime Soda":     {"price": 50,  "veg": True},
            }
        },
        "offers": {
            "SB10": {"type": "percent", "discount": 10, "min": 200, "desc": "10% off on ₹200+"},
            "MORNING": {"type": "flat", "discount": 30, "min": 150, "desc": "₹30 off breakfast"},
        },
        "delivery_partners": [
            {"name": "Rajan K",  "phone": "+91 9876500001", "rating": 4.8},
            {"name": "Muthu S",  "phone": "+91 9876500002", "rating": 4.7},
        ]
    },
    "anjappar": {
        "name": "Anjappar Chettinad", "emoji": "🍗",
        "cuisine": "Chettinad Non-Veg", "type": "nonveg",
        "area": "Anna Nagar", "lat": 13.0840, "lng": 80.2100,
        "address": "Shop 7, 2nd Ave, Anna Nagar, Chennai",
        "phone": "+91 44 26261616", "rating": 4.5, "reviews": 1820,
        "delivery_time": "35-50 min", "delivery_charge": 40, "min_order": 300,
        "timing": "11 AM – 11 PM", "subscription": "active",
        "menu": {
            "Biryani": {
                "Chicken Biryani":     {"price": 280, "veg": False},
                "Mutton Biryani":      {"price": 380, "veg": False},
                "Egg Biryani":         {"price": 220, "veg": False},
                "Prawn Biryani":       {"price": 420, "veg": False},
            },
            "Gravy": {
                "Chicken Chettinad":   {"price": 320, "veg": False},
                "Mutton Pepper Fry":   {"price": 420, "veg": False},
                "Fish Curry":          {"price": 300, "veg": False},
                "Egg Curry":           {"price": 160, "veg": False},
            },
            "Starters": {
                "Chicken 65":          {"price": 260, "veg": False},
                "Mutton Sukka":        {"price": 360, "veg": False},
                "Prawn Fry":           {"price": 340, "veg": False},
            }
        },
        "offers": {
            "CHETTINAD15": {"type": "percent", "discount": 15, "min": 500, "desc": "15% off ₹500+"},
            "FREEDEL": {"type": "delivery", "discount": 40, "min": 400, "desc": "Free delivery on ₹400+"},
        },
        "delivery_partners": [
            {"name": "Kumar R",   "phone": "+91 9876500003", "rating": 4.6},
            {"name": "Pradeep M", "phone": "+91 9876500004", "rating": 4.9},
        ]
    },
    "murugan": {
        "name": "Murugan Idli Shop", "emoji": "🫕",
        "cuisine": "Traditional Tiffin", "type": "veg",
        "area": "Mylapore", "lat": 13.0340, "lng": 80.2690,
        "address": "77, Luz Church Rd, Mylapore, Chennai",
        "phone": "+91 44 28113455", "rating": 4.7, "reviews": 3100,
        "delivery_time": "20-30 min", "delivery_charge": 25, "min_order": 100,
        "timing": "6 AM – 10 PM", "subscription": "active",
        "menu": {
            "Signature": {
                "Soft Idly (4 pcs)":   {"price": 80,  "veg": True},
                "Ghee Idly (2 pcs)":   {"price": 90,  "veg": True},
                "Sambar Vada":         {"price": 70,  "veg": True},
                "Set Dosa":            {"price": 100, "veg": True},
                "Podi Idly":           {"price": 90,  "veg": True},
            },
            "Combos": {
                "Idly Vada Combo":     {"price": 130, "veg": True},
                "Dosa Sambar Combo":   {"price": 140, "veg": True},
                "Breakfast Thali":     {"price": 180, "veg": True},
            },
        },
        "offers": {
            "MURUGAN20": {"type": "flat", "discount": 20, "min": 150, "desc": "₹20 off on ₹150+"},
        },
        "delivery_partners": [
            {"name": "Selvam T",  "phone": "+91 9876500005", "rating": 4.7},
        ]
    },
    "buhari": {
        "name": "Buhari Restaurant", "emoji": "🍖",
        "cuisine": "Mughlai & Biryani", "type": "nonveg",
        "area": "Egmore", "lat": 13.0790, "lng": 80.2610,
        "address": "83, Anna Salai, Egmore, Chennai",
        "phone": "+91 44 28521001", "rating": 4.4, "reviews": 2780,
        "delivery_time": "40-55 min", "delivery_charge": 45, "min_order": 350,
        "timing": "12 PM – 12 AM", "subscription": "active",
        "menu": {
            "Biryani": {
                "Buhari Special Biryani":  {"price": 350, "veg": False},
                "Mutton Dum Biryani":      {"price": 420, "veg": False},
                "Chicken Dum Biryani":     {"price": 320, "veg": False},
                "Veg Biryani":             {"price": 220, "veg": True},
            },
            "Kebab & Tandoor": {
                "Chicken Seekh Kebab":     {"price": 340, "veg": False},
                "Mutton Shammi":           {"price": 380, "veg": False},
                "Tandoori Chicken (half)": {"price": 360, "veg": False},
            },
            "Gravy": {
                "Butter Chicken":          {"price": 320, "veg": False},
                "Mutton Rogan Josh":       {"price": 400, "veg": False},
                "Dal Makhani":             {"price": 200, "veg": True},
            }
        },
        "offers": {
            "BUHARI50": {"type": "flat", "discount": 50, "min": 500, "desc": "₹50 off on ₹500+"},
            "NIGHTOWL": {"type": "percent", "discount": 20, "min": 400, "desc": "20% off after 9 PM"},
        },
        "delivery_partners": [
            {"name": "Arjun P",   "phone": "+91 9876500006", "rating": 4.5},
            {"name": "Dinesh K",  "phone": "+91 9876500007", "rating": 4.6},
        ]
    },
    "cream_centre": {
        "name": "Cream Centre", "emoji": "🍕",
        "cuisine": "Multi-Cuisine Veg", "type": "veg",
        "area": "Nungambakkam", "lat": 13.0620, "lng": 80.2430,
        "address": "7, Khader Nawaz Khan Rd, Nungambakkam",
        "phone": "+91 44 28331234", "rating": 4.3, "reviews": 1560,
        "delivery_time": "30-45 min", "delivery_charge": 35, "min_order": 250,
        "timing": "12 PM – 11 PM", "subscription": "active",
        "menu": {
            "Starters": {
                "Veg Spring Rolls":     {"price": 180, "veg": True},
                "Paneer Tikka":         {"price": 260, "veg": True},
                "Cheese Balls":         {"price": 200, "veg": True},
            },
            "Mains": {
                "Paneer Butter Masala": {"price": 280, "veg": True},
                "Pasta Arrabiata":      {"price": 240, "veg": True},
                "Veg Lasagne":          {"price": 320, "veg": True},
                "Mexican Rice Bowl":    {"price": 260, "veg": True},
            },
            "Pizza": {
                "Margherita Pizza":     {"price": 260, "veg": True},
                "Veggie Supreme Pizza": {"price": 320, "veg": True},
            },
            "Desserts": {
                "Hot Chocolate Fudge":  {"price": 220, "veg": True},
                "Brownie Sundae":       {"price": 200, "veg": True},
            }
        },
        "offers": {
            "PIZZA20": {"type": "percent", "discount": 20, "min": 300, "desc": "20% off on pizza"},
        },
        "delivery_partners": [
            {"name": "Vinoth S",  "phone": "+91 9876500008", "rating": 4.8},
        ]
    },
    "kaaraikudi": {
        "name": "Kaaraikudi Chettinad", "emoji": "🍛",
        "cuisine": "Authentic Chettinad", "type": "nonveg",
        "area": "Velachery", "lat": 12.9788, "lng": 80.2204,
        "address": "45, 100 Ft Rd, Velachery, Chennai",
        "phone": "+91 98412 00000", "rating": 4.6, "reviews": 980,
        "delivery_time": "30-45 min", "delivery_charge": 35, "min_order": 250,
        "timing": "11 AM – 10:30 PM", "subscription": "active",
        "menu": {
            "Biryani": {
                "Kaaraikudi Mutton Biryani": {"price": 400, "veg": False},
                "Chicken Biryani":           {"price": 280, "veg": False},
            },
            "Chettinad Specials": {
                "Chettinad Fish Fry":        {"price": 320, "veg": False},
                "Chicken Kuzhambu":          {"price": 300, "veg": False},
                "Quail (Kaadai) Fry":        {"price": 380, "veg": False},
                "Kavuni Arisi (Dessert)":    {"price": 120, "veg": True},
            },
        },
        "offers": {
            "KAAR10": {"type": "percent", "discount": 10, "min": 300, "desc": "10% off ₹300+"},
        },
        "delivery_partners": [
            {"name": "Balu K",  "phone": "+91 9876500009", "rating": 4.7},
        ]
    },
    "bombay_bakery": {
        "name": "Bombay Bakery & Café", "emoji": "🥐",
        "cuisine": "Bakery, Snacks & Chai", "type": "veg",
        "area": "Adyar", "lat": 13.0063, "lng": 80.2574,
        "address": "12, LB Rd, Adyar, Chennai",
        "phone": "+91 98400 11111", "rating": 4.5, "reviews": 710,
        "delivery_time": "15-25 min", "delivery_charge": 20, "min_order": 80,
        "timing": "7 AM – 10 PM", "subscription": "active",
        "menu": {
            "Bakery": {
                "Veg Puff":            {"price": 35,  "veg": True},
                "Egg Puff":            {"price": 40,  "veg": False},
                "Croissant":           {"price": 60,  "veg": True},
                "Samosa (2 pcs)":      {"price": 50,  "veg": True},
                "Bread Toast":         {"price": 45,  "veg": True},
            },
            "Café Drinks": {
                "Masala Chai":         {"price": 40,  "veg": True},
                "Cold Coffee":         {"price": 80,  "veg": True},
                "Lemon Iced Tea":      {"price": 70,  "veg": True},
            },
            "Sweets": {
                "Gulab Jamun (2 pcs)": {"price": 60,  "veg": True},
                "Carrot Halwa":        {"price": 80,  "veg": True},
                "Payasam Cup":         {"price": 70,  "veg": True},
            }
        },
        "offers": {
            "CHAI5": {"type": "flat", "discount": 20, "min": 100, "desc": "₹20 off on ₹100+"},
        },
        "delivery_partners": [
            {"name": "Suresh A", "phone": "+91 9876500010", "rating": 4.9},
        ]
    },
    "seafood_bay": {
        "name": "Chennai Seafood Bay", "emoji": "🦐",
        "cuisine": "Coastal Seafood", "type": "nonveg",
        "area": "Besant Nagar", "lat": 13.0002, "lng": 80.2698,
        "address": "18, 4th Ave, Besant Nagar, Chennai",
        "phone": "+91 98765 22222", "rating": 4.7, "reviews": 1240,
        "delivery_time": "35-50 min", "delivery_charge": 50, "min_order": 400,
        "timing": "12 PM – 11 PM", "subscription": "active",
        "menu": {
            "Seafood Starters": {
                "Prawn Masala Fry":         {"price": 380, "veg": False},
                "Fish Fingers":             {"price": 280, "veg": False},
                "Squid Pepper Fry":         {"price": 360, "veg": False},
                "Crab Masala (500g)":       {"price": 680, "veg": False},
            },
            "Mains & Curry": {
                "Prawn Biryani":            {"price": 440, "veg": False},
                "Fish Curry with Rice":     {"price": 320, "veg": False},
                "Lobster Butter Garlic":    {"price": 980, "veg": False},
                "Mixed Seafood Rice Bowl":  {"price": 420, "veg": False},
            },
        },
        "offers": {
            "SEAFRESH": {"type": "percent", "discount": 12, "min": 500, "desc": "12% off ₹500+"},
            "FREESHIP": {"type": "delivery", "discount": 50, "min": 600, "desc": "Free delivery ₹600+"},
        },
        "delivery_partners": [
            {"name": "Fisher K",  "phone": "+91 9876500011", "rating": 4.6},
            {"name": "Mohan G",   "phone": "+91 9876500012", "rating": 4.8},
        ]
    },
}

# ════════════════════════════════════════════════════════════════════════════
#  IN-MEMORY STATE
# ════════════════════════════════════════════════════════════════════════════
sessions   = {}   # sender → conversation messages for GPT
user_state = {}   # sender → {"step", "cart", "restaurant", "name", "address",
                  #           "coupon_discount", "location_lat", "location_lng",
                  #           "zone", "last_active"}
orders     = {}
payouts    = {}


# ════════════════════════════════════════════════════════════════════════════
#  GEO UTILITIES
# ════════════════════════════════════════════════════════════════════════════
def haversine(lat1, lng1, lat2, lng2):
    """Distance in km between two lat/lng points."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def latlong_to_zone(lat, lng):
    """Return the nearest Chennai zone name for given coordinates."""
    best, best_dist = None, 9999
    for key, (zlat, zlng, zname) in CHENNAI_ZONES.items():
        d = haversine(lat, lng, zlat, zlng)
        if d < best_dist:
            best_dist, best = d, zname
    return best if best else "Chennai"

def text_to_zone(text):
    """Match typed area/landmark text to a zone. Returns (zone_name, lat, lng) or None."""
    t = text.lower().strip()
    for key, (zlat, zlng, zname) in CHENNAI_ZONES.items():
        if key in t or t in key:
            return zname, zlat, zlng
    return None

def restaurants_near(lat, lng, limit=5):
    """Return restaurants sorted by distance from given point."""
    active = [(rid, r) for rid, r in RESTAURANTS.items() if r.get("subscription") == "active"]
    with_dist = []
    for rid, r in active:
        d = haversine(lat, lng, r["lat"], r["lng"])
        with_dist.append((d, rid, r))
    with_dist.sort(key=lambda x: x[0])
    return [(dist, rid, r) for dist, rid, r in with_dist[:limit]]


# ════════════════════════════════════════════════════════════════════════════
#  TIME-AWARE PROACTIVE SUGGESTIONS
# ════════════════════════════════════════════════════════════════════════════
def time_greeting():
    hour = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).hour
    if 5 <= hour < 12:
        return "Good morning! ☀️", "breakfast", ["idly", "dosa", "pongal", "chai", "coffee"]
    elif 12 <= hour < 15:
        return "Good afternoon! 🌤️", "lunch", ["biryani", "meals", "rice", "chicken", "fish"]
    elif 15 <= hour < 18:
        return "Good evening! ☕", "snacks", ["puff", "chai", "samosa", "coffee", "sweets"]
    elif 18 <= hour < 22:
        return "Good evening! 🌆", "dinner", ["biryani", "chicken", "mutton", "seafood", "pizza"]
    else:
        return "Hey night owl! 🌙", "late night", ["biryani", "chicken", "pizza", "kebab"]

def proactive_nudge(suggestion_type, foods, zone=None):
    greeting, meal, _ = time_greeting()
    area_hint = f" near *{zone}*" if zone else " near you"
    suggestions = ", ".join([f"_{f}_" for f in foods[:4]])
    return (
        f"{greeting} Craving something for *{meal}*?\n\n"
        f"🔥 Popular right now{area_hint}:\n{suggestions}\n\n"
        f"📍 *Share your location* (📎 → Location) for restaurants nearest to you!\n"
        f"_Or just type any food name — I'll find it!_ 🔍"
    )


# ════════════════════════════════════════════════════════════════════════════
#  SEARCH ENGINE
# ════════════════════════════════════════════════════════════════════════════
FOOD_ALIASES = {
    "biriyani": "biryani", "briyani": "biryani",
    "dosai": "dosa", "thosai": "dosa",
    "idli": "idly", "idlies": "idly",
    "noodle": "noodles", "pasta": "pasta",
    "prawns": "prawn", "shrimp": "prawn",
    "crab": "crab", "fish": "fish",
    "chicken 65": "chicken 65", "c65": "chicken 65",
}

def search_food(query, filter_type=None, user_lat=None, user_lng=None):
    """Search restaurants by food name. Returns list of (distance_km or None, rid, r, matched_items)."""
    q = FOOD_ALIASES.get(query.lower(), query.lower())
    results = []
    for rid, r in RESTAURANTS.items():
        if r.get("subscription") != "active":
            continue
        if filter_type == "veg" and r["type"] not in ["veg", "both"]:
            continue
        if filter_type == "nonveg" and r["type"] not in ["nonveg", "both"]:
            continue
        matched = []
        for cat, items in r["menu"].items():
            for item, d in items.items():
                if q in item.lower() or any(w in item.lower() for w in q.split()):
                    matched.append(f"{item} ₹{d['price']}")
        if matched:
            dist = haversine(user_lat, user_lng, r["lat"], r["lng"]) if user_lat else None
            results.append((dist, rid, r, matched[:3]))
    if user_lat:
        results.sort(key=lambda x: x[0] if x[0] is not None else 9999)
    return results


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
        f"_Powered by NexoraAI — Your WhatsApp Food SuperBot_\n\n"
        f"{greeting} Time for *{meal}*! Try: {suggestions}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 *Share your location* for nearest restaurants!\n"
        f"_(tap 📎 → Location in WhatsApp)_\n\n"
        f"🔍 *Or search any food:*\n"
        f"🍛 _biryani_ · 🥣 _idly_ · 🍗 _chicken_ · 🐟 _fish_ · 🍕 _pizza_\n\n"
        f"*Quick Commands:*\n"
        f"• *nearby* — Restaurants near you\n"
        f"• *veg* — Veg only\n"
        f"• *top* — Highest rated\n"
        f"• *area T Nagar* — By location\n"
        f"• *all* — All {total} restaurants\n\n"
        f"_Type any food name to start!_ 😊"
    )

def location_received_msg(zone, nearby_list):
    t  = f"📍 *Got your location!* You're near *{zone}*\n\n"
    t += f"🍽️ *Restaurants closest to you:*\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, (dist, rid, r) in enumerate(nearby_list, 1):
        veg_tag = "🟢" if r["type"] == "veg" else ("🔴" if r["type"] == "nonveg" else "🟡")
        t += f"{i}️⃣ {r['emoji']} *{r['name']}* {veg_tag}\n"
        t += f"   📍 {r['area']} — *{dist:.1f} km away*\n"
        t += f"   ⭐ {r['rating']}/5 | 🛵 {r['delivery_time']}\n"
        t += f"   💰 Min ₹{r['min_order']} | Delivery ₹{r['delivery_charge']}\n\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    for i, (dist, rid, r) in enumerate(nearby_list, 1):
        t += f"Type *{i}* to order from {r['name']}\n"
    t += "\n_Or search a food name (e.g. biryani, dosa, fish)_ 🔍"
    return t

def show_search_results(query, results):
    t  = f"🔍 *\"{query}\"* found in {len(results)} restaurant(s)\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, (dist, rid, r, matched) in enumerate(results, 1):
        veg_tag = "🟢 VEG" if r["type"] == "veg" else ("🔴 NON-VEG" if r["type"] == "nonveg" else "🟡 BOTH")
        t += f"{i}️⃣ {r['emoji']} *{r['name']}* {veg_tag}\n"
        t += f"   🍽️ {r['cuisine']}\n"
        dist_str = f" — *{dist:.1f} km*" if dist is not None else ""
        t += f"   📍 {r['area']}{dist_str}\n"
        t += f"   ⭐ {r['rating']}/5 | 🛵 {r['delivery_time']} | ₹{r['delivery_charge']} delivery\n"
        t += f"   🍽️ {' · '.join(matched)}\n\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    for i, (dist, rid, r, _) in enumerate(results, 1):
        t += f"Type *{i}* to order from {r['name']}\n"
    t += "\n_Search again or type *nearby* for all restaurants near you_ 🔍"
    return t

def show_no_results_msg(query, zone=None):
    area_hint = f" near *{zone}*" if zone else ""
    _, meal, foods = time_greeting()
    suggest = ", ".join([f"_{f}_" for f in foods[:3]])
    return (
        f"😕 Couldn't find *\"{query}\"*{area_hint}.\n\n"
        f"*Try these popular {meal} searches:*\n"
        f"{suggest}\n\n"
        f"Or try: _chicken_ · _mutton_ · _biryani_ · _dosa_ · _fish_ · _pizza_ · _veg meals_\n\n"
        f"💡 Type *all* to browse all restaurants!"
    )

def show_all_restaurants(user_lat=None, user_lng=None):
    active = [(rid, r) for rid, r in RESTAURANTS.items() if r.get("subscription") == "active"]
    if user_lat:
        active.sort(key=lambda x: haversine(user_lat, user_lng, x[1]["lat"], x[1]["lng"]))
    t = f"🍽️ *All FoodieBot Restaurants — Chennai*\n"
    t += f"_{len(active)} partner restaurants_\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, (rid, r) in enumerate(active, 1):
        dist = haversine(user_lat, user_lng, r["lat"], r["lng"]) if user_lat else None
        dist_str = f" | *{dist:.1f} km*" if dist else ""
        veg_tag = "🟢" if r["type"] == "veg" else ("🔴" if r["type"] == "nonveg" else "🟡")
        t += f"{i}️⃣ {r['emoji']} *{r['name']}* {veg_tag}\n"
        t += f"   🍽️ {r['cuisine']} | 📍 {r['area']}{dist_str}\n"
        t += f"   ⭐ {r['rating']}/5 | 🛵 {r['delivery_time']}\n\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    for i, (rid, r) in enumerate(active, 1):
        t += f"Type *{i}* to order from {r['name']}\n"
    return t

def show_restaurant_home(r):
    t  = f"{r['emoji']} *{r['name']}*\n"
    t += f"🍽️ {r['cuisine']}\n"
    t += f"📍 {r['address']}\n"
    t += f"⭐ {r['rating']}/5 ({r['reviews']} reviews)\n"
    t += f"🛵 {r['delivery_time']} | ₹{r['delivery_charge']} delivery\n"
    t += f"💰 Min order: ₹{r['min_order']}\n"
    t += f"⏰ {r['timing']}\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    # Show menu by category
    for cat, items in r["menu"].items():
        t += f"*{cat}*\n"
        for item, d in items.items():
            tag = "🟢" if d.get("veg") else "🔴"
            t += f"  {tag} {item} — ₹{d['price']}\n"
        t += "\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    t += "_Type the item names to add to cart_\n"
    t += "_e.g._ *Chicken Biryani, Chicken 65*\n\n"
    offers = r.get("offers", {})
    if offers:
        t += "🎁 *Offers:*\n"
        for code, o in offers.items():
            t += f"  *{code}* — {o['desc']}\n"
    return t

def show_cart(r, cart):
    total = sum(d["price"] * d["qty"] for d in cart.values())
    t = f"🛒 *Your Cart — {r['name']}*\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    for item, d in cart.items():
        t += f"  • {item} × {d['qty']} = ₹{d['price'] * d['qty']}\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    t += f"Subtotal: ₹{total}\n"
    t += f"Delivery: ₹{r['delivery_charge']}\n"
    t += f"*Total: ₹{total + r['delivery_charge']}*\n\n"
    if total < r["min_order"]:
        remaining = r["min_order"] - total
        t += f"⚠️ Add ₹{remaining} more to reach min order ₹{r['min_order']}\n\n"
    t += "_Type *checkout* to place order_\n"
    t += "_Type *more* to add items_\n"
    t += "_Type *coupon XXXX* to apply discount_\n"
    t += "_Type *clear* to empty cart_"
    return t

def order_confirmation(oid, r, name, total, payment_type, partner):
    t  = "━━━━━━━━━━━━━━━━━━━━━━\n"
    t += f"✅ *Order Confirmed!*\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    t += f"Order ID: *{oid}*\n"
    t += f"Restaurant: *{r['name']}*\n"
    t += f"Customer: {name}\n"
    t += f"Amount: ₹{total}\n"
    t += f"Payment: {payment_type}\n\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    t += f"🛵 *Your Delivery Partner:*\n"
    t += f"   Name: {partner['name']}\n"
    t += f"   Phone: {partner['phone']}\n"
    t += f"   Rating: ⭐{partner['rating']}\n\n"
    t += f"⏱️ Estimated delivery: {r['delivery_time']}\n\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    t += "_You will receive a call before delivery_\n"
    t += f"📞 Restaurant: {r['phone']}\n"
    t += f"📞 Help: {PLATFORM['phone']}\n\n"
    t += "Thank you for ordering on FoodieBot! 🍛❤️\n"
    t += "Type *review* after eating to share feedback!"
    return t

def upi_payment_msg(total, r):
    gpay  = f"gpay://upi/pay?pa={PLATFORM['upi']}&pn=FoodieBot&am={total}&cu=INR&tn=FoodieBot+Order"
    phonpe= f"phonepe://pay?pa={PLATFORM['upi']}&pn=FoodieBot&am={total}&cu=INR"
    return (
        f"💳 *Payment — ₹{total}*\n\n"
        f"Pay to: *{PLATFORM['upi']}*\n"
        f"Amount: *₹{total}*\n\n"
        f"📱 Quick Pay:\n"
        f"GPay: {gpay}\n"
        f"PhonePe: {phonpe}\n\n"
        f"After paying:\n"
        f"Type *paid* — confirm UPI payment\n"
        f"Type *cod* — Cash on Delivery\n\n"
        f"_Your order will be confirmed once payment is received_"
    )

def apply_coupon(r, code, subtotal):
    offers = r.get("offers", {})
    code = code.upper().strip()
    o = offers.get(code)
    if not o:
        return None, f"❌ Invalid coupon *{code}*. Type *offers* to see valid codes."
    if subtotal < o["min"]:
        return None, f"❌ Min order ₹{o['min']} needed. Your total: ₹{subtotal}."
    if o["type"] == "percent":
        d = int(subtotal * o["discount"] / 100)
        return d, f"✅ *{code}* applied! {o['discount']}% off = ₹{d} saved 🎉"
    if o["type"] == "flat":
        return o["discount"], f"✅ *{code}* applied! ₹{o['discount']} off 🎉"
    if o["type"] == "delivery":
        return r["delivery_charge"], f"✅ *{code}* applied! Free delivery 🎉"
    return None, "❌ Invalid coupon."

def ask_gpt(r, sender, text):
    if not OPENAI_KEY:
        return f"Please call us: {r['phone']} 📞"
    sessions.setdefault(sender, [])
    sessions[sender].append({"role": "user", "content": text})
    if len(sessions[sender]) > 20:
        sessions[sender] = sessions[sender][-20:]
    menu_str   = ", ".join([f"{item} ₹{d['price']}" for cat, its in r["menu"].items() for item, d in its.items()])
    offers_str = ", ".join([f"{c}: {o['desc']}" for c, o in r.get("offers", {}).items()])
    system = (
        f"You are a WhatsApp ordering assistant for {r['name']} ({r['cuisine']}) on FoodieBot Chennai.\n"
        f"MENU: {menu_str}\n"
        f"OFFERS: {offers_str}\n"
        f"DELIVERY: {r['delivery_time']} | ₹{r['delivery_charge']} | Min ₹{r['min_order']} | {r['timing']}\n"
        f"PAYMENT: Via FoodieBot UPI ({PLATFORM['upi']}) — GPay/PhonePe/COD\n"
        f"Be friendly, use emojis, reply concisely. Suggest combos and upsell where appropriate."
    )
    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "system", "content": system}] + sessions[sender], "max_tokens": 300},
            timeout=10
        )
        reply = resp.json()["choices"][0]["message"]["content"]
        sessions[sender].append({"role": "assistant", "content": reply})
        return reply
    except Exception:
        return f"Sorry, I'm having trouble right now. Call us: {r['phone']} 📞"


# ════════════════════════════════════════════════════════════════════════════
#  TWILIO SENDER
# ════════════════════════════════════════════════════════════════════════════
def send_whatsapp(to, body):
    if not TWILIO_SID or not TWILIO_AUTH:
        print(f"[DRY RUN → {to}]\n{body}\n")
        return
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
    requests.post(url, auth=(TWILIO_SID, TWILIO_AUTH), data={
        "From": TWILIO_FROM,
        "To":   f"whatsapp:{to}" if not to.startswith("whatsapp:") else to,
        "Body": body
    })


# ════════════════════════════════════════════════════════════════════════════
#  CORE MESSAGE HANDLER
# ════════════════════════════════════════════════════════════════════════════
def handle_message(sender, body, latitude=None, longitude=None):
    text  = (body or "").strip()
    lower = text.lower()
    now   = time.time()

    # Init state
    state = user_state.setdefault(sender, {
        "step": "home", "cart": {}, "restaurant": None,
        "name": None, "address": None,
        "coupon_discount": 0, "search_results": [],
        "location_lat": None, "location_lng": None, "zone": None,
        "last_active": now
    })
    state["last_active"] = now

    # ── LOCATION PIN SHARED ──────────────────────────────────────────────────
    if latitude is not None and longitude is not None:
        lat, lng = float(latitude), float(longitude)
        state["location_lat"] = lat
        state["location_lng"] = lng
        zone = latlong_to_zone(lat, lng)
        state["zone"] = zone
        nearby = restaurants_near(lat, lng, limit=5)
        state["search_results"] = [(dist, rid, r) for dist, rid, r in nearby]
        state["step"] = "home"
        return location_received_msg(zone, nearby)

    # ── NUMBER SELECTION (from search / nearby / all list) ───────────────────
    if text.isdigit() and state["step"] in ("home", "search", "area_search"):
        idx = int(text) - 1
        results = state.get("search_results", [])
        if results and 0 <= idx < len(results):
            entry = results[idx]
            if len(entry) == 3:
                dist, rid, r = entry
            else:
                dist, rid, r, _ = entry
            state["restaurant"] = rid
            state["cart"] = {}
            state["coupon_discount"] = 0
            state["step"] = "restaurant"
            return show_restaurant_home(r)
        return "❓ Please pick a number from the list above."

    # ── WITHIN RESTAURANT FLOW ───────────────────────────────────────────────
    if state["step"] == "restaurant" and state.get("restaurant"):
        r = RESTAURANTS[state["restaurant"]]

        # --- view cart ---
        if lower in ("cart", "view cart", "my cart"):
            return show_cart(r, state["cart"]) if state["cart"] else "🛒 Your cart is empty. Type menu items to add!"

        # --- clear cart ---
        if lower in ("clear", "clear cart"):
            state["cart"] = {}
            return "🗑️ Cart cleared! Type item names to add again."

        # --- checkout ---
        if lower == "checkout":
            if not state["cart"]:
                return "🛒 Your cart is empty! Type menu items first."
            subtotal = sum(d["price"] * d["qty"] for d in state["cart"].values())
            if subtotal < r["min_order"]:
                return f"⚠️ Min order for {r['name']} is ₹{r['min_order']}. Add ₹{r['min_order'] - subtotal} more."
            state["step"] = "get_name"
            return "📦 Almost there! What's your *name* for the order?"

        # --- coupon ---
        if lower.startswith("coupon ") or lower.startswith("apply "):
            code = text.split(" ", 1)[1]
            sub = sum(d["price"] * d["qty"] for d in state["cart"].values())
            disc, msg = apply_coupon(r, code, sub)
            if disc:
                state["coupon_discount"] = disc
            return msg

        # --- offers ---
        if lower in ("offers", "discount", "coupons"):
            offers = r.get("offers", {})
            if not offers:
                return "No active offers right now. Stay tuned!"
            t = "🎁 *Active Offers:*\n"
            for code, o in offers.items():
                t += f"  *{code}* — {o['desc']}\n"
            t += "\nType *coupon CODE* to apply."
            return t

        # --- more items / back ---
        if lower in ("more", "back", "menu"):
            return show_restaurant_home(r)

        # --- try to parse items from menu ---
        all_items = {item.lower(): (item, d["price"]) for cat, its in r["menu"].items() for item, d in its.items()}
        added = []
        for item_lower, (item_name, price) in all_items.items():
            if item_lower in lower:
                qty = 1
                # try "2 chicken biryani" or "chicken biryani x2"
                import re
                m = re.search(r'(\d+)\s*[x×]?\s*' + re.escape(item_lower), lower) or \
                    re.search(re.escape(item_lower) + r'\s*[x×]?\s*(\d+)', lower)
                if m:
                    qty = int(m.group(1))
                if item_name in state["cart"]:
                    state["cart"][item_name]["qty"] += qty
                else:
                    state["cart"][item_name] = {"price": price, "qty": qty}
                added.append(f"{item_name} × {qty}")
        if added:
            sub = sum(d["price"] * d["qty"] for d in state["cart"].values())
            total = sub + r["delivery_charge"] - state["coupon_discount"]
            t  = f"✅ Added: {', '.join(added)}\n\n"
            t += f"🛒 Cart total: ₹{total} ({len(state['cart'])} item(s))\n"
            t += f"Type *cart* to review | *checkout* to order | add more items"
            return t

        # --- GPT fallback for restaurant context ---
        return ask_gpt(r, sender, text)

    # ── ORDER FLOW ───────────────────────────────────────────────────────────
    if state["step"] == "get_name":
        state["name"] = text
        state["step"] = "get_address"
        zone = state.get("zone")
        hint = f"\n_(Detected near {zone} — just confirm or update)_" if zone else ""
        return f"🏠 Great *{text}*! What's your *delivery address*?{hint}"

    if state["step"] == "get_address":
        state["address"] = text
        # also try to detect zone from address text
        if not state.get("zone"):
            match = text_to_zone(text)
            if match:
                state["zone"] = match[0]
                state["location_lat"] = match[1]
                state["location_lng"] = match[2]
        r = RESTAURANTS[state["restaurant"]]
        sub  = sum(d["price"] * d["qty"] for d in state["cart"].values())
        tot  = sub + r["delivery_charge"] - state["coupon_discount"]
        state["order_total"] = tot
        state["step"] = "payment"
        return upi_payment_msg(tot, r)

    if state["step"] == "payment":
        if lower in ("paid", "done", "payment done", "upi done", "gpay", "phonepay"):
            payment_type = "UPI"
        elif lower in ("cod", "cash", "cash on delivery"):
            payment_type = "COD"
        else:
            return "💳 Type *paid* after UPI payment or *cod* for Cash on Delivery."

        r = RESTAURANTS[state["restaurant"]]
        partner = random.choice(r["delivery_partners"])
        oid = "FB" + str(uuid.uuid4())[:6].upper()
        total = state.get("order_total", 0)

        # Save order
        orders[oid] = {
            "restaurant": state["restaurant"], "name": state["name"],
            "address": state["address"], "cart": state["cart"].copy(),
            "total": total, "payment": payment_type, "partner": partner,
            "time": datetime.datetime.now().isoformat(), "sender": sender
        }
        commission = int(total * PLATFORM["commission"])
        payouts[state["restaurant"]] = payouts.get(state["restaurant"], 0) + (total - commission)

        msg = order_confirmation(oid, r, state["name"], total, payment_type, partner)

        # Reset
        state["step"] = "home"
        state["cart"] = {}
        state["restaurant"] = None
        state["coupon_discount"] = 0
        state["search_results"] = []
        return msg

    # ── HOME COMMANDS ────────────────────────────────────────────────────────
    ulat = state.get("location_lat")
    ulng = state.get("location_lng")
    uzone = state.get("zone")

    # hi / hello → welcome
    if lower in ("hi", "hello", "hey", "start", "hii", "menu", "help"):
        return welcome_msg(uzone)

    # nearby (no args) → show nearest based on stored location
    if lower in ("nearby", "near me", "closest"):
        if ulat:
            nearby = restaurants_near(ulat, ulng, 5)
            state["search_results"] = [(d, rid, r) for d, rid, r in nearby]
            state["step"] = "home"
            return location_received_msg(uzone or "your area", nearby)
        return (
            "📍 Share your location first!\n"
            "_(tap 📎 → Location in WhatsApp)_\n\n"
            "Or type *area T Nagar* / *area Adyar* etc."
        )

    # area <zone> → look up zone and show nearest
    if lower.startswith("area "):
        area_query = text[5:].strip()
        match = text_to_zone(area_query)
        if match:
            zname, zlat, zlng = match
            state["zone"] = zname
            state["location_lat"] = zlat
            state["location_lng"] = zlng
            nearby = restaurants_near(zlat, zlng, 5)
            state["search_results"] = [(d, rid, r) for d, rid, r in nearby]
            state["step"] = "area_search"
            return location_received_msg(zname, nearby)
        return f"😕 Couldn't find *{area_query}* in Chennai. Try: T Nagar, Adyar, Velachery, Anna Nagar, OMR, Mylapore…"

    # all
    if lower == "all":
        active = [(rid, r) for rid, r in RESTAURANTS.items() if r.get("subscription") == "active"]
        if ulat:
            active.sort(key=lambda x: haversine(ulat, ulng, x[1]["lat"], x[1]["lng"]))
        state["search_results"] = [(haversine(ulat, ulng, r["lat"], r["lng"]) if ulat else None, rid, r) for rid, r in active]
        state["step"] = "home"
        return show_all_restaurants(ulat, ulng)

    # veg
    if lower in ("veg", "vegetarian", "veg only"):
        results = search_food("", filter_type="veg", user_lat=ulat, user_lng=ulng)
        # show all veg restaurants
        veg_rests = [(haversine(ulat, ulng, r["lat"], r["lng"]) if ulat else 0, rid, r)
                     for rid, r in RESTAURANTS.items() if r.get("subscription") == "active" and r["type"] in ("veg", "both")]
        if ulat:
            veg_rests.sort(key=lambda x: x[0])
        state["search_results"] = veg_rests
        state["step"] = "home"
        t = f"🟢 *Veg Restaurants — Chennai*\n"
        t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, (dist, rid, r) in enumerate(veg_rests, 1):
            dist_str = f" | *{dist:.1f} km*" if ulat else ""
            t += f"{i}️⃣ {r['emoji']} *{r['name']}*\n"
            t += f"   📍 {r['area']}{dist_str} | ⭐ {r['rating']}/5\n\n"
        t += "━━━━━━━━━━━━━━━━━━━━━━\n"
        for i, (_, rid, r) in enumerate(veg_rests, 1):
            t += f"Type *{i}* to order from {r['name']}\n"
        return t

    # top
    if lower in ("top", "best", "top rated"):
        ranked = sorted(
            [(rid, r) for rid, r in RESTAURANTS.items() if r.get("subscription") == "active"],
            key=lambda x: x[1]["rating"], reverse=True
        )
        state["search_results"] = [(haversine(ulat, ulng, r["lat"], r["lng"]) if ulat else 0, rid, r) for rid, r in ranked]
        state["step"] = "home"
        t = "⭐ *Top Rated Restaurants*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, (rid, r) in enumerate(ranked, 1):
            t += f"{i}️⃣ {r['emoji']} *{r['name']}* — ⭐{r['rating']}/5\n   📍 {r['area']} | {r['cuisine']}\n\n"
        t += "━━━━━━━━━━━━━━━━━━━━━━\n"
        for i, (rid, r) in enumerate(ranked, 1):
            t += f"Type *{i}* to order from {r['name']}\n"
        return t

    # cheap
    if lower in ("cheap", "budget", "cheap food"):
        cheap = sorted(
            [(rid, r) for rid, r in RESTAURANTS.items() if r.get("subscription") == "active"],
            key=lambda x: x[1]["min_order"]
        )
        state["search_results"] = [(0, rid, r) for rid, r in cheap]
        state["step"] = "home"
        t = "💰 *Budget Friendly Restaurants*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, (rid, r) in enumerate(cheap, 1):
            t += f"{i}️⃣ {r['emoji']} *{r['name']}* — Min ₹{r['min_order']}\n   📍 {r['area']} | ⭐{r['rating']}/5\n\n"
        t += "━━━━━━━━━━━━━━━━━━━━━━\n"
        for i, (rid, r) in enumerate(cheap, 1):
            t += f"Type *{i}* to order from {r['name']}\n"
        return t

    # review shortcut
    if lower.startswith("review"):
        return "⭐ Thank you! Share your review:\nhttps://g.page/foodiebot-chennai\n\n_Your feedback helps us grow!_ 🙏"

    # proactive nudge (blank message or "?")
    if lower in ("", "?"):
        _, meal, foods = time_greeting()
        return proactive_nudge(meal, foods, uzone)

    # ── FOOD SEARCH (default) ────────────────────────────────────────────────
    results = search_food(lower, user_lat=ulat, user_lng=ulng)
    if results:
        state["search_results"] = results
        state["step"] = "search"
        return show_search_results(lower, results)
    else:
        return show_no_results_msg(lower, uzone)


# ════════════════════════════════════════════════════════════════════════════
#  WEBHOOK
# ════════════════════════════════════════════════════════════════════════════
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return "FoodieBot SuperBot v3 is live! 🚀", 200

    # Twilio sends form-encoded POST
    sender  = request.form.get("From", "").replace("whatsapp:", "")
    body    = request.form.get("Body", "").strip()

    # WhatsApp location share → Twilio sends Latitude / Longitude fields
    latitude  = request.form.get("Latitude")
    longitude = request.form.get("Longitude")

    if not sender:
        return jsonify({"status": "no sender"}), 400

    reply = handle_message(sender, body, latitude, longitude)
    send_whatsapp(sender, reply)
    return jsonify({"status": "ok"}), 200


# ════════════════════════════════════════════════════════════════════════════
#  ADMIN APIs
# ════════════════════════════════════════════════════════════════════════════
def admin_auth():
    return request.args.get("key") == ADMIN_KEY

@app.route("/admin/orders")
def admin_orders():
    if not admin_auth(): return jsonify({"error": "unauthorized"}), 401
    return jsonify({"total_orders": len(orders), "orders": orders})

@app.route("/admin/stats")
def admin_stats():
    if not admin_auth(): return jsonify({"error": "unauthorized"}), 401
    total_rev = sum(o["total"] for o in orders.values())
    return jsonify({
        "total_orders": len(orders),
        "total_revenue": total_rev,
        "platform_commission": int(total_rev * PLATFORM["commission"]),
        "active_restaurants": len([r for r in RESTAURANTS.values() if r.get("subscription") == "active"]),
        "active_sessions": len(user_state)
    })

@app.route("/admin/payouts")
def admin_payouts():
    if not admin_auth(): return jsonify({"error": "unauthorized"}), 401
    return jsonify({"payouts": payouts})

@app.route("/admin/broadcast")
def admin_broadcast():
    """Send a proactive nudge to all active users."""
    if not admin_auth(): return jsonify({"error": "unauthorized"}), 401
    _, meal, foods = time_greeting()
    count = 0
    for sender, state in user_state.items():
        # only ping users active in last 24h
        if time.time() - state.get("last_active", 0) < 86400:
            msg = proactive_nudge(meal, foods, state.get("zone"))
            send_whatsapp(sender, msg)
            count += 1
    return jsonify({"broadcast_sent": count, "meal": meal})

@app.route("/health")
def health():
    return jsonify({"status": "ok", "version": "SuperBot v3.0", "restaurants": len(RESTAURANTS)})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
