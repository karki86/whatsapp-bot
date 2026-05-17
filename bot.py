"""
FoodieBot Chennai - SuperBot v5 FINAL
NexoraAI | +91 7010624989
Natural voice ordering | Cart CRUD | 4km radius | Min Rs100 guard
"""
import os,re,math,time,uuid,random,datetime,threading,logging
import requests
from flask import Flask,request,jsonify

app=Flask(__name__)
logging.basicConfig(level=logging.INFO)
log=logging.getLogger(__name__)

TWILIO_SID  = os.environ.get("TWILIO_ACCOUNT_SID","")
TWILIO_AUTH = os.environ.get("TWILIO_AUTH_TOKEN","")
TWILIO_FROM = os.environ.get("TWILIO_FROM","whatsapp:+14155238886")
OPENAI_KEY  = os.environ.get("OPENAI_API_KEY","")
ADMIN_KEY   = os.environ.get("ADMIN_KEY","NEXORAAI2026")

PLATFORM={"name":"FoodieBot Chennai","upi":"nexoraai@upi",
           "phone":"+91 7010624989","commission":0.10}
MIN_ORDER  = 100
RADIUS_KM  = 4.0

# ── CHENNAI ZONES ─────────────────────────────────────────────────────────
ZONES={
    "tiruvottiyur":(13.167,80.302,"Tiruvottiyur"),"manali":(13.168,80.262,"Manali"),
    "madhavaram":(13.149,80.229,"Madhavaram"),"kolathur":(13.119,80.220,"Kolathur"),
    "perambur":(13.114,80.246,"Perambur"),"egmore":(13.079,80.261,"Egmore"),
    "park town":(13.081,80.275,"Park Town"),"central":(13.082,80.270,"Chennai Central"),
    "chennai central":(13.082,80.270,"Chennai Central"),"choolai":(13.092,80.258,"Choolai"),
    "kilpauk":(13.089,80.242,"Kilpauk"),"chetpet":(13.080,80.245,"Chetpet"),
    "purasaiwakkam":(13.085,80.248,"Purasaiwakkam"),"vepery":(13.086,80.262,"Vepery"),
    "sowcarpet":(13.090,80.274,"Sowcarpet"),"parrys":(13.092,80.282,"Parrys"),
    "george town":(13.094,80.288,"George Town"),"t nagar":(13.041,80.234,"T Nagar"),
    "tnagar":(13.041,80.234,"T Nagar"),"pondy bazaar":(13.041,80.234,"T Nagar"),
    "kodambakkam":(13.053,80.222,"Kodambakkam"),"ashok nagar":(13.037,80.212,"Ashok Nagar"),
    "vadapalani":(13.053,80.213,"Vadapalani"),"koyambedu":(13.072,80.195,"Koyambedu"),
    "arumbakkam":(13.072,80.213,"Arumbakkam"),"anna nagar":(13.085,80.210,"Anna Nagar"),
    "anna nagar east":(13.084,80.220,"Anna Nagar East"),"mylapore":(13.034,80.269,"Mylapore"),
    "mandaveli":(13.027,80.265,"Mandaveli"),"royapettah":(13.053,80.261,"Royapettah"),
    "nungambakkam":(13.062,80.243,"Nungambakkam"),"alwarpet":(13.038,80.254,"Alwarpet"),
    "teynampet":(13.040,80.249,"Teynampet"),"adyar":(13.006,80.257,"Adyar"),
    "kotturpuram":(13.015,80.247,"Kotturpuram"),"thiruvanmiyur":(12.983,80.259,"Thiruvanmiyur"),
    "besant nagar":(13.000,80.269,"Besant Nagar"),"velachery":(12.978,80.220,"Velachery"),
    "nanganallur":(12.995,80.197,"Nanganallur"),"pallikaranai":(12.937,80.204,"Pallikaranai"),
    "chromepet":(12.951,80.142,"Chromepet"),"tambaram":(12.924,80.100,"Tambaram"),
    "guindy":(13.006,80.220,"Guindy"),"saidapet":(13.022,80.229,"Saidapet"),
    "porur":(13.037,80.157,"Porur"),"poonamallee":(13.048,80.097,"Poonamallee"),
    "ambattur":(13.114,80.162,"Ambattur"),"avadi":(13.115,80.098,"Avadi"),
    "mogappair":(13.093,80.168,"Mogappair"),"omr":(12.901,80.227,"OMR"),
    "sholinganallur":(12.901,80.227,"Sholinganallur"),"perungudi":(12.965,80.243,"Perungudi"),
    "taramani":(12.985,80.240,"Taramani"),"siruseri":(12.856,80.218,"Siruseri"),
    "navalur":(12.842,80.227,"Navalur"),"kelambakkam":(12.787,80.210,"Kelambakkam"),
    "neelankarai":(12.952,80.252,"Neelankarai"),"palavakkam":(12.945,80.250,"Palavakkam"),
    "boat club":(13.029,80.255,"Boat Club"),"gopalapuram":(13.042,80.257,"Gopalapuram"),
    "valasaravakkam":(13.037,80.176,"Valasaravakkam"),"saligramam":(13.047,80.187,"Saligramam"),
    "padi":(13.108,80.199,"Padi"),"virugambakkam":(13.055,80.194,"Virugambakkam"),
}

