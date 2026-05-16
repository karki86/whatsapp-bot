"""
FoodieBot Chennai - Complete WhatsApp Food Discovery Platform
By NexoraAI | +91 7010624989 | nexoraai.netlify.app
Customer types Hi → finds nearby restaurants → orders → pays
Ready to Deploy: GitHub → Render → Twilio → LIVE!
"""

from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import requests, os, random
from datetime import datetime

app = Flask(__name__)

OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
MASTER_KEY = os.environ.get("MASTER_KEY", "NEXORAAI2026")

# ═══════════════════════════════════════════════════════════
# PLATFORM PAYMENT — NexoraAI collects, pays restaurants daily
# ═══════════════════════════════════════════════════════════
PLATFORM = {
    "name":     "FoodieBot Chennai",
    "company":  "NexoraAI",
    "upi":      os.environ.get("PLATFORM_UPI",     "nexoraai@upi"),
    "gpay":     os.environ.get("PLATFORM_GPAY",    "nexoraai@okicici"),
    "phonepe":  os.environ.get("PLATFORM_PHONEPE", "nexoraai@ybl"),
    "card":     os.environ.get("PLATFORM_CARD",    "https://rzp.io/l/nexoraai"),
    "phone":    "+91 7010624989",
    "website":  "nexoraai.netlify.app",
}

COMMISSION = 0.10  # 10% per order