# ── RESTAURANTS ────────────────────────────────────────────────────────────
RESTAURANTS={
"saravana":{"name":"Hotel Saravana Bhavan","emoji":"🥣","cuisine":"South Indian Veg","type":"veg",
    "area":"T Nagar","lat":13.040,"lng":80.233,"address":"77, Usman Rd, T Nagar",
    "phone":"+91 44 28340000","rating":4.6,"reviews":2340,"delivery_time":"25-35 min",
    "delivery_charge":30,"min_order":150,"timing":"6AM-11PM","subscription":"active",
    "menu":{
        "Breakfast":{
            "Idly 2pcs":        {"price":50, "veg":True},
            "Masala Dosa":      {"price":90, "veg":True},
            "Pongal":           {"price":70, "veg":True},
            "Rava Upma":        {"price":60, "veg":True},
            "Vada":             {"price":30, "veg":True},
            "Sambar Vada":      {"price":50, "veg":True},
            "Mini Tiffin Combo":{"price":120,"veg":True},
        },
        "Meals":{
            "Full Meals":       {"price":180,"veg":True},
            "Mini Meals":       {"price":140,"veg":True},
            "Curd Rice":        {"price":80, "veg":True},
        },
        "Drinks":{
            "Filter Coffee":    {"price":40, "veg":True},
            "Buttermilk":       {"price":30, "veg":True},
        },
    },
    "offers":{
        "SB10":   {"type":"percent","discount":10,"min":200,"desc":"10% off Rs200+"},
        "MORNING":{"type":"flat","discount":30,"min":150,"desc":"Rs30 off breakfast"},
    },
    "partners":[{"name":"Rajan K","phone":"+91 9876500001","rating":4.8},
                {"name":"Muthu S","phone":"+91 9876500002","rating":4.7}]},

"anjappar":{"name":"Anjappar Chettinad","emoji":"🍗","cuisine":"Chettinad Non-Veg","type":"nonveg",
    "area":"Anna Nagar","lat":13.084,"lng":80.210,"address":"Shop 7, 2nd Ave, Anna Nagar",
    "phone":"+91 44 26261616","rating":4.5,"reviews":1820,"delivery_time":"35-50 min",
    "delivery_charge":40,"min_order":300,"timing":"11AM-11PM","subscription":"active",
    "menu":{
        "Biryani":{
            "Chicken Biryani":  {"price":280,"veg":False},
            "Mutton Biryani":   {"price":380,"veg":False},
            "Egg Biryani":      {"price":220,"veg":False},
            "Prawn Biryani":    {"price":420,"veg":False},
        },
        "Gravy":{
            "Chicken Chettinad":{"price":320,"veg":False},
            "Mutton Pepper Fry":{"price":420,"veg":False},
            "Fish Curry":       {"price":300,"veg":False},
        },
        "Starters":{
            "Chicken 65":       {"price":260,"veg":False},
            "Mutton Sukka":     {"price":360,"veg":False},
            "Prawn Fry":        {"price":340,"veg":False},
        },
    },
    "offers":{
        "CHETTINAD15":{"type":"percent","discount":15,"min":500,"desc":"15% off Rs500+"},
        "FREEDEL":    {"type":"delivery","discount":40,"min":400,"desc":"Free delivery Rs400+"},
    },
    "partners":[{"name":"Kumar R","phone":"+91 9876500003","rating":4.6},
                {"name":"Pradeep M","phone":"+91 9876500004","rating":4.9}]},

"murugan":{"name":"Murugan Idli Shop","emoji":"🫕","cuisine":"Traditional Tiffin","type":"veg",
    "area":"Mylapore","lat":13.034,"lng":80.269,"address":"77, Luz Church Rd, Mylapore",
    "phone":"+91 44 28113455","rating":4.7,"reviews":3100,"delivery_time":"20-30 min",
    "delivery_charge":25,"min_order":100,"timing":"6AM-10PM","subscription":"active",
    "menu":{
        "Signature":{
            "Soft Idly 4pcs":   {"price":80, "veg":True},
            "Ghee Idly 2pcs":   {"price":90, "veg":True},
            "Sambar Vada":      {"price":70, "veg":True},
            "Set Dosa":         {"price":100,"veg":True},
            "Podi Idly":        {"price":90, "veg":True},
            "Vada":             {"price":35, "veg":True},
            "Medu Vada":        {"price":40, "veg":True},
        },
        "Combos":{
            "Idly Vada Combo":  {"price":130,"veg":True},
            "Dosa Sambar Combo":{"price":140,"veg":True},
            "Breakfast Thali":  {"price":180,"veg":True},
        },
    },
    "offers":{
        "MURUGAN20":{"type":"flat","discount":20,"min":150,"desc":"Rs20 off Rs150+"},
    },
    "partners":[{"name":"Selvam T","phone":"+91 9876500005","rating":4.7}]},

"buhari":{"name":"Buhari Restaurant","emoji":"🍖","cuisine":"Mughlai Biryani","type":"nonveg",
    "area":"Egmore","lat":13.079,"lng":80.261,"address":"83, Anna Salai, Egmore",
    "phone":"+91 44 28521001","rating":4.4,"reviews":2780,"delivery_time":"40-55 min",
    "delivery_charge":45,"min_order":350,"timing":"12PM-12AM","subscription":"active",
    "menu":{
        "Biryani":{
            "Buhari Special Biryani":{"price":350,"veg":False},
            "Mutton Dum Biryani":    {"price":420,"veg":False},
            "Chicken Dum Biryani":   {"price":320,"veg":False},
            "Veg Biryani":           {"price":220,"veg":True},
        },
        "Kebab":{
            "Chicken Seekh Kebab":   {"price":340,"veg":False},
            "Tandoori Chicken Half": {"price":360,"veg":False},
        },
        "Gravy":{
            "Butter Chicken":        {"price":320,"veg":False},
            "Dal Makhani":           {"price":200,"veg":True},
        },
    },
    "offers":{
        "BUHARI50": {"type":"flat","discount":50,"min":500,"desc":"Rs50 off Rs500+"},
        "NIGHTOWL": {"type":"percent","discount":20,"min":400,"desc":"20% off after 9PM"},
    },
    "partners":[{"name":"Arjun P","phone":"+91 9876500006","rating":4.5},
                {"name":"Dinesh K","phone":"+91 9876500007","rating":4.6}]},

"cream_centre":{"name":"Cream Centre","emoji":"🍕","cuisine":"Multi-Cuisine Veg","type":"veg",
    "area":"Nungambakkam","lat":13.062,"lng":80.243,"address":"7, Khader Nawaz Khan Rd",
    "phone":"+91 44 28331234","rating":4.3,"reviews":1560,"delivery_time":"30-45 min",
    "delivery_charge":35,"min_order":250,"timing":"12PM-11PM","subscription":"active",
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
            "Veggie Supreme":       {"price":320,"veg":True},
        },
        "Desserts":{
            "Hot Chocolate Fudge":  {"price":220,"veg":True},
            "Brownie Sundae":       {"price":200,"veg":True},
        },
    },
    "offers":{
        "PIZZA20":{"type":"percent","discount":20,"min":300,"desc":"20% off pizza"},
    },
    "partners":[{"name":"Vinoth S","phone":"+91 9876500008","rating":4.8}]},

"kaaraikudi":{"name":"Kaaraikudi Chettinad","emoji":"🍛","cuisine":"Authentic Chettinad","type":"nonveg",
    "area":"Velachery","lat":12.978,"lng":80.220,"address":"45, 100 Ft Rd, Velachery",
    "phone":"+91 98412 00000","rating":4.6,"reviews":980,"delivery_time":"30-45 min",
    "delivery_charge":35,"min_order":250,"timing":"11AM-10:30PM","subscription":"active",
    "menu":{
        "Biryani":{
            "Kaaraikudi Mutton Biryani":{"price":400,"veg":False},
            "Chicken Biryani":           {"price":280,"veg":False},
        },
        "Specials":{
            "Chettinad Fish Fry":        {"price":320,"veg":False},
            "Chicken Kuzhambu":          {"price":300,"veg":False},
            "Quail Kaadai Fry":          {"price":380,"veg":False},
        },
    },
    "offers":{
        "KAAR10":{"type":"percent","discount":10,"min":300,"desc":"10% off Rs300+"},
    },
    "partners":[{"name":"Balu K","phone":"+91 9876500009","rating":4.7}]},