# ═══════════════════════════════════════════════════════════
# ALL CHENNAI RESTAURANTS — VEG & NON-VEG
# Add more by copying any block below
# ═══════════════════════════════════════════════════════════
RESTAURANTS = {

    # ── VEG RESTAURANTS ──────────────────────────────────

    "R001": {
        "id": "R001", "type": "veg",
        "name": "Hotel Saravana Bhavan",
        "emoji": "🍛", "cuisine": "South Indian Veg",
        "area": "T Nagar", "city": "Chennai",
        "address": "293, Usman Road, T Nagar, Chennai 600017",
        "phone": "+91 44 2814 2060",
        "timing": "6:00 AM – 11:00 PM",
        "rating": 4.5, "reviews": "12,400",
        "delivery_time": "30-45 mins",
        "delivery_charge": 40, "min_order": 100,
        "subscription": "active", "plan": "pro",
        "tags": ["idly","dosa","pongal","vada","sambar","filter coffee","veg","south indian","breakfast","upma","meals","ghee rice","rasam","curd rice"],
        "menu": {
            "🌅 Breakfast (6AM-11AM)": {
                "Idly (4pcs) + Sambar":   {"price":60,  "rating":4.8,"orders":8400, "spice":"Mild"},
                "Masala Dosa":            {"price":80,  "rating":4.9,"orders":9200, "spice":"Mild"},
                "Plain Dosa":             {"price":60,  "rating":4.7,"orders":7600, "spice":"None"},
                "Pongal + Chutney":       {"price":70,  "rating":4.7,"orders":6800, "spice":"Mild"},
                "Medu Vada (2pcs)":       {"price":50,  "rating":4.8,"orders":7800, "spice":"Mild"},
                "Upma":                   {"price":50,  "rating":4.5,"orders":4200, "spice":"Mild"},
                "Poori + Masala (3pcs)":  {"price":80,  "rating":4.6,"orders":5400, "spice":"Mild"},
                "Rava Dosa":              {"price":90,  "rating":4.7,"orders":5600, "spice":"None"},
                "Uthappam":               {"price":90,  "rating":4.6,"orders":4800, "spice":"Mild"},
            },
            "🍛 Meals & Rice": {
                "Full Meals (Veg)":       {"price":180, "rating":4.9,"orders":12000,"spice":"Mild"},
                "Mini Meals":             {"price":140, "rating":4.7,"orders":8400, "spice":"Mild"},
                "Curd Rice":              {"price":80,  "rating":4.6,"orders":5200, "spice":"None"},
                "Lemon Rice":             {"price":90,  "rating":4.6,"orders":4800, "spice":"Mild"},
                "Veg Biryani":            {"price":160, "rating":4.5,"orders":6400, "spice":"Medium"},
                "Ghee Rice + Dal":        {"price":140, "rating":4.7,"orders":5600, "spice":"Mild"},
                "Bisi Bele Bath":         {"price":120, "rating":4.6,"orders":4200, "spice":"Medium"},
            },
            "🥘 Curries & Gravies": {
                "Paneer Butter Masala":   {"price":180, "rating":4.7,"orders":7200, "spice":"Mild"},
                "Dal Tadka":              {"price":120, "rating":4.6,"orders":5800, "spice":"Mild"},
                "Palak Paneer":           {"price":180, "rating":4.6,"orders":5200, "spice":"Mild"},
                "Sambar":                 {"price":60,  "rating":4.8,"orders":9600, "spice":"Medium"},
            },
            "🫓 Breads": {
                "Chapati (2pcs)":         {"price":40,  "rating":4.5,"orders":6800, "spice":"None"},
                "Parotta (2pcs)":         {"price":50,  "rating":4.8,"orders":9200, "spice":"None"},
            },
            "☕ Drinks & Sweets": {
                "Filter Coffee":          {"price":40,  "rating":4.9,"orders":14000,"spice":"None"},
                "Mango Lassi":            {"price":80,  "rating":4.7,"orders":4800, "spice":"None"},
                "Gulab Jamun (2pcs)":     {"price":60,  "rating":4.7,"orders":8400, "spice":"None"},
                "Halwa":                  {"price":80,  "rating":4.6,"orders":6200, "spice":"None"},
            },
        },
        "offers": {
            "SARVANA10": {"discount":10,"type":"percent","desc":"10% off meals","min":150},
            "THALI50":   {"discount":50,"type":"flat","desc":"₹50 off above ₹200","min":200},
            "FREEDEL":   {"discount":40,"type":"delivery","desc":"Free delivery","min":200},
        },
        "reviews": [
            {"name":"Vijay K","rating":5,"date":"Yesterday","text":"Best veg restaurant in Chennai! Filter coffee is divine ☕"},
            {"name":"Priya M","rating":5,"date":"2 days ago","text":"Coming here since 1990. Quality never changes! 🍛"},
        ],
    },

    "R002": {
        "id": "R002", "type": "veg",
        "name": "Murugan Idli Shop",
        "emoji": "🥣", "cuisine": "South Indian Breakfast",
        "area": "T Nagar", "city": "Chennai",
        "address": "77, Usman Road, T Nagar, Chennai 600017",
        "phone": "+91 44 2434 5678",
        "timing": "5:30 AM – 11:30 PM",
        "rating": 4.8, "reviews": "15,200",
        "delivery_time": "20-35 mins",
        "delivery_charge": 30, "min_order": 80,
        "subscription": "active", "plan": "pro",
        "tags": ["idly","dosa","vada","sambar","breakfast","pongal","soft idly","filter coffee","veg","south indian","tiffin","chutney"],
        "menu": {
            "🥣 Idly Specials": {
                "Soft Idly (4pcs)":       {"price":60,  "rating":4.9,"orders":18000,"spice":"Mild"},
                "Ghee Idly (4pcs)":       {"price":80,  "rating":4.9,"orders":12000,"spice":"Mild"},
                "Mini Idly (12pcs)":      {"price":100, "rating":4.8,"orders":9200, "spice":"Mild"},
                "Kanchipuram Idly (2pcs)":{"price":70,  "rating":4.8,"orders":8400, "spice":"Medium"},
                "Rava Idly (4pcs)":       {"price":80,  "rating":4.7,"orders":6800, "spice":"Mild"},
            },
            "🫓 Dosa": {
                "Masala Dosa":            {"price":80,  "rating":4.9,"orders":16000,"spice":"Mild"},
                "Paper Roast Dosa":       {"price":100, "rating":4.8,"orders":9800, "spice":"None"},
                "Plain Dosa":             {"price":60,  "rating":4.8,"orders":14000,"spice":"None"},
                "Onion Dosa":             {"price":80,  "rating":4.7,"orders":8400, "spice":"Mild"},
                "Cheese Dosa":            {"price":120, "rating":4.7,"orders":6200, "spice":"None"},
                "Set Dosa (3pcs)":        {"price":90,  "rating":4.7,"orders":7400, "spice":"None"},
            },
            "🍲 Combos & Vada": {
                "Medu Vada (2pcs)":       {"price":50,  "rating":4.8,"orders":12000,"spice":"Mild"},
                "Sambar Vada":            {"price":70,  "rating":4.8,"orders":9600, "spice":"Medium"},
                "Pongal + Vada Combo":    {"price":100, "rating":4.8,"orders":8400, "spice":"Mild"},
                "Idly + Vada Combo":      {"price":100, "rating":4.9,"orders":10000,"spice":"Mild"},
            },
            "☕ Drinks": {
                "Filter Coffee":          {"price":35,  "rating":4.9,"orders":18000,"spice":"None"},
                "Tea":                    {"price":25,  "rating":4.7,"orders":12000,"spice":"None"},
                "Buttermilk":             {"price":30,  "rating":4.7,"orders":8400, "spice":"None"},
            },
        },
        "offers": {
            "IDLY10":  {"discount":10,"type":"percent","desc":"10% off breakfast combos","min":100},
            "COMBO30": {"discount":30,"type":"flat","desc":"₹30 off above ₹150","min":150},
            "FREEDEL": {"discount":30,"type":"delivery","desc":"Free delivery","min":150},
        },
        "reviews": [
            {"name":"Kavitha M","rating":5,"date":"Today","text":"Softest idly in all of Chennai! Sambar is divine ☕"},
            {"name":"Rajan T","rating":5,"date":"Yesterday","text":"Paper roast dosa is crispy perfection! 🥣"},
        ],
    },

    "R003": {
        "id": "R003", "type": "veg",
        "name": "Cream Centre",
        "emoji": "🍕", "cuisine": "Multi-Cuisine Veg",
        "area": "Nungambakkam", "city": "Chennai",
        "address": "13, Khader Nawaz Khan Road, Nungambakkam, Chennai 600006",
        "phone": "+91 44 2833 4477",
        "timing": "11:30 AM – 11:00 PM",
        "rating": 4.5, "reviews": "6,200",
        "delivery_time": "30-45 mins",
        "delivery_charge": 45, "min_order": 200,
        "subscription": "active", "plan": "pro",
        "tags": ["pizza","pasta","burger","veg","sandwich","milkshake","ice cream","waffle","dessert","mocktail","italian","mexican"],
        "menu": {
            "🍕 Pizza": {
                "Margherita Pizza":       {"price":320, "rating":4.7,"orders":3600, "spice":"Mild"},
                "Paneer Tikka Pizza":     {"price":400, "rating":4.7,"orders":3200, "spice":"Medium"},
                "Veggie Supreme Pizza":   {"price":380, "rating":4.6,"orders":2800, "spice":"Mild"},
                "Corn & Capsicum Pizza":  {"price":340, "rating":4.5,"orders":2400, "spice":"Mild"},
            },
            "🍝 Pasta & Mexican": {
                "Penne Arrabbiata":       {"price":280, "rating":4.6,"orders":2800, "spice":"Hot"},
                "Pasta Alfredo":          {"price":300, "rating":4.6,"orders":2400, "spice":"None"},
                "Veg Burrito":            {"price":280, "rating":4.5,"orders":1800, "spice":"Medium"},
                "Nachos + Dip":           {"price":240, "rating":4.6,"orders":2800, "spice":"Mild"},
            },
            "🍨 Desserts": {
                "Chocolate Sundae":       {"price":200, "rating":4.8,"orders":4800, "spice":"None"},
                "Hot Fudge Sundae":       {"price":220, "rating":4.8,"orders":4200, "spice":"None"},
                "Waffle + Ice Cream":     {"price":280, "rating":4.7,"orders":3600, "spice":"None"},
                "Brownie + Ice Cream":    {"price":260, "rating":4.8,"orders":4000, "spice":"None"},
            },
            "🥤 Drinks": {
                "Milkshake":              {"price":160, "rating":4.7,"orders":4800, "spice":"None"},
                "Fresh Juice":            {"price":120, "rating":4.6,"orders":3600, "spice":"None"},
                "Mocktail":               {"price":180, "rating":4.6,"orders":2800, "spice":"None"},
            },
        },
        "offers": {
            "CREAM20": {"discount":20,"type":"percent","desc":"20% off desserts","min":200},
            "FLAT80":  {"discount":80,"type":"flat","desc":"₹80 off above ₹400","min":400},
            "FREEDEL": {"discount":45,"type":"delivery","desc":"Free delivery","min":300},
        },
        "reviews": [
            {"name":"Nithya R","rating":5,"date":"3 days ago","text":"Hot Fudge Sundae is incredible! Best desserts in Chennai 🍨"},
        ],
    },

    "R004": {
        "id": "R004", "type": "veg",
        "name": "Sangeetha Veg Restaurant",
        "emoji": "🌿", "cuisine": "South Indian & North Indian Veg",
        "area": "Anna Nagar", "city": "Chennai",
        "address": "Shop 12, 2nd Avenue, Anna Nagar, Chennai 600040",
        "phone": "+91 44 2626 1234",
        "timing": "7:00 AM – 10:30 PM",
        "rating": 4.4, "reviews": "5,800",
        "delivery_time": "25-40 mins",
        "delivery_charge": 35, "min_order": 100,
        "subscription": "active", "plan": "starter",
        "tags": ["idly","dosa","veg","meals","chapati","parotta","north indian","veg biryani","paneer","dal","south indian","breakfast"],
        "menu": {
            "🌅 Breakfast": {
                "Idly (4pcs)":            {"price":55,  "rating":4.6,"orders":5400, "spice":"Mild"},
                "Dosa":                   {"price":70,  "rating":4.6,"orders":6200, "spice":"None"},
                "Pongal":                 {"price":65,  "rating":4.5,"orders":4200, "spice":"Mild"},
                "Vada (2pcs)":            {"price":50,  "rating":4.5,"orders":4800, "spice":"Mild"},
            },
            "🍛 Meals": {
                "Veg Meals":              {"price":160, "rating":4.5,"orders":7200, "spice":"Mild"},
                "Veg Biryani":            {"price":150, "rating":4.4,"orders":5600, "spice":"Medium"},
                "Curd Rice":              {"price":75,  "rating":4.5,"orders":4200, "spice":"None"},
            },
            "🥘 North Indian": {
                "Paneer Butter Masala":   {"price":180, "rating":4.5,"orders":4800, "spice":"Mild"},
                "Dal Makhani":            {"price":160, "rating":4.4,"orders":3600, "spice":"Mild"},
                "Palak Paneer":           {"price":170, "rating":4.4,"orders":3200, "spice":"Mild"},
                "Chana Masala":           {"price":150, "rating":4.3,"orders":2800, "spice":"Medium"},
            },
            "🫓 Breads": {
                "Chapati (3pcs)":         {"price":45,  "rating":4.4,"orders":5600, "spice":"None"},
                "Parotta (2pcs)":         {"price":50,  "rating":4.5,"orders":6200, "spice":"None"},
                "Naan (2pcs)":            {"price":60,  "rating":4.4,"orders":3800, "spice":"None"},
            },
            "☕ Drinks": {
                "Filter Coffee":          {"price":35,  "rating":4.7,"orders":8400, "spice":"None"},
                "Lassi":                  {"price":70,  "rating":4.5,"orders":3200, "spice":"None"},
            },
        },
        "offers": {
            "SANG10":  {"discount":10,"type":"percent","desc":"10% off meals","min":120},
            "FREEDEL": {"discount":35,"type":"delivery","desc":"Free delivery","min":180},
        },
        "reviews": [
            {"name":"Anand S","rating":4,"date":"4 days ago","text":"Good veg food, quick delivery. Value for money! 🌿"},
        ],
    },

    # ── NON-VEG RESTAURANTS ───────────────────────────────

    "R005": {
        "id": "R005", "type": "nonveg",
        "name": "Anjappar Chettinad",
        "emoji": "🌶️", "cuisine": "Chettinad Non-Veg",
        "area": "Anna Nagar", "city": "Chennai",
        "address": "100 Feet Road, Anna Nagar, Chennai 600040",
        "phone": "+91 44 4211 7788",
        "timing": "11:00 AM – 11:00 PM",
        "rating": 4.7, "reviews": "8,600",
        "delivery_time": "35-50 mins",
        "delivery_charge": 45, "min_order": 200,
        "subscription": "active", "plan": "pro",
        "tags": ["chicken","mutton","biryani","chettinad","non veg","pepper chicken","fish","prawn","crab","egg","spicy","kuzhi paniyaram"],
        "menu": {
            "🍗 Biryani": {
                "Chicken Biryani":        {"price":320, "rating":4.9,"orders":6800, "spice":"Medium"},
                "Mutton Biryani":         {"price":380, "rating":4.8,"orders":4200, "spice":"Medium"},
                "Prawn Biryani":          {"price":420, "rating":4.7,"orders":2800, "spice":"Medium"},
                "Chettinad Biryani":      {"price":350, "rating":4.9,"orders":5200, "spice":"Hot"},
                "Egg Biryani":            {"price":240, "rating":4.6,"orders":3600, "spice":"Medium"},
            },
            "🥩 Chettinad Specials": {
                "Chettinad Pepper Chicken":{"price":380,"rating":4.9,"orders":5600,"spice":"Hot"},
                "Mutton Chukka":           {"price":420,"rating":4.9,"orders":4400,"spice":"Hot"},
                "Country Chicken Gravy":   {"price":480,"rating":4.8,"orders":3800,"spice":"Hot"},
                "Kuzhi Paniyaram":         {"price":160,"rating":4.7,"orders":3200,"spice":"Medium"},
            },
            "🐟 Seafood": {
                "Fish Curry":             {"price":320, "rating":4.7,"orders":3600, "spice":"Hot"},
                "Prawn Masala":           {"price":420, "rating":4.8,"orders":2800, "spice":"Hot"},
                "Fish Fry":               {"price":280, "rating":4.8,"orders":4200, "spice":"Medium"},
                "Crab Masala":            {"price":580, "rating":4.7,"orders":1800, "spice":"Hot"},
            },
            "🫓 Breads": {
                "Parotta (2pcs)":         {"price":60,  "rating":4.7,"orders":6400, "spice":"None"},
                "Idiyappam + Curry":      {"price":140, "rating":4.8,"orders":3600, "spice":"Medium"},
                "Roti (2pcs)":            {"price":50,  "rating":4.5,"orders":4200, "spice":"None"},
            },
        },
        "offers": {
            "ANJA15":  {"discount":15,"type":"percent","desc":"15% off Chettinad specials","min":300},
            "FLAT100": {"discount":100,"type":"flat","desc":"₹100 off above ₹500","min":500},
            "FREEDEL": {"discount":45,"type":"delivery","desc":"Free delivery","min":300},
        },
        "reviews": [
            {"name":"Senthil K","rating":5,"date":"2 days ago","text":"Best Chettinad food! Pepper chicken is outstanding! 🌶️"},
            {"name":"Anand P","rating":5,"date":"3 days ago","text":"Country chicken gravy is legendary! Worth every rupee 🍗"},
        ],
    },

    "R006": {
        "id": "R006", "type": "nonveg",
        "name": "Buhari Restaurant",
        "emoji": "🍖", "cuisine": "Mughlai & South Indian",
        "area": "Anna Salai", "city": "Chennai",
        "address": "83, Anna Salai, Mount Road, Chennai 600002",
        "phone": "+91 44 2852 1144",
        "timing": "12:00 PM – 11:30 PM",
        "rating": 4.6, "reviews": "9,800",
        "delivery_time": "40-55 mins",
        "delivery_charge": 50, "min_order": 250,
        "subscription": "active", "plan": "pro",
        "tags": ["biryani","chicken","mutton","kebab","mughlai","naan","butter chicken","fish","prawn","non veg","tandoori"],
        "menu": {
            "🍗 Biryani (Since 1951)": {
                "Special Chicken Biryani":{"price":380, "rating":4.9,"orders":8400, "spice":"Medium"},
                "Mutton Biryani":         {"price":440, "rating":4.8,"orders":5600, "spice":"Medium"},
                "Prawn Biryani":          {"price":480, "rating":4.8,"orders":3200, "spice":"Medium"},
                "Veg Biryani":            {"price":240, "rating":4.5,"orders":2800, "spice":"Mild"},
            },
            "🥩 Mughlai": {
                "Butter Chicken":         {"price":360, "rating":4.9,"orders":5600, "spice":"Mild"},
                "Chicken Tikka":          {"price":380, "rating":4.8,"orders":4800, "spice":"Medium"},
                "Mutton Seekh Kebab":     {"price":420, "rating":4.8,"orders":3600, "spice":"Medium"},
                "Mutton Rogan Josh":      {"price":440, "rating":4.8,"orders":3200, "spice":"Hot"},
                "Chicken Korma":          {"price":340, "rating":4.7,"orders":3800, "spice":"Mild"},
            },
            "🐟 Seafood": {
                "Fish Masala":            {"price":360, "rating":4.7,"orders":3200, "spice":"Hot"},
                "Prawn Masala":           {"price":460, "rating":4.7,"orders":2400, "spice":"Hot"},
            },
            "🫓 Breads": {
                "Butter Naan (2pcs)":     {"price":80,  "rating":4.7,"orders":5600, "spice":"None"},
                "Garlic Naan (2pcs)":     {"price":100, "rating":4.8,"orders":4800, "spice":"None"},
                "Tandoori Roti (2pcs)":   {"price":70,  "rating":4.6,"orders":4200, "spice":"None"},
            },
            "🍦 Desserts": {
                "Gulab Jamun (4pcs)":     {"price":100, "rating":4.7,"orders":3600, "spice":"None"},
                "Kheer":                  {"price":120, "rating":4.6,"orders":2400, "spice":"None"},
                "Phirni":                 {"price":100, "rating":4.7,"orders":2800, "spice":"None"},
            },
        },
        "offers": {
            "BUHARI15": {"discount":15,"type":"percent","desc":"15% off first order","min":300},
            "FLAT120":  {"discount":120,"type":"flat","desc":"₹120 off above ₹600","min":600},
            "FREEDEL":  {"discount":50,"type":"delivery","desc":"Free delivery","min":400},
        },
        "reviews": [
            {"name":"Ashwin R","rating":5,"date":"2 days ago","text":"Buhari biryani — legendary since 1951! 🍖"},
            {"name":"Deepa S","rating":5,"date":"4 days ago","text":"Butter chicken is divine. Naan perfectly soft! 👌"},
        ],
    },

    "R007": {
        "id": "R007", "type": "nonveg",
        "name": "Ponnusamy Hotel",
        "emoji": "🍗", "cuisine": "Tamil Non-Veg",
        "area": "Vadapalani", "city": "Chennai",
        "address": "31, Arcot Road, Vadapalani, Chennai 600026",
        "phone": "+91 44 2374 5678",
        "timing": "11:00 AM – 11:00 PM",
        "rating": 4.6, "reviews": "7,400",
        "delivery_time": "30-45 mins",
        "delivery_charge": 40, "min_order": 180,
        "subscription": "active", "plan": "pro",
        "tags": ["chicken","mutton","biryani","fish","non veg","tamil","pepper chicken","country chicken","egg","prawn","kothu parotta"],
        "menu": {
            "🍗 Biryani": {
                "Chicken Biryani":        {"price":280, "rating":4.8,"orders":7200, "spice":"Medium"},
                "Mutton Biryani":         {"price":340, "rating":4.7,"orders":4400, "spice":"Medium"},
                "Egg Biryani":            {"price":220, "rating":4.6,"orders":3800, "spice":"Medium"},
                "Fish Biryani":           {"price":320, "rating":4.7,"orders":2800, "spice":"Medium"},
            },
            "🥩 Specials": {
                "Pepper Chicken":         {"price":300, "rating":4.8,"orders":4800, "spice":"Hot"},
                "Country Chicken Fry":    {"price":380, "rating":4.8,"orders":3600, "spice":"Hot"},
                "Chicken 65":             {"price":260, "rating":4.8,"orders":5400, "spice":"Hot"},
                "Mutton Liver Fry":       {"price":320, "rating":4.7,"orders":2400, "spice":"Hot"},
                "Egg Curry":              {"price":160, "rating":4.5,"orders":3200, "spice":"Medium"},
            },
            "🐟 Seafood": {
                "Fish Fry":               {"price":260, "rating":4.7,"orders":4200, "spice":"Medium"},
                "Prawn Fry":              {"price":380, "rating":4.7,"orders":2400, "spice":"Medium"},
                "Fish Curry":             {"price":280, "rating":4.6,"orders":3200, "spice":"Hot"},
            },
            "🫓 Breads & Rice": {
                "Kothu Parotta (Chicken)":{"price":160, "rating":4.8,"orders":5600, "spice":"Hot"},
                "Parotta (2pcs)":         {"price":50,  "rating":4.7,"orders":7200, "spice":"None"},
                "Steamed Rice":           {"price":50,  "rating":4.5,"orders":4800, "spice":"None"},
            },
        },
        "offers": {
            "PONNU10": {"discount":10,"type":"percent","desc":"10% off all orders","min":200},
            "FLAT60":  {"discount":60,"type":"flat","desc":"₹60 off above ₹350","min":350},
            "FREEDEL": {"discount":40,"type":"delivery","desc":"Free delivery","min":250},
        },
        "reviews": [
            {"name":"Murugan K","rating":5,"date":"1 day ago","text":"Best pepper chicken in Chennai! Kothu parotta is fire 🍗"},
            {"name":"Ramesh P","rating":5,"date":"3 days ago","text":"Authentic Tamil non-veg. Never disappoints! 💯"},
        ],
    },

    "R008": {
        "id": "R008", "type": "nonveg",
        "name": "Hakeem's Biryani",
        "emoji": "🍛", "cuisine": "Biryani Specialist",
        "area": "Perambur", "city": "Chennai",
        "address": "45, Perambur High Road, Chennai 600011",
        "phone": "+91 98840 56789",
        "timing": "11:30 AM – 11:00 PM",
        "rating": 4.7, "reviews": "5,400",
        "delivery_time": "30-45 mins",
        "delivery_charge": 35, "min_order": 200,
        "subscription": "active", "plan": "pro",
        "tags": ["biryani","chicken","mutton","prawn","egg","non veg","dum biryani","family pack","salna"],
        "menu": {
            "🍛 Biryani — Our Specialty": {
                "Chicken Biryani (1 person)": {"price":280,"rating":4.9,"orders":9600,"spice":"Medium"},
                "Mutton Biryani (1 person)":  {"price":360,"rating":4.9,"orders":5600,"spice":"Medium"},
                "Prawn Biryani (1 person)":   {"price":400,"rating":4.8,"orders":2800,"spice":"Medium"},
                "Egg Biryani (1 person)":     {"price":220,"rating":4.7,"orders":4400,"spice":"Medium"},
                "Chicken Biryani (Family)":   {"price":900,"rating":4.9,"orders":2400,"spice":"Medium"},
                "Mutton Biryani (Family)":    {"price":1100,"rating":4.9,"orders":1600,"spice":"Medium"},
            },
            "🥘 Sides & Gravy": {
                "Chicken Salna":          {"price":120, "rating":4.8,"orders":4800, "spice":"Hot"},
                "Mutton Salna":           {"price":160, "rating":4.8,"orders":2800, "spice":"Hot"},
                "Raita":                  {"price":60,  "rating":4.6,"orders":6400, "spice":"None"},
                "Boiled Egg":             {"price":30,  "rating":4.5,"orders":5600, "spice":"None"},
            },
            "🥤 Drinks": {
                "Mango Lassi":            {"price":80,  "rating":4.7,"orders":3200, "spice":"None"},
                "Buttermilk":             {"price":40,  "rating":4.6,"orders":4800, "spice":"None"},
                "Mineral Water":          {"price":20,  "rating":4.0,"orders":8400, "spice":"None"},
            },
        },
        "offers": {
            "BIRYANI10": {"discount":10,"type":"percent","desc":"10% off all biryani","min":250},
            "FAMILY20":  {"discount":20,"type":"percent","desc":"20% off family packs","min":800},
            "FREEDEL":   {"discount":35,"type":"delivery","desc":"Free delivery","min":300},
        },
        "reviews": [
            {"name":"Farhan A","rating":5,"date":"Yesterday","text":"Best dum biryani in North Chennai! Family pack is great value 🍛"},
            {"name":"Priyanka R","rating":5,"date":"3 days ago","text":"Mutton biryani is outstanding! Tender meat, perfect spice! ❤️"},
        ],
    },

    "R009": {
        "id": "R009", "type": "both",
        "name": "Barbeque Nation",
        "emoji": "🔥", "cuisine": "Grills & BBQ",
        "area": "Phoenix Mall, Velachery", "city": "Chennai",
        "address": "Phoenix MarketCity, Velachery Main Road, Chennai 600042",
        "phone": "+91 44 4055 5555",
        "timing": "12:00 PM – 11:00 PM",
        "rating": 4.5, "reviews": "11,200",
        "delivery_time": "45-60 mins",
        "delivery_charge": 60, "min_order": 400,
        "subscription": "active", "plan": "enterprise",
        "tags": ["barbeque","bbq","grill","chicken","mutton","veg","non veg","seekh kebab","tikka","prawns","peri peri","buffet"],
        "menu": {
            "🔥 BBQ & Grills": {
                "Chicken Tikka (6pcs)":   {"price":380, "rating":4.8,"orders":4800, "spice":"Medium"},
                "Mutton Seekh Kebab (4pcs)":{"price":420,"rating":4.8,"orders":3200,"spice":"Medium"},
                "Peri Peri Chicken (6pcs)":{"price":360,"rating":4.7,"orders":3600,"spice":"Hot"},
                "Paneer Tikka (6pcs)":    {"price":320, "rating":4.6,"orders":2800, "spice":"Medium"},
                "Prawn Grill (6pcs)":     {"price":460, "rating":4.7,"orders":2000, "spice":"Medium"},
            },
            "🍛 Mains": {
                "Chicken Biryani":        {"price":380, "rating":4.7,"orders":3600, "spice":"Medium"},
                "Butter Chicken":         {"price":360, "rating":4.8,"orders":3200, "spice":"Mild"},
                "Dal Makhani":            {"price":280, "rating":4.6,"orders":2400, "spice":"Mild"},
                "Paneer Makhani":         {"price":320, "rating":4.6,"orders":2200, "spice":"Mild"},
            },
            "🫓 Breads": {
                "Garlic Naan (2pcs)":     {"price":100, "rating":4.7,"orders":4800, "spice":"None"},
                "Butter Naan (2pcs)":     {"price":90,  "rating":4.6,"orders":4400, "spice":"None"},
            },
            "🍦 Desserts": {
                "Gulab Jamun (4pcs)":     {"price":160, "rating":4.7,"orders":3200, "spice":"None"},
                "Ice Cream":              {"price":140, "rating":4.6,"orders":2800, "spice":"None"},
                "Rasmalai":               {"price":180, "rating":4.7,"orders":2400, "spice":"None"},
            },
        },
        "offers": {
            "BBQ15":   {"discount":15,"type":"percent","desc":"15% off grills","min":400},
            "FLAT150": {"discount":150,"type":"flat","desc":"₹150 off above ₹800","min":800},
            "FREEDEL": {"discount":60,"type":"delivery","desc":"Free delivery","min":600},
        },
        "reviews": [
            {"name":"Vivek S","rating":5,"date":"2 days ago","text":"Amazing BBQ! Peri peri chicken is addictive 🔥"},
        ],
    },

    "R010": {
        "id": "R010", "type": "nonveg",
        "name": "Junior Kuppanna",
        "emoji": "🌺", "cuisine": "Kongu Non-Veg",
        "area": "Mogappair", "city": "Chennai",
        "address": "12, 4th Street, Mogappair West, Chennai 600037",
        "phone": "+91 98420 12345",
        "timing": "11:00 AM – 10:30 PM",
        "rating": 4.6, "reviews": "6,800",
        "delivery_time": "35-50 mins",
        "delivery_charge": 45, "min_order": 200,
        "subscription": "active", "plan": "pro",
        "tags": ["chicken","mutton","biryani","non veg","kongu","tamil","pepper chicken","country chicken","fish","veg thali"],
        "menu": {
            "🍗 Biryani": {
                "Chicken Biryani":        {"price":300, "rating":4.8,"orders":5600, "spice":"Medium"},
                "Mutton Biryani":         {"price":360, "rating":4.7,"orders":3200, "spice":"Medium"},
                "Chicken Kuzhambu Sadam":{"price":280, "rating":4.7,"orders":3600, "spice":"Hot"},
            },
            "🥩 Kongu Specials": {
                "Pepper Chicken":         {"price":340, "rating":4.8,"orders":4400, "spice":"Hot"},
                "Country Chicken Curry":  {"price":420, "rating":4.9,"orders":3800, "spice":"Hot"},
                "Mutton Kuzhambu":        {"price":400, "rating":4.8,"orders":2800, "spice":"Hot"},
                "Chicken Varuval":        {"price":320, "rating":4.7,"orders":3600, "spice":"Hot"},
                "Egg Masala":             {"price":180, "rating":4.5,"orders":2800, "spice":"Medium"},
            },
            "🐟 Seafood": {
                "Fish Kuzhambu":          {"price":300, "rating":4.7,"orders":2800, "spice":"Hot"},
                "Prawn Masala":           {"price":400, "rating":4.7,"orders":2000, "spice":"Hot"},
                "Nethili Fish Fry":       {"price":260, "rating":4.8,"orders":2400, "spice":"Medium"},
            },
            "🫓 Breads & Rice": {
                "Parotta (2pcs)":         {"price":50,  "rating":4.7,"orders":5600, "spice":"None"},
                "Idiyappam + Curry":      {"price":130, "rating":4.7,"orders":3200, "spice":"Medium"},
                "Steamed Rice":           {"price":50,  "rating":4.5,"orders":4200, "spice":"None"},
            },
        },
        "offers": {
            "KUPPANNA10":{"discount":10,"type":"percent","desc":"10% off all orders","min":220},
            "FLAT80":    {"discount":80,"type":"flat","desc":"₹80 off above ₹400","min":400},
            "FREEDEL":   {"discount":45,"type":"delivery","desc":"Free delivery","min":300},
        },
        "reviews": [
            {"name":"Kathir R","rating":5,"date":"1 day ago","text":"Country chicken curry is absolutely divine! Authentic Kongu taste 🌺"},
        ],
    },
}