"bombay_bakery":{"name":"Bombay Bakery Cafe","emoji":"🥐","cuisine":"Bakery Snacks Chai","type":"veg",
    "area":"Adyar","lat":13.006,"lng":80.257,"address":"12, LB Rd, Adyar",
    "phone":"+91 98400 11111","rating":4.5,"reviews":710,"delivery_time":"15-25 min",
    "delivery_charge":20,"min_order":80,"timing":"7AM-10PM","subscription":"active",
    "menu":{
        "Bakery":{
            "Veg Puff":         {"price":35, "veg":True},
            "Egg Puff":         {"price":40, "veg":False},
            "Croissant":        {"price":60, "veg":True},
            "Samosa 2pcs":      {"price":50, "veg":True},
            "Bread Toast":      {"price":45, "veg":True},
        },
        "Cafe":{
            "Masala Chai":      {"price":40, "veg":True},
            "Cold Coffee":      {"price":80, "veg":True},
        },
        "Sweets":{
            "Gulab Jamun 2pcs": {"price":60, "veg":True},
            "Carrot Halwa":     {"price":80, "veg":True},
        },
    },
    "offers":{
        "CHAI5":{"type":"flat","discount":20,"min":100,"desc":"Rs20 off Rs100+"},
    },
    "partners":[{"name":"Suresh A","phone":"+91 9876500010","rating":4.9}]},

"seafood_bay":{"name":"Chennai Seafood Bay","emoji":"🦐","cuisine":"Coastal Seafood","type":"nonveg",
    "area":"Besant Nagar","lat":13.000,"lng":80.269,"address":"18, 4th Ave, Besant Nagar",
    "phone":"+91 98765 22222","rating":4.7,"reviews":1240,"delivery_time":"35-50 min",
    "delivery_charge":50,"min_order":400,"timing":"12PM-11PM","subscription":"active",
    "menu":{
        "Starters":{
            "Prawn Masala Fry":      {"price":380,"veg":False},
            "Fish Fingers":          {"price":280,"veg":False},
            "Squid Pepper Fry":      {"price":360,"veg":False},
        },
        "Mains":{
            "Prawn Biryani":         {"price":440,"veg":False},
            "Fish Curry Rice":       {"price":320,"veg":False},
            "Mixed Seafood Rice":    {"price":420,"veg":False},
        },
    },
    "offers":{
        "SEAFRESH":{"type":"percent","discount":12,"min":500,"desc":"12% off Rs500+"},
        "FREESHIP": {"type":"delivery","discount":50,"min":600,"desc":"Free delivery Rs600+"},
    },
    "partners":[{"name":"Fisher K","phone":"+91 9876500011","rating":4.6},
                {"name":"Mohan G","phone":"+91 9876500012","rating":4.8}]},
}

sessions={};user_state={};orders={};payouts={}

# ── GEO ───────────────────────────────────────────────────────────────────
def hav(la1,lg1,la2,lg2):
    R=6371;dl=math.radians(la2-la1);dg=math.radians(lg2-lg1)
    a=math.sin(dl/2)**2+math.cos(math.radians(la1))*math.cos(math.radians(la2))*math.sin(dg/2)**2
    return R*2*math.asin(math.sqrt(a))

def zone_from_ll(la,lg):
    best,bd=None,9999
    for k,(zl,zg,zn) in ZONES.items():
        d=hav(la,lg,zl,zg)
        if d<bd:bd,best=d,zn
    return best or "Chennai"

def zone_from_text(txt):
    t=txt.lower().strip()
    for k,(zl,zg,zn) in ZONES.items():
        if k in t or t in k:return zn,zl,zg
    return None

def rests_near(la,lg,limit=8,radius=None):
    active=[(rid,r) for rid,r in RESTAURANTS.items() if r.get("subscription")=="active"]
    res=[(hav(la,lg,r["lat"],r["lng"]),rid,r) for rid,r in active]
    if radius:res=[x for x in res if x[0]<=radius]
    res.sort(key=lambda x:x[0]);return res[:limit]

# ── TIME GREETING ─────────────────────────────────────────────────────────
def greet():
    ist=datetime.timezone(datetime.timedelta(hours=5,minutes=30))
    h=datetime.datetime.now(ist).hour
    if 5<=h<12:return "Good morning! ☀️","breakfast",["idly","vada","dosa","pongal","chai"]
    elif 12<=h<15:return "Good afternoon! 🌤","lunch",["biryani","meals","chicken","fish"]
    elif 15<=h<18:return "Good evening! ☕","snacks",["puff","chai","samosa","coffee"]
    elif 18<=h<22:return "Good evening! 🌆","dinner",["biryani","chicken","mutton","seafood"]
    else:return "Night owl! 🌙","late night",["biryani","chicken","pizza","kebab"]

# ════════════════════════════════════════════════════════════════════════════
#  NATURAL VOICE ORDER ENGINE
#  Understands: "2 idly 1 vada", "give me chicken biryani",
#               "idly rendu vada onnu", "biryani", "vada 3"
#  No rigid format required - customer talks naturally
# ════════════════════════════════════════════════════════════════════════════

# Word numbers (English + Tamil + Hindi)
WORD_NUMS={
    # English
    "one":1,"two":2,"three":3,"four":4,"five":5,
    "six":6,"seven":7,"eight":8,"nine":9,"ten":10,
    # Tamil
    "onnu":1,"rendu":2,"moonnu":3,"naalu":4,"anju":5,
    "aaru":6,"ezhu":7,"ettu":8,"ombodhu":9,"pathu":10,
    "oru":1,"irandu":2,"moonu":3,"nalu":4,
    # Hindi
    "ek":1,"do":2,"teen":3,"char":4,"paanch":5,
    "chhe":6,"saat":7,"aath":8,"nau":9,"das":10,
}

# FILLER WORDS to remove before parsing
FILLERS=r'\b(give me|i want|i need|send me|get me|can i get|please|order|'\
        r'want to order|i would like|can you send|also|and|with|some|the|'\
        r'a plate of|plate of|nos|no\.|pieces|piece|pcs|pc|nos\.)\b'