# ═══════════════════════════════════════════════════════════
# DELIVERY PARTNERS BY AREA
# ═══════════════════════════════════════════════════════════
DELIVERY_PARTNERS = {
    "t nagar":      {"name":"Ramu",   "phone":"+91 98001 11001","rating":4.8},
    "anna nagar":   {"name":"Suresh", "phone":"+91 98001 11002","rating":4.9},
    "velachery":    {"name":"Balu",   "phone":"+91 98001 11003","rating":4.7},
    "anna salai":   {"name":"Kannan", "phone":"+91 98001 11004","rating":4.8},
    "nungambakkam": {"name":"Mani",   "phone":"+91 98001 11005","rating":4.9},
    "vadapalani":   {"name":"Karthik","phone":"+91 98001 11006","rating":4.7},
    "perambur":     {"name":"Raja",   "phone":"+91 98001 11007","rating":4.8},
    "mogappair":    {"name":"Siva",   "phone":"+91 98001 11008","rating":4.8},
}

# ═══════════════════════════════════════════════════════════
# STORAGE
# ═══════════════════════════════════════════════════════════
sessions        = {}
active_orders   = {}
pending_reviews = {}
payout_ledger   = {}
order_history   = []

# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════
def stars(r): return "⭐" * int(r)
def oid(rid): return f"{rid}-{datetime.now().strftime('%d%m%H%M')}{random.randint(10,99)}"

def delivery_partner(area):
    for key, p in DELIVERY_PARTNERS.items():
        if key in area.lower(): return p
    return {"name":"Vijay","phone":"+91 98001 11009","rating":4.7}

def record_payout(rid, order_id, subtotal, del_charge):
    commission = int(subtotal * COMMISSION)
    rest_amt   = subtotal - commission
    if rid not in payout_ledger:
        payout_ledger[rid] = {"pending":0,"paid":0,"orders":0}
    payout_ledger[rid]["pending"] += rest_amt
    payout_ledger[rid]["orders"]  += 1
    order_history.append({
        "oid": order_id, "rid": rid,
        "subtotal": subtotal, "commission": commission,
        "rest": rest_amt, "platform": commission + del_charge,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })

def search_food(query):
    q = query.lower()
    results = []
    for rid, r in RESTAURANTS.items():
        if r.get("subscription") != "active": continue
        matched = any(q in tag or tag in q for tag in r.get("tags", []))
        if not matched:
            for cat, items in r["menu"].items():
                for item in items:
                    if q in item.lower(): matched = True; break
                if matched: break
        if matched: results.append(r)
    return results

def find_item(r, name):
    nl = name.lower()
    for cat, items in r["menu"].items():
        for item, d in items.items():
            if nl in item.lower() or item.lower() in nl:
                return item, d
    return None, None