def build_voice_aliases(r):
    """
    Build alias map for a restaurant's menu.
    Maps every natural way a customer might say an item to the canonical menu name.
    """
    aliases={}
    for cat,items in r["menu"].items():
        for item_name,d in items.items():
            canon=item_name
            key=item_name.lower()
            # Add exact menu name
            aliases[key]=canon
            # Add without numbers in name (e.g. "Soft Idly 4pcs" -> "soft idly")
            stripped=re.sub(r'\d+(pcs|pc|nos|pieces)?','',key).strip()
            if stripped and stripped!=key:aliases[stripped]=canon
            # Add first word only if unique enough (3+ chars)
            first=key.split()[0]
            if len(first)>=3:aliases.setdefault(first,canon)

    # Universal food aliases (common variations customers type)
    UNIVERSAL={
        # Idly
        "idly":"Idly 2pcs","idli":"Idly 2pcs","idlies":"Idly 2pcs",
        "soft idly":"Soft Idly 4pcs","ghee idly":"Ghee Idly 2pcs",
        "soft idli":"Soft Idly 4pcs","ghee idli":"Ghee Idly 2pcs",
        "podi idly":"Podi Idly","podi idli":"Podi Idly",
        # Vada
        "vada":"Vada","vadai":"Vada","vadas":"Vada","wada":"Vada",
        "medu vada":"Medu Vada","meduvada":"Medu Vada","meduvadai":"Medu Vada",
        "sambar vada":"Sambar Vada","sambarvada":"Sambar Vada",
        # Dosa
        "dosa":"Masala Dosa","dosai":"Masala Dosa","thosai":"Masala Dosa",
        "masala dosa":"Masala Dosa","set dosa":"Set Dosa","setdosa":"Set Dosa",
        # Biryani
        "biryani":"Chicken Biryani","biriyani":"Chicken Biryani","briyani":"Chicken Biryani",
        "chicken biryani":"Chicken Biryani","chicken biriyani":"Chicken Biryani",
        "mutton biryani":"Mutton Biryani","mutton biriyani":"Mutton Biryani",
        "egg biryani":"Egg Biryani","prawn biryani":"Prawn Biryani",
        "veg biryani":"Veg Biryani",
        # Chicken
        "chicken 65":"Chicken 65","c65":"Chicken 65","chicken65":"Chicken 65",
        "butter chicken":"Butter Chicken",
        # Coffee / Chai
        "coffee":"Filter Coffee","kaapi":"Filter Coffee","filter coffee":"Filter Coffee",
        "chai":"Masala Chai","tea":"Masala Chai","masala chai":"Masala Chai",
        "cold coffee":"Cold Coffee",
        # Puff
        "puff":"Veg Puff","veg puff":"Veg Puff","egg puff":"Egg Puff",
        # Misc
        "pongal":"Pongal","upma":"Rava Upma","rava upma":"Rava Upma",
        "meals":"Full Meals","full meals":"Full Meals","mini meals":"Mini Meals",
        "curd rice":"Curd Rice","buttermilk":"Buttermilk",
        "combo":"Idly Vada Combo","idly vada":"Idly Vada Combo",
        "pizza":"Margherita Pizza","margherita":"Margherita Pizza",
        "paneer":"Paneer Butter Masala","paneer tikka":"Paneer Tikka",
        "fish curry":"Fish Curry","fish":"Fish Curry Rice",
        "prawn":"Prawn Masala Fry","prawns":"Prawn Masala Fry",
    }
    # Merge universal into aliases (menu-specific names take priority)
    for k,v in UNIVERSAL.items():
        aliases.setdefault(k,v)

    return aliases

def extract_num(token):
    """Extract quantity from a token — digit or word number."""
    t=token.strip().lower()
    if t.isdigit():return int(t)
    return WORD_NUMS.get(t,None)

def voice_parse(text,r):
    """
    Parse natural voice order text into (item_name, price, qty) list.

    Handles all these formats naturally:
      "2 idly 1 vada"
      "idly 2 vada 1"
      "give me chicken biryani and vada"
      "I want 3 dosa"
      "biryani"
      "chicken biryani 2 and chicken 65 one"
      "idly rendu vada onnu"  (Tamil numbers)
      "send me 2 dosa and 1 coffee"
    """
    # Step 1: Get all aliases for this restaurant
    aliases=build_voice_aliases(r)

    # Step 2: Clean filler words
    cleaned=re.sub(FILLERS,' ',text.lower().strip())
    cleaned=re.sub(r'\s+',' ',cleaned).strip()

    # Step 3: Greedy match aliases, longest first
    sorted_keys=sorted(aliases.keys(),key=lambda x:-len(x))
    found={}   # item_name -> qty
    used=[]    # list of (start,end) spans already consumed

    for alias in sorted_keys:
        # Only look for aliases that exist in this restaurant's menu
        target=aliases[alias]
        in_menu=any(
            target==item
            for cat,items in r["menu"].items()
            for item in items
        )
        if not in_menu:continue

        pattern=r'\b'+re.escape(alias)+r'\b'
        for m in re.finditer(pattern,cleaned):
            s,e=m.start(),m.end()
            # Skip overlapping spans
            if any(ps<=s<pe or ps<e<=pe for ps,pe in used):continue

            qty=1
            # Look for number BEFORE alias
            before_txt=cleaned[:s].strip()
            before_toks=before_txt.split()
            q_before=extract_num(before_toks[-1]) if before_toks else None

            # Look for number AFTER alias
            after_txt=cleaned[e:].strip()
            after_toks=after_txt.split()
            q_after=extract_num(after_toks[0]) if after_toks else None

            if q_before:
                qty=q_before
            elif q_after:
                qty=q_after

            found[target]=found.get(target,0)+qty
            used.append((s,e))

    # Return as list of (name, price, qty)
    result=[]
    for item_name,qty in found.items():
        price=0
        for cat,items in r["menu"].items():
            if item_name in items:
                price=items[item_name]["price"]
                break
        result.append((item_name,price,max(1,min(qty,20))))
    return result

# ── FOOD SEARCH ───────────────────────────────────────────────────────────
def food_search(query,ftype=None,ulat=None,ulng=None,radius=RADIUS_KM):
    q=query.lower()
    # Normalize common aliases in search
    SEARCH_MAP={"biriyani":"biryani","briyani":"biryani","dosai":"dosa",
                "thosai":"dosa","idli":"idly","vadai":"vada","prawns":"prawn"}
    q=SEARCH_MAP.get(q,q)
    res=[]
    for rid,r in RESTAURANTS.items():
        if r.get("subscription")!="active":continue
        if ftype=="veg" and r["type"] not in["veg","both"]:continue
        if ftype=="nonveg" and r["type"] not in["nonveg","both"]:continue
        dist=hav(ulat,ulng,r["lat"],r["lng"]) if ulat else None
        if dist is not None and dist>radius:continue
        matched=[f"{item} Rs{d['price']}"
                 for cat,items in r["menu"].items()
                 for item,d in items.items()
                 if q in item.lower() or any(w in item.lower() for w in q.split())]
        if matched:res.append((dist,rid,r,matched[:3]))
    if ulat:res.sort(key=lambda x:x[0] if x[0] is not None else 9999)
    return res

# ── CART HELPERS ──────────────────────────────────────────────────────────
def cart_sub(cart):return sum(d["price"]*d["qty"] for d in cart.values())

def fuzzy_cart(q,cart):
    q=q.lower()
    for item in cart:
        if q in item.lower() or item.lower() in q:return item
    return None

def fuzzy_menu(q,r):
    q=q.lower();best=None
    for cat,items in r["menu"].items():
        for nm,d in items.items():
            if q in nm.lower() or nm.lower() in q:
                if not best or len(nm)<len(best[0]):best=(nm,d["price"])
    return best

def coupon_apply(r,code,sub):
    o=r.get("offers",{}).get(code.upper())
    if not o:return None,f"Coupon *{code}* not found. Type *offers* to see valid codes."
    if sub<o["min"]:return None,f"Min order Rs{o['min']} needed. Your total: Rs{sub}."
    if o["type"]=="percent":
        d=int(sub*o["discount"]/100)
        return d,f"*{code}* applied! {o['discount']}% off = *Rs{d} saved* ✅"
    if o["type"]=="flat":
        return o["discount"],f"*{code}* applied! *Rs{o['discount']} off* ✅"
    if o["type"]=="delivery":
        return r["delivery_charge"],f"*{code}* applied! *Free delivery* ✅"
    return None,"Invalid coupon."

# ── MESSAGE BUILDERS ──────────────────────────────────────────────────────
def msg_welcome(zone=None):
    g,meal,foods=greet()
    az=f" | 📍 {zone}" if zone else ""
    sug=" | ".join([f"_{f}_" for f in foods[:4]])
    n=len([r for r in RESTAURANTS.values() if r.get("subscription")=="active"])
    return(
        f"👋 *Welcome to FoodieBot Chennai!*{az}\n"
        f"_NexoraAI SuperBot v5_\n\n"
        f"{g} Time for *{meal}*!\n"
        f"Try: {sug}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 *Share your location*\n"
        f"_(tap 📎 attachment → Location)_\n"
        f"_Shows restaurants within {RADIUS_KM}km_\n\n"
        f"🗣️ *Just type what you want to eat:*\n"
        f"_idly_ · _biryani_ · _dosa_ · _chicken_ · _fish_\n\n"
        f"*Commands:*\n"
        f"nearby · area T Nagar · veg · top · all\n\n"
        f"_{n} restaurants ready to deliver!_ 🍽️"
    )

def msg_location(zone,nearby):
    if not nearby:
        return(
            f"📍 You're near *{zone}*\n\n"
            f"No restaurants within {RADIUS_KM}km right now.\n"
            f"Type *all* to see all Chennai restaurants\n"
            f"Or *area [zone]* to search elsewhere"
        )
    t=f"📍 You're near *{zone}*\n"
    t+=f"_Showing within {RADIUS_KM}km_\n\n"
    t+="🍽️ *Restaurants near you:*\n"
    t+="━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i,(d,rid,r) in enumerate(nearby,1):
        v="🟢" if r["type"]=="veg" else"🔴"
        t+=f"{i}. {r['emoji']} *{r['name']}* {v}\n"
        t+=f"   📍 {r['area']} — *{d:.1f}km away*\n"
        t+=f"   ⭐ {r['rating']}/5 | 🛵 {r['delivery_time']}\n"
        t+=f"   💰 Min Rs{r['min_order']} | Delivery Rs{r['delivery_charge']}\n\n"
    t+="━━━━━━━━━━━━━━━━━━━━━━\n"
    for i,(d,rid,r) in enumerate(nearby,1):
        t+=f"Type *{i}* to order from {r['name']}\n"
    t+="\n_Just type food name to search_ 🔍"
    return t

def msg_search(query,results):
    has_loc=results and results[0][0] is not None
    note=f" within {RADIUS_KM}km" if has_loc else""
    t=f"🔍 *{query}* — {len(results)} place(s){note}\n"
    t+="━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i,(d,rid,r,matched) in enumerate(results,1):
        v="🟢" if r["type"]=="veg" else"🔴"
        ds=f" — *{d:.1f}km*" if d is not None else""
        t+=f"{i}. {r['emoji']} *{r['name']}* {v}\n"
        t+=f"   📍 {r['area']}{ds} | ⭐ {r['rating']}/5\n"
        t+=f"   🛵 {r['delivery_time']} | Rs{r['delivery_charge']} delivery\n"
        t+=f"   🍽️ {' · '.join(matched)}\n\n"
    t+="━━━━━━━━━━━━━━━━━━━━━━\n"
    for i,(d,rid,r,_) in enumerate(results,1):
        t+=f"Type *{i}* to order from {r['name']}\n"
    return t

def msg_all(ulat=None,ulng=None,zone=None,radius=RADIUS_KM):
    if ulat:nearby=rests_near(ulat,ulng,20,radius)
    else:nearby=[(None,rid,r) for rid,r in RESTAURANTS.items() if r.get("subscription")=="active"]
    zn=f" near *{zone}* ({radius}km)" if zone else" — all Chennai"
    t=f"🍽️ *FoodieBot Restaurants*{zn}\n"
    t+=f"_{len(nearby)} found_\n"
    t+="━━━━━━━━━━━━━━━━━━━━━━\n\n"
    if not nearby:
        return t+f"No restaurants within {radius}km.\nType *area [zone]* to expand.",[]
    for i,(d,rid,r) in enumerate(nearby,1):
        v="🟢" if r["type"]=="veg" else"🔴"
        ds=f" | *{d:.1f}km*" if d is not None else""
        t+=f"{i}. {r['emoji']} *{r['name']}* {v}\n"
        t+=f"   📍 {r['area']}{ds} | ⭐ {r['rating']}/5\n"
        t+=f"   🛵 {r['delivery_time']} | Min Rs{r['min_order']}\n\n"
    t+="━━━━━━━━━━━━━━━━━━━━━━\n"
    for i,(d,rid,r) in enumerate(nearby,1):
        t+=f"Type *{i}* to order from {r['name']}\n"
    return t,nearby

def msg_menu(r):
    t=f"{r['emoji']} *{r['name']}*\n"
    t+=f"🍽️ {r['cuisine']}\n"
    t+=f"📍 {r['address']}\n"
    t+=f"⭐ {r['rating']}/5 ({r['reviews']} reviews)\n"
    t+=f"🛵 {r['delivery_time']} | Rs{r['delivery_charge']} delivery\n"
    t+=f"💰 Min order: Rs{r['min_order']}\n"
    t+=f"⏰ {r['timing']}\n"
    t+="━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for cat,items in r["menu"].items():
        t+=f"*{cat}*\n"
        for item,d in items.items():
            tag="🟢" if d.get("veg") else"🔴"
            t+=f"  {tag} {item} — Rs{d['price']}\n"
        t+="\n"
    t+="━━━━━━━━━━━━━━━━━━━━━━\n"
    t+="_Just type what you want to order:_\n"
    t+="_e.g. idly, vada, chicken biryani_\n\n"
    if r.get("offers"):
        t+="🎁 *Offers:*\n"
        for code,o in r["offers"].items():
            t+=f"  *{code}* — {o['desc']}\n"
    return t

def msg_cart(r,cart,disc=0):
    sub=cart_sub(cart);total=sub+r["delivery_charge"]-disc
    t=f"🛒 *Your Cart — {r['name']}*\n"
    t+="━━━━━━━━━━━━━━━━━━━━━━\n"
    if not cart:
        t+="_Cart is empty._\n"
    else:
        for i,(item,d) in enumerate(cart.items(),1):
            t+=f"{i}. {item} ×{d['qty']} = Rs{d['price']*d['qty']}\n"
    t+="━━━━━━━━━━━━━━━━━━━━━━\n"
    t+=f"Subtotal:  Rs{sub}\n"
    t+=f"Delivery:  Rs{r['delivery_charge']}\n"
    if disc:t+=f"Discount: -Rs{disc}\n"
    t+=f"*Total:    Rs{total}*\n\n"
    # Min order warnings
    if 0<sub<MIN_ORDER:
        t+=f"⚠️ Min order is Rs{MIN_ORDER}. Add Rs{MIN_ORDER-sub} more.\n\n"
    elif 0<sub<r["min_order"]:
        t+=f"⚠️ {r['name']} needs min Rs{r['min_order']}. Add Rs{r['min_order']-sub} more.\n\n"
    t+="━━━━━━━━━━━━━━━━━━━━━━\n"
    t+="*What would you like to do?*\n"
    t+="• *checkout* — place order\n"
    t+="• *remove vada* — remove an item\n"
    t+="• *update idly 3* — change quantity\n"
    t+="• *clear* — empty cart\n"
    t+="• *coupon CODE* — apply discount\n"
    t+="• *menu* — back to menu"
    return t