def apply_coupon(r, code, subtotal):
    code = code.upper().strip()
    o = r.get("offers", {}).get(code)
    if not o: return None, "❌ Invalid coupon. Type *offers* to see valid codes."
    if subtotal < o["min"]: return None, f"❌ Min order ₹{o['min']} needed. Your total: ₹{subtotal}."
    if o["type"] == "percent":
        d = int(subtotal * o["discount"] / 100)
        return d, f"✅ *{code}* applied! {o['discount']}% off = ₹{d} saved 🎉"
    if o["type"] == "flat":
        return o["discount"], f"✅ *{code}* applied! ₹{o['discount']} off 🎉"
    if o["type"] == "delivery":
        return r["delivery_charge"], f"✅ *{code}* applied! Free delivery 🎉"
    return None, "❌ Invalid coupon."

# ═══════════════════════════════════════════════════════════
# DISPLAY BUILDERS
# ═══════════════════════════════════════════════════════════
def welcome():
    veg_count   = sum(1 for r in RESTAURANTS.values() if r["type"] in ["veg","both"])
    nonveg_count= sum(1 for r in RESTAURANTS.values() if r["type"] in ["nonveg","both"])
    total       = len([r for r in RESTAURANTS.values() if r.get("subscription")=="active"])
    return f"""👋 *Welcome to FoodieBot Chennai!* 🍽️
_Order from Chennai's best restaurants!_

━━━━━━━━━━━━━━━━━━━━━━
🟢 *{total} Restaurants* | 🥬 {veg_count} Veg | 🥩 {nonveg_count} Non-Veg

🔍 *Just type what you're craving:*

🥣 _idly_ or _dosa_ — Breakfast spots
🍛 _biryani_ — All biryani restaurants
🌶️ _chicken_ — Chicken dishes
🥩 _mutton_ — Mutton specials
🐟 _fish_ — Seafood spots
🍕 _pizza_ — Fast food
🔥 _barbeque_ — BBQ & Grills

━━━━━━━━━━━━━━━━━━━━━━
*Quick Commands:*
• *all* — All {total} restaurants
• *veg* — Veg only restaurants
• *nonveg* — Non-veg restaurants
• *top* — Highest rated
• *nearby [area]* — By location
• *cheap* — Budget friendly

_Type any food name to start!_ 😊"""