def msg_payment(total,r):
    return(
        f"💳 *Payment — Rs{total}*\n\n"
        f"Pay to: *{PLATFORM['upi']}*\n"
        f"Amount: *Rs{total}*\n\n"
        f"📱 *Quick Pay:*\n"
        f"GPay: gpay://upi/pay?pa={PLATFORM['upi']}&am={total}\n"
        f"PhonePe: phonepe://pay?pa={PLATFORM['upi']}&am={total}\n\n"
        f"Reply *paid* — after UPI payment\n"
        f"Reply *cod* — Cash on Delivery"
    )

def msg_confirm(oid,r,name,total,ptype,partner):
    return(
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ *Order Confirmed!*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Order ID: *{oid}*\n"
        f"Restaurant: *{r['name']}*\n"
        f"Customer: {name}\n"
        f"Amount: Rs{total}\n"
        f"Payment: {ptype}\n\n"
        f"🛵 *Your Delivery Partner:*\n"
        f"   {partner['name']} | {partner['phone']} | ⭐{partner['rating']}\n\n"
        f"⏱️ Estimated: {r['delivery_time']}\n"
        f"📞 Help: {PLATFORM['phone']}\n\n"
        f"Thank you for ordering on FoodieBot! 🍛\n"
        f"_Type *review* after eating_ 😊"
    )

# ── TWILIO SEND ───────────────────────────────────────────────────────────
def send_wa(to,body):
    sid=os.environ.get("TWILIO_ACCOUNT_SID","")
    auth=os.environ.get("TWILIO_AUTH_TOKEN","")
    frm=os.environ.get("TWILIO_FROM","whatsapp:+14155238886")
    if not sid or not auth:
        log.warning(f"[DRY RUN -> {to}]\n{body}")
        return
    to_n=f"whatsapp:{to}" if not to.startswith("whatsapp:") else to
    for chunk in[body[i:i+1500] for i in range(0,len(body),1500)]:
        try:
            resp=requests.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                auth=(sid,auth),
                data={"From":frm,"To":to_n,"Body":chunk},
                timeout=15
            )
            log.info(f"[SENT] {resp.status_code} -> {to_n}")
            if resp.status_code not in(200,201):
                log.error(f"[TWILIO ERR] {resp.text[:150]}")
        except Exception as e:
            log.error(f"[SEND ERR] {e}")

# ── CORE HANDLER ──────────────────────────────────────────────────────────
def handle(sender,body,lat=None,lng=None):
    text=(body or"").strip();lower=text.lower();now=time.time()
    s=user_state.setdefault(sender,{
        "step":"home","cart":{},"restaurant":None,
        "name":None,"address":None,"disc":0,
        "results":[],"lat":None,"lng":None,"zone":None,
        "order_total":0,"last":now,
    })
    s["last"]=now

    # ── LOCATION PIN ───────────────────────────────────────────────────────
    if lat and lng:
        la,ln=float(lat),float(lng)
        s["lat"]=la;s["lng"]=ln
        zone=zone_from_ll(la,ln);s["zone"]=zone
        nearby=rests_near(la,ln,8,RADIUS_KM)
        s["results"]=[(d,rid,r) for d,rid,r in nearby]
        s["step"]="home"
        return msg_location(zone,nearby)

    ul=s.get("lat");ug=s.get("lng");uz=s.get("zone")

    # ── NUMBER SELECTION ───────────────────────────────────────────────────
    if text.isdigit() and s["step"] in("home","search","area_search","all_list"):
        idx=int(text)-1;res=s.get("results",[])
        if res and 0<=idx<len(res):
            e=res[idx];rid,r=e[1],e[2]
            s["restaurant"]=rid;s["cart"]={};s["disc"]=0;s["step"]="rest"
            return msg_menu(r)
        return"Please pick a number from the list above."

    # ── RESTAURANT FLOW ────────────────────────────────────────────────────
    if s["step"]=="rest" and s.get("restaurant"):
        r=RESTAURANTS[s["restaurant"]]

        # VIEW CART
        if lower in("cart","view cart","my cart","show cart","basket"):
            return msg_cart(r,s["cart"],s["disc"])

        # CLEAR
        if lower in("clear","clear cart","empty cart","reset","start over"):
            s["cart"]={};s["disc"]=0
            return"🗑️ Cart cleared!\n_Type what you want to eat_ 😊"

        # REMOVE — "remove vada" / "delete idly" / "cancel biryani"
        m=re.match(r'^(remove|delete|cancel|rm|take out|drop)\s+(.+)$',lower)
        if m:
            matched=fuzzy_cart(m.group(2).strip(),s["cart"])
            if matched:
                del s["cart"][matched]
                sub=cart_sub(s["cart"])
                tot=sub+r["delivery_charge"]-s["disc"]
                t=f"✅ *{matched}* removed.\n\n"
                t+=f"🛒 Cart: Rs{tot} ({len(s['cart'])} item(s))\n"
                if sub<MIN_ORDER and sub>0:
                    t+=f"⚠️ Add Rs{MIN_ORDER-sub} more for min order.\n"
                t+="Type *cart* to review | *checkout* to order"
                return t
            return f"❌ *{m.group(2)}* not in cart.\nType *cart* to see your items."

        # UPDATE QTY — "update vada 3" / "change idly 2" / "make it 2 vada"
        m=re.match(r'^(update|change|set|qty|make it|modify)\s+(.+?)\s+(\d+)$',lower)
        if m:
            q=m.group(2).strip();nq=int(m.group(3))
            matched=fuzzy_cart(q,s["cart"])
            if not matched:
                mm=fuzzy_menu(q,r)
                if mm:
                    s["cart"][mm[0]]={"price":mm[1],"qty":nq}
                    return f"✅ *{mm[0]}* ×{nq} added.\n\n"+msg_cart(r,s["cart"],s["disc"])
                return f"❌ *{q}* not found in menu.\nType *menu* to see items."
            if nq<=0:
                del s["cart"][matched]
                return f"✅ *{matched}* removed.\n\n"+msg_cart(r,s["cart"],s["disc"])
            s["cart"][matched]["qty"]=nq
            return f"✅ *{matched}* updated to ×{nq}.\n\n"+msg_cart(r,s["cart"],s["disc"])

        # CHECKOUT
        if lower in("checkout","place order","order","confirm","buy","done ordering"):
            if not s["cart"]:
                return"🛒 Cart is empty!\n_Just type what you want to eat_ 😊"
            sub=cart_sub(s["cart"])
            if sub<MIN_ORDER:
                return(
                    f"⚠️ *Minimum order is Rs{MIN_ORDER}.*\n"
                    f"Your cart is Rs{sub}. Add Rs{MIN_ORDER-sub} more.\n\n"
                    +msg_cart(r,s["cart"],s["disc"])
                )
            if sub<r["min_order"]:
                return(
                    f"⚠️ *{r['name']} requires min Rs{r['min_order']}.*\n"
                    f"Add Rs{r['min_order']-sub} more.\n\n"
                    +msg_cart(r,s["cart"],s["disc"])
                )
            s["step"]="get_name"
            return"📦 Almost there!\nWhat's your *name* for the delivery?"

        # COUPON
        if lower.startswith("coupon ") or lower.startswith("apply "):
            code=text.split(" ",1)[1].strip()
            sub=cart_sub(s["cart"])
            disc,msg=coupon_apply(r,code,sub)
            if disc:s["disc"]=disc
            return msg

        # OFFERS
        if lower in("offers","coupons","discount","promo","deals"):
            off=r.get("offers",{})
            if not off:return"No active offers right now. Check back later!"
            t="🎁 *Active Offers:*\n\n"
            for code,o in off.items():
                t+=f"  *{code}* — {o['desc']}\n"
            return t+"\nType *coupon CODE* to apply"

        # MENU / BACK
        if lower in("menu","back","more","show menu","see menu"):
            return msg_menu(r)

        # ══════════════════════════════════════════════════════════════════
        # VOICE ORDER ENGINE
        # Customer just types naturally — no format required
        # "idly" / "2 idly 1 vada" / "give me chicken biryani" / "biryani"
        # ══════════════════════════════════════════════════════════════════
        voice_items=voice_parse(text,r)
        if voice_items:
            added=[]
            for nm,price,qty in voice_items:
                if nm in s["cart"]:
                    s["cart"][nm]["qty"]+=qty
                else:
                    s["cart"][nm]={"price":price,"qty":qty}
                added.append(f"*{nm}* ×{qty}")

            sub=cart_sub(s["cart"])
            tot=sub+r["delivery_charge"]-s["disc"]

            t=f"✅ *Added to cart:*\n"
            for a in added:t+=f"  {a}\n"
            t+=f"\n🛒 Cart total: Rs{tot} ({len(s['cart'])} item(s))\n"

            if sub<MIN_ORDER:
                t+=f"\n⚠️ Add Rs{MIN_ORDER-sub} more for Rs{MIN_ORDER} min order."
            else:
                t+=f"\nType *checkout* to place order | *cart* to review | add more items"
            return t

        # GPT fallback
        if OPENAI_KEY:
            sessions.setdefault(sender,[])
            sessions[sender].append({"role":"user","content":text})
            if len(sessions[sender])>20:sessions[sender]=sessions[sender][-20:]
            mn=", ".join([f"{i} Rs{d['price']}" for c,it in r["menu"].items() for i,d in it.items()])
            sys_p=(f"You are a friendly WhatsApp food ordering assistant for {r['name']} "
                   f"({r['cuisine']}) on FoodieBot Chennai. "
                   f"MENU: {mn}. "
                   f"Help the customer order. Be brief and friendly. Use emojis sparingly.")
            try:
                resp=requests.post("https://api.openai.com/v1/chat/completions",
                    headers={"Authorization":f"Bearer {OPENAI_KEY}","Content-Type":"application/json"},
                    json={"model":"gpt-4o-mini",
                          "messages":[{"role":"system","content":sys_p}]+sessions[sender],
                          "max_tokens":200},timeout=10)
                rep=resp.json()["choices"][0]["message"]["content"]
                sessions[sender].append({"role":"assistant","content":rep})
                return rep
            except:pass

        # Soft fallback — show cart + menu hint
        return(
            f"I didn't catch that 🙂\n\n"
            f"Just type what you want:\n"
            f"_e.g. idly, vada, chicken biryani_\n\n"
            f"Or type *menu* to see all items | *cart* to review"
        )

    # ── ORDER STEPS ────────────────────────────────────────────────────────
    if s["step"]=="get_name":
        s["name"]=text;s["step"]="get_address"
        hint=f"\n_(near {uz})_" if uz else""
        return f"🏠 Thanks *{text}*!\nWhat's your *delivery address*?{hint}"

    if s["step"]=="get_address":
        s["address"]=text
        if not uz:
            m=zone_from_text(text)
            if m:s["zone"]=m[0];s["lat"]=m[1];s["lng"]=m[2]
        r=RESTAURANTS[s["restaurant"]]
        sub=cart_sub(s["cart"])
        tot=sub+r["delivery_charge"]-s["disc"]
        s["order_total"]=tot;s["step"]="payment"
        return msg_payment(tot,r)

    if s["step"]=="payment":
        if lower in("paid","done","upi done","gpay","phonepe","paytm","paid done"):
            pt="UPI"
        elif lower in("cod","cash","cash on delivery","pay on delivery"):
            pt="COD"
        else:
            return"💳 Reply *paid* after UPI payment\nOr reply *cod* for Cash on Delivery"
        r=RESTAURANTS[s["restaurant"]]
        partner=random.choice(r["partners"])
        oid="FB"+str(uuid.uuid4())[:6].upper()
        total=s.get("order_total",0)
        orders[oid]={
            "restaurant":s["restaurant"],"name":s["name"],
            "address":s["address"],"cart":s["cart"].copy(),
            "total":total,"payment":pt,"partner":partner,
            "time":datetime.datetime.now().isoformat(),"sender":sender,
        }
        comm=int(total*PLATFORM["commission"])
        payouts[s["restaurant"]]=payouts.get(s["restaurant"],0)+(total-comm)
        msg=msg_confirm(oid,r,s["name"],total,pt,partner)
        s.update({"step":"home","cart":{},"restaurant":None,"disc":0,"results":[]})
        return msg

    # ── HOME COMMANDS ──────────────────────────────────────────────────────
    if lower in("hi","hello","hey","start","hii","help","menu","hai"):
        return msg_welcome(uz)

    if lower in("nearby","near me","closest","restaurants near me"):
        if ul:
            nb=rests_near(ul,ug,8,RADIUS_KM)
            s["results"]=[(d,rid,r) for d,rid,r in nb];s["step"]="home"
            return msg_location(uz or"your area",nb)
        return(
            "📍 *Share your location first!*\n"
            "_(tap 📎 attachment → Location in WhatsApp)_\n\n"
            "Or type: *area T Nagar* / *area Adyar* / *area OMR*"
        )

    if lower.startswith("area "):
        aq=text[5:].strip()
        m=zone_from_text(aq)
        if m:
            zn,zl,zg=m;s.update({"zone":zn,"lat":zl,"lng":zg})
            nb=rests_near(zl,zg,8,RADIUS_KM)
            s["results"]=[(d,rid,r) for d,rid,r in nb];s["step"]="area_search"
            return msg_location(zn,nb)
        return(
            f"😕 Couldn't find *{aq}* in Chennai.\n"
            "Try: T Nagar · Adyar · Velachery · Anna Nagar · OMR · Mylapore"
        )

    if lower=="all":
        result=msg_all(ul,ug,uz,radius=RADIUS_KM if ul else None)
        if isinstance(result,tuple):msg,nb=result
        else:msg,nb=result,[]
        s["results"]=[(d,rid,r) for d,rid,r in nb];s["step"]="all_list"
        return msg

    if lower in("veg","vegetarian","veg only","veg food"):
        veg=[(hav(ul,ug,r["lat"],r["lng"]) if ul else 0,rid,r)
             for rid,r in RESTAURANTS.items()
             if r.get("subscription")=="active" and r["type"] in("veg","both")
             and(ul is None or hav(ul,ug,r["lat"],r["lng"])<=RADIUS_KM)]
        if ul:veg.sort(key=lambda x:x[0])
        s["results"]=veg;s["step"]="home"
        if not veg:
            return f"No veg restaurants within {RADIUS_KM}km.\nType *area [zone]* to search elsewhere."
        t=f"🟢 *Veg Restaurants* (within {RADIUS_KM}km)\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i,(d,rid,r) in enumerate(veg,1):
            ds=f" | {d:.1f}km" if ul else""
            t+=f"{i}. {r['emoji']} *{r['name']}*{ds}\n   📍 {r['area']} | ⭐{r['rating']}/5\n\n"
        t+="━━━━━━━━━━━━━━━━━━━━━━\n"
        for i,(_,rid,r) in enumerate(veg,1):t+=f"Type *{i}* to order from {r['name']}\n"
        return t

    if lower in("top","best","top rated","highest rated"):
        ranked=sorted(
            [(rid,r) for rid,r in RESTAURANTS.items() if r.get("subscription")=="active"],
            key=lambda x:x[1]["rating"],reverse=True
        )
        s["results"]=[(0,rid,r) for rid,r in ranked];s["step"]="home"
        t="⭐ *Top Rated Restaurants*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i,(rid,r) in enumerate(ranked,1):
            t+=f"{i}. {r['emoji']} *{r['name']}* — ⭐{r['rating']}/5\n   📍 {r['area']} | {r['cuisine']}\n\n"
        t+="━━━━━━━━━━━━━━━━━━━━━━\n"
        for i,(rid,r) in enumerate(ranked,1):t+=f"Type *{i}* to order from {r['name']}\n"
        return t

    if lower in("cheap","budget","affordable","low price"):
        cheap=sorted(
            [(rid,r) for rid,r in RESTAURANTS.items() if r.get("subscription")=="active"],
            key=lambda x:x[1]["min_order"]
        )
        s["results"]=[(0,rid,r) for rid,r in cheap];s["step"]="home"
        t="💰 *Budget Restaurants*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i,(rid,r) in enumerate(cheap,1):
            t+=f"{i}. {r['emoji']} *{r['name']}* — Min Rs{r['min_order']}\n   📍 {r['area']}\n\n"
        t+="━━━━━━━━━━━━━━━━━━━━━━\n"
        for i,(rid,r) in enumerate(cheap,1):t+=f"Type *{i}* to order from {r['name']}\n"
        return t

    if lower.startswith("review"):
        return"⭐ Share your review:\nhttps://g.page/foodiebot-chennai\n_Thank you!_ 🙏"

    if lower in("","?","options","what can you do"):
        _,meal,foods=greet()
        sug=" | ".join([f"_{f}_" for f in foods[:4]])
        return(
            f"🔥 Popular *{meal}* picks:\n{sug}\n\n"
            f"Just type a food name to search! 🍽️\n"
            f"Or: *nearby* · *veg* · *top* · *all*"
        )

    # ── FOOD SEARCH (default) ──────────────────────────────────────────────
    results=food_search(lower,ulat=ul,ulng=ug,radius=RADIUS_KM)
    if results:
        s["results"]=results;s["step"]="search"
        return msg_search(lower,results)

    # Nothing found
    _,meal,foods=greet()
    sug=" | ".join([f"_{f}_" for f in foods[:3]])
    return(
        f"😕 No result for *{lower}*.\n\n"
        f"Popular *{meal}* picks: {sug}\n\n"
        f"Type *all* to browse all restaurants"
    )