def show_results(query, results):
    t  = f"🔍 *\"{query}\"* found in {len(results)} restaurant(s)\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, r in enumerate(results, 1):
        veg_tag = "🟢 VEG" if r["type"]=="veg" else ("🔴 NON-VEG" if r["type"]=="nonveg" else "🟡 VEG+NON-VEG")
        t += f"{i}️⃣ {r['emoji']} *{r['name']}* {veg_tag}\n"
        t += f"   🍽️ {r['cuisine']}\n"
        t += f"   📍 {r['area']}\n"
        t += f"   ⭐ {r['rating']}/5 ({r['reviews']} reviews)\n"
        t += f"   🛵 {r['delivery_time']} | ₹{r['delivery_charge']} delivery\n"
        t += f"   💰 Min: ₹{r['min_order']}\n"
        preview = [f"{item} ₹{d['price']}" for cat, items in r["menu"].items() for item, d in items.items() if query.lower() in item.lower()][:2]
        if preview: t += f"   🍽️ {' | '.join(preview)}\n"
        t += "\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    for i, r in enumerate(results, 1):
        t += f"Type *{i}* → {r['name']}\n"
    t += "\n_Type another food to search again_ 🔍"
    return t

def show_all(filter_type=None):
    active = [r for r in RESTAURANTS.values() if r.get("subscription")=="active"]
    if filter_type == "veg":
        active = [r for r in active if r["type"] in ["veg","both"]]
        title = "🥬 *Vegetarian Restaurants*"
    elif filter_type == "nonveg":
        active = [r for r in active if r["type"] in ["nonveg","both"]]
        title = "🥩 *Non-Veg Restaurants*"
    else:
        title = "🍽️ *All Restaurants — FoodieBot Chennai*"
    t  = f"{title}\n_{len(active)} restaurants_\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, r in enumerate(active, 1):
        veg_tag = "🟢" if r["type"]=="veg" else ("🔴" if r["type"]=="nonveg" else "🟡")
        t += f"{i}️⃣ {veg_tag} {r['emoji']} *{r['name']}*\n"
        t += f"   {r['cuisine']} | 📍 {r['area']}\n"
        t += f"   ⭐{r['rating']}/5 | 🛵{r['delivery_time']} | Min ₹{r['min_order']}\n\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    for i, r in enumerate(active, 1):
        t += f"Type *{i}* → {r['name']}\n"
    return t, active

def restaurant_home(r):
    veg_tag = "🟢 Pure Veg" if r["type"]=="veg" else ("🔴 Non-Veg" if r["type"]=="nonveg" else "🟡 Veg & Non-Veg")
    t  = f"{r['emoji']} *{r['name']}* {veg_tag}\n"
    t += f"🍽️ {r['cuisine']}\n"
    t += f"📍 {r['address']}\n"
    t += f"⭐ {r['rating']}/5 ({r['reviews']} reviews)\n"
    t += f"⏰ {r['timing']}\n"
    t += f"🛵 {r['delivery_time']} | ₹{r['delivery_charge']} delivery\n"
    t += f"💰 Min order: ₹{r['min_order']}\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    t += "🍽️ *M* — Full Menu\n"
    t += "🏆 *T* — Top Dishes\n"
    t += "🎉 *O* — Today's Offers\n"
    t += "📦 *P* — Place Order\n"
    t += "⭐ *R* — Reviews\n"
    t += "💳 *Y* — Payment Methods\n"
    t += "🔙 *back* — Search Other Restaurants\n\n"
    t += "_Or just tell me what you want!_ 😊"
    return t

def show_menu(r):
    t  = f"🍽️ *{r['name']} — Full Menu*\n"
    t += f"⭐{r['rating']}/5 | Min ₹{r['min_order']}\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for cat, items in r["menu"].items():
        t += f"*{cat}*\n"
        for item, d in items.items():
            spice = f" 🌶️{d['spice']}" if d['spice'] not in ["None","Mild"] else ""
            t += f"  • {item} — ₹{d['price']} {stars(d['rating'])}{spice}\n"
        t += "\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    t += "💰 Type *O* for offers!\n"
    t += "_Tell me what you want to order!_ 🛒"
    return t

def show_top(r):
    items = [(i,d) for cat,its in r["menu"].items() for i,d in its.items()]
    top   = sorted(items, key=lambda x:(x[1]['rating'],x[1]['orders']), reverse=True)[:8]
    t  = f"🏆 *Top Dishes — {r['name']}*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i,(item,d) in enumerate(top,1):
        t += f"{i}. *{item}* — ₹{d['price']}\n"
        t += f"   {stars(d['rating'])} {d['rating']}/5 | {d['orders']:,}+ orders\n\n"
    return t

def show_offers(r):
    t  = f"🎉 *Offers at {r['name']}*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for code, o in r.get("offers",{}).items():
        t += f"🏷️ *{code}*\n   {o['desc']}\n   Min: ₹{o['min']}\n\n"
    t += "Type coupon when ordering | *P* to order 🛒"
    return t

def show_reviews(r):
    revs = r.get("reviews",[])
    t  = f"⭐ *{r['name']} Reviews*\n{r['rating']}/5 ({r['reviews']} reviews)\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for rev in revs:
        t += f"{stars(rev['rating'])} *{rev['name']}*\n_{rev['date']}_\n{rev['text']}\n\n"
    t += "Type *add review* to share yours! 📝"
    return t

def payment_methods():
    return f"""💳 *Payment — FoodieBot*
_Secure payments by NexoraAI_

1️⃣ *Google Pay* 📱
   UPI: `{PLATFORM['upi']}`

2️⃣ *PhonePe* 📱
   UPI: `{PLATFORM['upi']}`

3️⃣ *Any UPI / Paytm*
   UPI ID: `{PLATFORM['upi']}`

4️⃣ *Credit / Debit Card* 💳
   {PLATFORM['card']}

5️⃣ *Cash on Delivery* 💵
   Pay at your door

📸 After payment share screenshot here!
📞 Help: {PLATFORM['phone']}"""

def build_payment_screen(r, items_dict, discount, coupon_type, name, address):
    subtotal = sum(d["price"]*qty for _,(d,qty) in items_dict.items())
    delivery = 0 if coupon_type=="delivery" else r["delivery_charge"]
    total    = subtotal - discount + delivery
    order_id = oid(r["id"])
    partner  = delivery_partner(r["area"])

    gpay    = f"gpay://upi/pay?pa={PLATFORM['upi']}&am={total}&tn=FoodieBot-{order_id}&cu=INR"
    phonepe = f"phonepe://pay?pa={PLATFORM['upi']}&am={total}&tn=FoodieBot-{order_id}&cu=INR"

    t  = f"✅ *Order Summary*\n"
    t += f"Order ID: *{order_id}*\n"
    t += f"Restaurant: *{r['name']}*\n"
    t += f"Customer: {name}\n"
    t += f"Address: {address}\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    for iname,(d,qty) in items_dict.items():
        t += f"• {iname} x{qty} = ₹{d['price']*qty}\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    t += f"📦 Subtotal:  ₹{subtotal}\n"
    if discount > 0: t += f"🎉 Discount: -₹{discount}\n"
    t += f"🛵 Delivery:  ₹{delivery}\n"
    t += f"💰 *Total:    ₹{total}*\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    t += "*Pay Now:*\n\n"
    t += f"1️⃣ *Google Pay* — ₹{total}\n   👉 {gpay}\n\n"
    t += f"2️⃣ *PhonePe* — ₹{total}\n   👉 {phonepe}\n\n"
    t += f"3️⃣ *Any UPI* — ₹{total}\n   👉 `{PLATFORM['upi']}`\n\n"
    t += f"4️⃣ *Card* — ₹{total}\n   👉 {PLATFORM['card']}\n\n"
    t += f"5️⃣ *Cash on Delivery* — ₹{total}\n   Type *cod* to confirm\n\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    t += "📸 After payment: share screenshot ✅\n"
    t += f"🛵 Partner: {partner['name']} ⭐{partner['rating']}\n"
    t += f"⏱️ ETA: {r['delivery_time']}\n"
    t += f"📞 Help: {PLATFORM['phone']}"
    return t, order_id, total, partner

def confirm_msg(r, oid, total, name, partner, method):
    t  = f"🎉 *Order Confirmed!*\n\n"
    t += f"Order ID: *{oid}*\n"
    t += f"Restaurant: *{r['name']}*\n"
    t += f"Amount: ₹{total}\n"
    t += f"Payment: {method}\n"
    t += f"Customer: {name}\n\n"
    t += "━━━━━━━━━━━━━━━━━━━━━━\n"
    t += f"🛵 *Delivery Partner:*\n"
    t += f"   {partner['name']} | ⭐{partner['rating']}\n"
    t += f"   📞 {partner['phone']}\n\n"
    t += f"⏱️ Delivery in {r['delivery_time']}\n"
    t += f"📞 Restaurant: {r['phone']}\n"
    t += f"📞 Platform: {PLATFORM['phone']}\n\n"
    t += "Enjoy your meal! 🍛❤️\n"
    t += "Type *add review* after eating!"
    return t

def ask_gpt(r, sender, text):
    if not OPENAI_KEY:
        return f"Please call {r['phone']} 📞"
    sessions.setdefault(sender,[])
    sessions[sender].append({"role":"user","content":text})
    if len(sessions[sender])>20: sessions[sender]=sessions[sender][-20:]
    menu_str = ", ".join([f"{i} ₹{d['price']}" for cat,its in r["menu"].items() for i,d in its.items()])
    sys = f"""You are FoodieBot assistant for {r['name']} ({r['cuisine']}).
MENU: {menu_str}
DELIVERY: {r['delivery_time']} | Min ₹{r['min_order']} | Charge ₹{r['delivery_charge']}
PAYMENT: All via FoodieBot UPI (nexoraai@upi) — GPay/PhonePe/COD
Help customer order. Be friendly with emojis. Reply in Tamil or English."""
    try:
        resp = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization":f"Bearer {OPENAI_KEY}","Content-Type":"application/json"},
            json={"model":"gpt-3.5-turbo","messages":[{"role":"system","content":sys}]+sessions[sender],"max_tokens":400},
            timeout=30)
        if resp.status_code==200:
            reply = resp.json()["choices"][0]["message"]["content"]
            sessions[sender].append({"role":"assistant","content":reply})
            return reply
    except: pass
    return f"Please call {r['phone']} 📞"

# ═══════════════════════════════════════════════════════════
# MAIN MESSAGE HANDLER
# ═══════════════════════════════════════════════════════════
def handle(sender, text):
    t = text.lower().strip()
    order = active_orders.get(sender, {})
    r = RESTAURANTS.get(order.get("rid")) if order.get("rid") else None

    # BACK
    if t in ["back","home","restart","hi","hello","hey","start","vanakkam"]:
        active_orders.pop(sender,None); sessions.pop(sender,None)
        if t in ["back","home","restart"]:
            return welcome()
        return welcome()

    # REVIEW FLOW
    if sender in pending_reviews:
        pr = pending_reviews[sender]; step = pr.get("step")
        if step=="dish":
            pr["dish"]=text; pr["step"]="rating"
            return "Rate 1-5:\n1️⃣ Poor 2️⃣ Below Avg 3️⃣ Good 4️⃣ Very Good 5️⃣ Excellent ⭐"
        if step=="rating":
            try:
                rating=int(t)
                if 1<=rating<=5:
                    pr["rating"]=rating; pr["step"]="review"
                    return f"Rated {stars(rating)} ({rating}/5)\nTell us your experience 🙏"
            except: pass
            return "Reply with 1-5 ⭐"
        if step=="review":
            dish=pr.get("dish","Overall"); rating=pr.get("rating",5)
            del pending_reviews[sender]
            return f"✅ *Thank You!*\n{dish} — {stars(rating)} ({rating}/5)\n_{text}_\n\n🎁 Free item on next visit! ❤️"
        del pending_reviews[sender]; return "Thank you! 🙏"

    # PAYMENT STEP
    if r and order.get("step")=="payment":
        order_id = order.get("oid", oid(r["id"]))
        total    = order.get("total","?")
        name     = order.get("name","Customer")
        partner  = order.get("partner", delivery_partner(r["area"]))

        if any(x in t for x in ["cod","cash","5"]):
            record_payout(r["id"], order_id, order.get("subtotal",0), r["delivery_charge"])
            del active_orders[sender]
            return confirm_msg(r, order_id, total, name, partner, "Cash on Delivery 💵")

        if any(x in t for x in ["paid","done","sent","screenshot","payment","gpay","phonepe"]):
            record_payout(r["id"], order_id, order.get("subtotal",0), r["delivery_charge"])
            del active_orders[sender]
            return confirm_msg(r, order_id, total, name, partner, "Online Payment ✅")

    # COUPON STEP
    if r and order.get("step")=="coupon":
        subtotal=order.get("subtotal",0); items_dict=order.get("items_dict",{})
        name=order.get("name","Customer"); address=order.get("address","Chennai")
        if t in ["skip","no","none","0"]:
            summary,oid_,total,partner = build_payment_screen(r,items_dict,0,None,name,address)
            active_orders[sender].update({"step":"payment","oid":oid_,"total":total,"partner":partner})
            return summary
        disc,msg = apply_coupon(r,text,subtotal)
        if disc is not None:
            o = r.get("offers",{}).get(text.upper(),{})
            summary,oid_,total,partner = build_payment_screen(r,items_dict,disc,o.get("type"),name,address)
            active_orders[sender].update({"step":"payment","oid":oid_,"total":total,"partner":partner})
            return f"{msg}\n\n{summary}"
        return f"{msg}\n\nType coupon or *skip* to continue."

    # NAME+ADDRESS STEP
    if r and order.get("step")=="name_address" and len(text)>4:
        parts = text.split(",",1)
        name    = parts[0].strip()
        address = parts[1].strip() if len(parts)>1 else r["area"]
        active_orders[sender].update({"name":name,"address":address,"step":"coupon"})
        codes = ", ".join(r.get("offers",{}).keys())
        return f"✅ Saved!\n👤 {name}\n📍 {address}\n\n🎉 *Have a coupon?*\nCodes: *{codes}*\n\nType code or *skip* →"

    # NUMBER SELECTION
    all_list = order.get("all_list",[])
    search_results = order.get("search_results",[])
    current_list = all_list or search_results

    if current_list and t.isdigit():
        idx = int(t)-1
        if 0<=idx<len(current_list):
            sel = current_list[idx]
            active_orders[sender] = {"rid":sel["id"]}
            return restaurant_home(sel)

    # IN RESTAURANT
    if r:
        if t in ["m","menu"]: return show_menu(r)
        if t in ["t","top"]:  return show_top(r)
        if t in ["o","offers","deals"]: return show_offers(r)
        if t in ["r","reviews"]: return show_reviews(r)
        if t in ["y","payment","pay"]: return payment_methods()
        if t in ["p","order","place order"]:
            return f"🛒 Order from *{r['name']}*\n\nTell me what you want!\nExample: _2 Idly and 1 Masala Dosa_\n\nType *O* for offers first!\nMin: ₹{r['min_order']}"
        if any(x in t for x in ["add review","write review","my review"]):
            pending_reviews[sender]={"step":"dish","restaurant":r["name"]}
            return f"📝 Review for *{r['name']}*\n\nWhich dish to review?"
        if t in ["veg","veg items"]:
            veg=[f"• {i} — ₹{d['price']}" for cat,its in r["menu"].items() for i,d in its.items() if d['spice'] in ['None','Mild']]
            return f"🥬 *Mild/Veg at {r['name']}*\n\n"+"\n".join(veg[:10])

        # PARSE ORDER ITEMS
        items_dict={}; total_price=0
        for cat,items in r["menu"].items():
            for iname,details in items.items():
                if iname.lower() in t:
                    words=t.split(); qty=1
                    for i,w in enumerate(words):
                        if w.isdigit() and i+1<len(words) and iname.split()[0].lower() in words[i+1].lower():
                            qty=int(w)
                    items_dict[iname]=(details,qty); total_price+=details["price"]*qty

        if items_dict and total_price>=r["min_order"]:
            active_orders[sender].update({"items_dict":items_dict,"subtotal":total_price,"step":"name_address"})
            preview="\n".join([f"• {n} x{qty}=₹{d['price']*qty}" for n,(d,qty) in items_dict.items()])
            return f"🛒 *Your Order:*\n{preview}\nSubtotal: ₹{total_price}\n\n📋 Share *Name, Address* (comma separated)\nExample: _Raj Kumar, 14 Anna St T Nagar_"

        if items_dict and total_price<r["min_order"]:
            return f"❌ Min order ₹{r['min_order']}. Total: ₹{total_price}. Add more!\nType *M* for menu."

        return ask_gpt(r,sender,text)

    # PLATFORM COMMANDS
    if t in ["all","all restaurants","list"]:
        result,active = show_all()
        active_orders[sender]={"all_list":active}
        return result

    if t in ["veg","pure veg","vegetarian"]:
        result,active = show_all("veg")
        active_orders[sender]={"all_list":active,"filter":"veg"}
        return result

    if t in ["nonveg","non veg","non-veg"]:
        result,active = show_all("nonveg")
        active_orders[sender]={"all_list":active,"filter":"nonveg"}
        return result

    if t in ["top","top rated","best"]:
        sorted_r = sorted(RESTAURANTS.values(), key=lambda x:x["rating"], reverse=True)
        active_orders[sender]={"all_list":sorted_r}
        txt = "🏆 *Top Rated Restaurants*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i,res in enumerate(sorted_r,1):
            vt = "🟢" if res["type"]=="veg" else "🔴"
            txt+=f"{i}️⃣ {vt} {res['emoji']} *{res['name']}*\n   ⭐{res['rating']}/5 | {res['area']}\n\n"
        txt+="Type number to order!"
        return txt

    if t in ["cheap","budget","affordable"]:
        sorted_r=sorted(RESTAURANTS.values(),key=lambda x:x["min_order"])
        active_orders[sender]={"all_list":sorted_r}
        txt="💰 *Budget-Friendly*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i,res in enumerate(sorted_r,1):
            txt+=f"{i}️⃣ {res['emoji']} *{res['name']}*\n   Min: ₹{res['min_order']} | Delivery: ₹{res['delivery_charge']}\n   📍{res['area']}\n\n"
        txt+="Type number to order!"
        return txt

    if t.startswith("nearby ") or t.startswith("area "):
        area = t.replace("nearby ","").replace("area ","").strip()
        results=[res for res in RESTAURANTS.values() if area in res["area"].lower() and res.get("subscription")=="active"]
        if results:
            active_orders[sender]={"all_list":results}
            txt=f"📍 *Restaurants near {area.title()}*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            for i,res in enumerate(results,1):
                txt+=f"{i}️⃣ {res['emoji']} *{res['name']}*\n   ⭐{res['rating']}/5 | {res['delivery_time']}\n\n"
            txt+="Type number to order!"
            return txt
        return f"No restaurants near *{area}*.\nTry: T Nagar, Anna Nagar, Velachery, Vadapalani, Perambur, Mogappair, Nungambakkam"

    # FOOD SEARCH — MAIN FEATURE
    for word in ["i want","i need","give me","show me","order","looking for","want"]:
        t=t.replace(word,"").strip()

    if len(t)>1:
        results=search_food(t)
        if results:
            active_orders[sender]={"search_results":results}
            return show_results(t,results)
        return f"🔍 No results for *\"{t}\"*\n\nTry: idly / dosa / biryani / chicken / fish / pizza / mutton\nOr type *all* to see all restaurants! 🍽️"

    return welcome()