# ── FLASK ROUTES ──────────────────────────────────────────────────────────
@app.route("/")
def index():return"FoodieBot SuperBot v5 is live! 🚀",200

@app.route("/health")
def health():
    return jsonify({
        "status":"ok","version":"SuperBot v5",
        "restaurants":len(RESTAURANTS),
        "radius_km":RADIUS_KM,"min_order":MIN_ORDER,
        "twilio_ok":bool(os.environ.get("TWILIO_ACCOUNT_SID")),
    })

@app.route("/debug/env")
def debug_env():
    sid=os.environ.get("TWILIO_ACCOUNT_SID","")
    auth=os.environ.get("TWILIO_AUTH_TOKEN","")
    frm=os.environ.get("TWILIO_FROM","")
    return jsonify({
        "TWILIO_ACCOUNT_SID":sid[:8]+"..." if sid else"MISSING",
        "TWILIO_AUTH_TOKEN":auth[:8]+"..." if auth else"MISSING",
        "TWILIO_FROM":frm or"MISSING",
        "status":"ok" if sid and auth else"MISSING CREDENTIALS",
    })

@app.route("/webhook",methods=["GET","POST"])
def webhook():
    if request.method=="GET":return"FoodieBot webhook live!",200
    sender=request.form.get("From","").replace("whatsapp:","")
    body=request.form.get("Body","").strip()
    lat=request.form.get("Latitude")
    lng=request.form.get("Longitude")
    log.info(f"[IN] from={sender!r} body={body!r}")
    if not sender:return jsonify({"status":"no sender"}),400
    # Background thread — returns 200 to Twilio instantly
    def bg():
        try:
            rep=handle(sender,body,lat,lng)
            log.info(f"[OUT] len={len(rep)}")
            send_wa(sender,rep)
        except Exception as e:
            log.error(f"[ERR] {e}")
    threading.Thread(target=bg,daemon=True).start()
    return jsonify({"status":"ok"}),200

def aauth():return request.args.get("key")==ADMIN_KEY

@app.route("/admin/orders")
def admin_orders():
    if not aauth():return jsonify({"error":"unauthorized"}),401
    return jsonify({"total":len(orders),"orders":orders})

@app.route("/admin/stats")
def admin_stats():
    if not aauth():return jsonify({"error":"unauthorized"}),401
    rev=sum(o["total"] for o in orders.values())
    return jsonify({
        "total_orders":len(orders),"total_revenue":rev,
        "commission":int(rev*PLATFORM["commission"]),
        "active_restaurants":len([r for r in RESTAURANTS.values() if r.get("subscription")=="active"]),
        "active_sessions":len(user_state),
    })

@app.route("/admin/payouts")
def admin_payouts():
    if not aauth():return jsonify({"error":"unauthorized"}),401
    return jsonify({"payouts":payouts})

@app.route("/admin/broadcast")
def admin_broadcast():
    if not aauth():return jsonify({"error":"unauthorized"}),401
    _,meal,foods=greet();sug=" | ".join(foods[:3]);count=0
    for sender,state in user_state.items():
        if time.time()-state.get("last",0)<86400:
            m=(f"🔥 Craving *{meal}*?\n"
               f"Popular now: {sug}\n\n"
               f"Reply to order on FoodieBot Chennai! 🍽️")
            threading.Thread(target=send_wa,args=(sender,m),daemon=True).start()
            count+=1
    return jsonify({"broadcast_sent":count,"meal":meal})

if __name__=="__main__":
    app.run(debug=True,port=10000)