# ═══════════════════════════════════════════════════════════
# FLASK ROUTES
# ═══════════════════════════════════════════════════════════
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    sender = request.form.get("From","")
    text   = request.form.get("Body","").strip()
    media  = int(request.form.get("NumMedia","0"))
    print(f"📱 {sender}: {text[:60]}")
    resp = MessagingResponse()

    # Screenshot = payment confirmation
    if media>0:
        order=active_orders.get(sender,{})
        r=RESTAURANTS.get(order.get("rid"))
        if r and order.get("step")=="payment":
            order_id=order.get("oid",oid(r["id"]))
            total=order.get("total","?"); name=order.get("name","Customer")
            partner=order.get("partner",delivery_partner(r["area"]))
            record_payout(r["id"],order_id,order.get("subtotal",0),r["delivery_charge"])
            del active_orders[sender]
            resp.message(confirm_msg(r,order_id,total,name,partner,"Online Payment (Screenshot) ✅"))
            return str(resp)

    try:
        reply = handle(sender, text)
    except Exception as e:
        print(f"Error: {e}")
        import traceback; traceback.print_exc()
        reply = f"Sorry! Type *hi* to restart or call {PLATFORM['phone']} 🙏"

    resp.message(reply)
    return str(resp)

@app.route("/admin/stats")
def stats():
    if request.args.get("key")!=MASTER_KEY: return jsonify({"error":"Unauthorized"}),401
    active=[r for r in RESTAURANTS.values() if r.get("subscription")=="active"]
    mrr=sum({"starter":2999,"pro":4999,"enterprise":9999}.get(r.get("plan","starter"),2999) for r in active)
    comm=sum(o["commission"] for o in order_history)
    del_rev=sum(o.get("platform",0)-o.get("commission",0) for o in order_history)
    return jsonify({
        "platform":          "FoodieBot Chennai by NexoraAI",
        "total_restaurants": len(RESTAURANTS),
        "active":            len(active),
        "veg_restaurants":   len([r for r in active if r["type"]=="veg"]),
        "nonveg_restaurants":len([r for r in active if r["type"]=="nonveg"]),
        "subscription_mrr":  f"₹{mrr:,}/month",
        "total_orders":      len(order_history),
        "commission_earned": f"₹{comm:,}",
        "delivery_revenue":  f"₹{del_rev:,}",
        "total_revenue":     f"₹{mrr+comm:,}",
    })

@app.route("/admin/payouts")
def payouts():
    if request.args.get("key")!=MASTER_KEY: return jsonify({"error":"Unauthorized"}),401
    result=[]
    for rid,data in payout_ledger.items():
        r=RESTAURANTS.get(rid,{})
        result.append({"restaurant":r.get("name"),"phone":r.get("phone"),"pending":f"₹{data['pending']:,}","orders":data["orders"]})
    total=sum(d["pending"] for d in payout_ledger.values())
    return jsonify({"payouts":result,"total_pending":f"₹{total:,}"})

@app.route("/admin/orders")
def orders():
    if request.args.get("key")!=MASTER_KEY: return jsonify({"error":"Unauthorized"}),401
    return jsonify({"orders":order_history[-50:],"total":len(order_history)})

@app.route("/")
def home():
    active=len([r for r in RESTAURANTS.values() if r.get("subscription")=="active"])
    veg=len([r for r in RESTAURANTS.values() if r["type"]=="veg"])
    nonveg=len([r for r in RESTAURANTS.values() if r["type"]=="nonveg"])
    return f"""
    <h1>🍽️ FoodieBot Chennai</h1>
    <h3>by NexoraAI | {PLATFORM['phone']}</h3>
    <hr>
    <p>✅ Platform Live! | 📦 Orders: {len(order_history)}</p>
    <p>🏪 Total: {len(RESTAURANTS)} | ✅ Active: {active} | 🟢 Veg: {veg} | 🔴 Non-Veg: {nonveg}</p>
    <hr>
    <h3>Restaurants:</h3>
    <ul>{"".join(f"<li>{'🟢' if r['type']=='veg' else '🔴'} {r['emoji']} {r['name']} — {r['area']}</li>" for r in RESTAURANTS.values())}</ul>
    <hr>
    <p>🌐 {PLATFORM['website']}</p>
    """,200

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=False)
