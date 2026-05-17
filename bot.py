"""
FoodieBot Chennai - SuperBot v6 PRODUCTION READY
NexoraAI | +91 7010624989 | nexoraaiagen@gmail.com

Fine-tuning in v6:
  - Food search shows nearby restaurant automatically (no location needed)
  - Area name typed directly shows restaurants + food prompt
  - Smart search: sort by distance, show delivery ETA, price, rating
  - Return customer greeting with last order + reorder option
  - Voice order: any natural language, Tamil/Hindi numbers
  - Cart CRUD: remove/update/clear with live total
  - Min Rs100 guard with item suggestions to reach minimum
  - Address auto-fill from previous order
  - Proactive upsell: "Add X to unlock free delivery"
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
    "tiruvottiyur":(13.167,80.302,"Tiruvottiyur"),
    "manali":(13.168,80.262,"Manali"),
    "madhavaram":(13.149,80.229,"Madhavaram"),
    "kolathur":(13.119,80.220,"Kolathur"),
    "perambur":(13.114,80.246,"Perambur"),
    "vyasarpadi":(13.106,80.249,"Vyasarpadi"),
    "tondiarpet":(13.109,80.281,"Tondiarpet"),
    "royapuram":(13.108,80.293,"Royapuram"),
    "egmore":(13.079,80.261,"Egmore"),
    "park town":(13.081,80.275,"Park Town"),
    "central":(13.082,80.270,"Chennai Central"),
    "chennai central":(13.082,80.270,"Chennai Central"),
    "choolai":(13.092,80.258,"Choolai"),
    "aminjikarai":(13.089,80.237,"Aminjikarai"),
    "kilpauk":(13.089,80.242,"Kilpauk"),
    "chetpet":(13.080,80.245,"Chetpet"),
    "purasaiwakkam":(13.085,80.248,"Purasaiwakkam"),
    "vepery":(13.086,80.262,"Vepery"),
    "sowcarpet":(13.090,80.274,"Sowcarpet"),
    "parrys":(13.092,80.282,"Parrys"),
    "george town":(13.094,80.288,"George Town"),
    "t nagar":(13.041,80.234,"T Nagar"),
    "tnagar":(13.041,80.234,"T Nagar"),
    "pondy bazaar":(13.041,80.234,"T Nagar"),
    "kodambakkam":(13.053,80.222,"Kodambakkam"),
    "ashok nagar":(13.037,80.212,"Ashok Nagar"),
    "vadapalani":(13.053,80.213,"Vadapalani"),
    "koyambedu":(13.072,80.195,"Koyambedu"),
    "arumbakkam":(13.072,80.213,"Arumbakkam"),
    "virugambakkam":(13.055,80.194,"Virugambakkam"),
    "valasaravakkam":(13.037,80.176,"Valasaravakkam"),
    "saligramam":(13.047,80.187,"Saligramam"),
    "anna nagar":(13.085,80.210,"Anna Nagar"),
    "anna nagar east":(13.084,80.220,"Anna Nagar East"),
    "mylapore":(13.034,80.269,"Mylapore"),
    "mandaveli":(13.027,80.265,"Mandaveli"),
    "royapettah":(13.053,80.261,"Royapettah"),
    "nungambakkam":(13.062,80.243,"Nungambakkam"),
    "alwarpet":(13.038,80.254,"Alwarpet"),
    "teynampet":(13.040,80.249,"Teynampet"),
    "gopalapuram":(13.042,80.257,"Gopalapuram"),
    "boat club":(13.029,80.255,"Boat Club"),
    "adyar":(13.006,80.257,"Adyar"),
    "kotturpuram":(13.015,80.247,"Kotturpuram"),
    "thiruvanmiyur":(12.983,80.259,"Thiruvanmiyur"),
    "besant nagar":(13.000,80.269,"Besant Nagar"),
    "neelankarai":(12.952,80.252,"Neelankarai"),
    "palavakkam":(12.945,80.250,"Palavakkam"),
    "sholinganallur":(12.901,80.227,"Sholinganallur"),
    "perungudi":(12.965,80.243,"Perungudi"),
    "taramani":(12.985,80.240,"Taramani"),
    "velachery":(12.978,80.220,"Velachery"),
    "nanganallur":(12.995,80.197,"Nanganallur"),
    "pallikaranai":(12.937,80.204,"Pallikaranai"),
    "chromepet":(12.951,80.142,"Chromepet"),
    "tambaram":(12.924,80.100,"Tambaram"),
    "guindy":(13.006,80.220,"Guindy"),
    "ekkatuthangal":(13.016,80.207,"Ekkatuthangal"),
    "saidapet":(13.022,80.229,"Saidapet"),
    "little mount":(13.020,80.223,"Little Mount"),
    "porur":(13.037,80.157,"Porur"),
    "poonamallee":(13.048,80.097,"Poonamallee"),
    "ambattur":(13.114,80.162,"Ambattur"),
    "avadi":(13.115,80.098,"Avadi"),
    "mogappair":(13.093,80.168,"Mogappair"),
    "padi":(13.108,80.199,"Padi"),
    "omr":(12.901,80.227,"OMR"),
    "siruseri":(12.856,80.218,"Siruseri"),
    "navalur":(12.842,80.227,"Navalur"),
    "kelambakkam":(12.787,80.210,"Kelambakkam"),
}

# ── RESTAURANTS ────────────────────────────────────────────────────────────
RESTAURANTS={
"saravana":{"name":"Hotel Saravana Bhavan","emoji":"🥣","cuisine":"South Indian Veg","type":"veg",
    "area":"T Nagar","lat":13.040,"lng":80.233,"address":"77, Usman Rd, T Nagar",
    "phone":"+91 44 28340000","rating":4.6,"reviews":2340,"delivery_time":"25-35 min",
    "delivery_charge":30,"min_order":150,"timing":"6AM-11PM","subscription":"active",
    "menu":{
        "Breakfast":{
            "Idly 2pcs":        {"price":50,"veg":True},
            "Masala Dosa":      {"price":90,"veg":True},
            "Pongal":           {"price":70,"veg":True},
            "Rava Upma":        {"price":60,"veg":True},
            "Vada":             {"price":30,"veg":True},
            "Sambar Vada":      {"price":50,"veg":True},
            "Mini Tiffin Combo":{"price":120,"veg":True},
        },
        "Meals":{
            "Full Meals":       {"price":180,"veg":True},
            "Mini Meals":       {"price":140,"veg":True},
            "Curd Rice":        {"price":80,"veg":True},
        },
        "Drinks":{
            "Filter Coffee":    {"price":40,"veg":True},
            "Buttermilk":       {"price":30,"veg":True},
        },
    },
    "offers":{"SB10":{"type":"percent","discount":10,"min":200,"desc":"10% off Rs200+"},
              "MORNING":{"type":"flat","discount":30,"min":150,"desc":"Rs30 off breakfast"}},
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
    "offers":{"CHETTINAD15":{"type":"percent","discount":15,"min":500,"desc":"15% off Rs500+"},
              "FREEDEL":{"type":"delivery","discount":40,"min":400,"desc":"Free delivery Rs400+"}},
    "partners":[{"name":"Kumar R","phone":"+91 9876500003","rating":4.6},
                {"name":"Pradeep M","phone":"+91 9876500004","rating":4.9}]},

"murugan":{"name":"Murugan Idli Shop","emoji":"🫕","cuisine":"Traditional Tiffin","type":"veg",
    "area":"Mylapore","lat":13.034,"lng":80.269,"address":"77, Luz Church Rd, Mylapore",
    "phone":"+91 44 28113455","rating":4.7,"reviews":3100,"delivery_time":"20-30 min",
    "delivery_charge":25,"min_order":100,"timing":"6AM-10PM","subscription":"active",
    "menu":{
        "Signature":{
            "Soft Idly 4pcs":   {"price":80,"veg":True},
            "Ghee Idly 2pcs":   {"price":90,"veg":True},
            "Sambar Vada":      {"price":70,"veg":True},
            "Set Dosa":         {"price":100,"veg":True},
            "Podi Idly":        {"price":90,"veg":True},
            "Vada":             {"price":35,"veg":True},
            "Medu Vada":        {"price":40,"veg":True},
        },
        "Combos":{
            "Idly Vada Combo":  {"price":130,"veg":True},
            "Dosa Sambar Combo":{"price":140,"veg":True},
            "Breakfast Thali":  {"price":180,"veg":True},
        },
    },
    "offers":{"MURUGAN20":{"type":"flat","discount":20,"min":150,"desc":"Rs20 off Rs150+"}},
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
    "offers":{"BUHARI50":{"type":"flat","discount":50,"min":500,"desc":"Rs50 off Rs500+"},
              "NIGHTOWL":{"type":"percent","discount":20,"min":400,"desc":"20% off after 9PM"}},
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
    "offers":{"PIZZA20":{"type":"percent","discount":20,"min":300,"desc":"20% off pizza"}},
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
    "offers":{"KAAR10":{"type":"percent","discount":10,"min":300,"desc":"10% off Rs300+"}},
    "partners":[{"name":"Balu K","phone":"+91 9876500009","rating":4.7}]},

"bombay_bakery":{"name":"Bombay Bakery Cafe","emoji":"🥐","cuisine":"Bakery Snacks Chai","type":"veg",
    "area":"Adyar","lat":13.006,"lng":80.257,"address":"12, LB Rd, Adyar",
    "phone":"+91 98400 11111","rating":4.5,"reviews":710,"delivery_time":"15-25 min",
    "delivery_charge":20,"min_order":80,"timing":"7AM-10PM","subscription":"active",
    "menu":{
        "Bakery":{
            "Veg Puff":         {"price":35,"veg":True},
            "Egg Puff":         {"price":40,"veg":False},
            "Croissant":        {"price":60,"veg":True},
            "Samosa 2pcs":      {"price":50,"veg":True},
            "Bread Toast":      {"price":45,"veg":True},
        },
        "Cafe":{
            "Masala Chai":      {"price":40,"veg":True},
            "Cold Coffee":      {"price":80,"veg":True},
        },
        "Sweets":{
            "Gulab Jamun 2pcs": {"price":60,"veg":True},
            "Carrot Halwa":     {"price":80,"veg":True},
        },
    },
    "offers":{"CHAI5":{"type":"flat","discount":20,"min":100,"desc":"Rs20 off Rs100+"}},
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
    "offers":{"SEAFRESH":{"type":"percent","discount":12,"min":500,"desc":"12% off Rs500+"},
              "FREESHIP":{"type":"delivery","discount":50,"min":600,"desc":"Free delivery Rs600+"}},
    "partners":[{"name":"Fisher K","phone":"+91 9876500011","rating":4.6},
                {"name":"Mohan G","phone":"+91 9876500012","rating":4.8}]},
}

# ── STATE ──────────────────────────────────────────────────────────────────
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
    """Match any part of text against known zone names."""
    t=txt.lower().strip()
    # Exact match first
    for k,(zl,zg,zn) in ZONES.items():
        if t==k:return zn,zl,zg
    # Substring match
    for k,(zl,zg,zn) in ZONES.items():
        if k in t:return zn,zl,zg
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
#  Supports: "idly", "2 idly 1 vada", "give me biryani",
#            "idly rendu vada onnu" (Tamil), "ek biryani do vada" (Hindi)
# ════════════════════════════════════════════════════════════════════════════
WORD_NUMS={
    "one":1,"two":2,"three":3,"four":4,"five":5,
    "six":6,"seven":7,"eight":8,"nine":9,"ten":10,
    "onnu":1,"rendu":2,"moonnu":3,"naalu":4,"anju":5,
    "oru":1,"irandu":2,"moonu":3,"nalu":4,
    "ek":1,"do":2,"teen":3,"char":4,"paanch":5,
}
FILLERS=r'\b(give me|i want|i need|send me|get me|can i get|please|order|'\
        r'want to order|would like|also|and|with|some|the|a plate of|plate of|'\
        r'nos|pieces|piece|pcs|pc|just|only)\b'

def build_aliases(r):
    """Build natural language aliases for every item in a restaurant menu."""
    aliases={}
    for cat,items in r["menu"].items():
        for nm,d in items.items():
            # Exact name
            aliases[nm.lower()]=nm
            # Without numbers (e.g. "soft idly 4pcs" → "soft idly")
            stripped=re.sub(r'\d+(pcs|pc|nos|pieces)?','',nm.lower()).strip()
            if stripped and stripped!=nm.lower():
                aliases.setdefault(stripped,nm)
            # First meaningful word
            first=nm.lower().split()[0]
            if len(first)>=4:aliases.setdefault(first,nm)

    # Universal food aliases
    UNIVERSAL={
        "idly":None,"idli":None,"idlies":None,
        "soft idly":"Soft Idly 4pcs","ghee idly":"Ghee Idly 2pcs",
        "soft idli":"Soft Idly 4pcs","ghee idli":"Ghee Idly 2pcs",
        "podi idly":"Podi Idly","podi idli":"Podi Idly",
        "vada":None,"vadai":None,"vadas":None,"wada":None,
        "medu vada":"Medu Vada","meduvada":"Medu Vada","meduvadai":"Medu Vada",
        "sambar vada":"Sambar Vada","sambarvada":"Sambar Vada",
        "dosa":None,"dosai":None,"thosai":None,
        "masala dosa":"Masala Dosa","set dosa":"Set Dosa","setdosa":"Set Dosa",
        "biryani":None,"biriyani":None,"briyani":None,
        "chicken biryani":"Chicken Biryani","chicken biriyani":"Chicken Biryani",
        "mutton biryani":"Mutton Biryani","mutton biriyani":"Mutton Biryani",
        "egg biryani":"Egg Biryani","prawn biryani":"Prawn Biryani",
        "veg biryani":"Veg Biryani",
        "chicken 65":"Chicken 65","c65":"Chicken 65","chicken65":"Chicken 65",
        "butter chicken":"Butter Chicken",
        "coffee":None,"kaapi":None,"filter coffee":"Filter Coffee",
        "chai":None,"tea":None,"masala chai":"Masala Chai",
        "cold coffee":"Cold Coffee",
        "puff":None,"veg puff":"Veg Puff","egg puff":"Egg Puff",
        "pongal":"Pongal","upma":"Rava Upma","rava upma":"Rava Upma",
        "meals":None,"full meals":"Full Meals","mini meals":"Mini Meals",
        "curd rice":"Curd Rice","buttermilk":"Buttermilk",
        "combo":None,"idly vada":"Idly Vada Combo","idly vada combo":"Idly Vada Combo",
        "pizza":None,"margherita":"Margherita Pizza",
        "paneer":None,"paneer tikka":"Paneer Tikka",
        "fish curry":"Fish Curry","fish":None,
        "prawn":None,"prawns":None,
    }
    # Resolve None aliases to best menu match
    menu_items={nm.lower():nm for cat,its in r["menu"].items() for nm,d in its.items()}
    for alias,target in UNIVERSAL.items():
        if target is None:
            # Find best match in menu
            for mn_key,mn_nm in menu_items.items():
                if alias in mn_key:
                    aliases.setdefault(alias,mn_nm)
                    break
        else:
            # Only add if target exists in this restaurant's menu
            if target.lower() in menu_items or any(target==nm for cat,its in r["menu"].items() for nm in its):
                aliases.setdefault(alias,target)
    return aliases

def get_qty(token):
    if not token:return None
    t=token.strip().lower()
    if t.isdigit():return int(t)
    return WORD_NUMS.get(t,None)

def voice_parse(text,r):
    """
    Parse natural voice order into [(item_name, price, qty)].
    Works with: digits, word numbers (English/Tamil/Hindi), any order.
    """
    aliases=build_aliases(r)
    cleaned=re.sub(FILLERS,' ',text.lower().strip())
    cleaned=re.sub(r'\s+',' ',cleaned).strip()

    sorted_keys=sorted(aliases.keys(),key=lambda x:-len(x))
    found={};used=[]

    for alias in sorted_keys:
        target=aliases.get(alias)
        if not target:continue
        # Confirm target is in this restaurant menu
        in_menu=any(target==nm for cat,its in r["menu"].items() for nm in its)
        if not in_menu:continue

        pattern=r'\b'+re.escape(alias)+r'\b'
        for m in re.finditer(pattern,cleaned):
            s,e=m.start(),m.end()
            if any(ps<=s<pe or ps<e<=pe for ps,pe in used):continue
            qty=1
            btoks=cleaned[:s].strip().split()
            atoks=cleaned[e:].strip().split()
            qb=get_qty(btoks[-1]) if btoks else None
            qa=get_qty(atoks[0]) if atoks else None
            if qb:qty=qb
            elif qa:qty=qa
            found[target]=found.get(target,0)+qty
            used.append((s,e))

    result=[]
    for nm,qty in found.items():
        price=next((d["price"] for cat,its in r["menu"].items()
                    for n,d in its.items() if n==nm),0)
        result.append((nm,price,max(1,min(qty,20))))
    return result

# ── FOOD SEARCH ───────────────────────────────────────────────────────────
SEARCH_ALIASES={
    "biriyani":"biryani","briyani":"biryani","dosai":"dosa",
    "thosai":"dosa","idli":"idly","vadai":"vada",
    "prawns":"prawn","kaapi":"coffee",
}

def food_search(query,ftype=None,ulat=None,ulng=None,radius=None):
    """
    Search food across all restaurants.
    If location known: sort by distance, apply radius filter.
    If no location: show all matches sorted by rating.
    """
    q=SEARCH_ALIASES.get(query.lower(),query.lower())
    res=[]
    for rid,r in RESTAURANTS.items():
        if r.get("subscription")!="active":continue
        if ftype=="veg" and r["type"] not in["veg","both"]:continue
        if ftype=="nonveg" and r["type"] not in["nonveg","both"]:continue
        dist=hav(ulat,ulng,r["lat"],r["lng"]) if ulat else None
        # Apply radius only when location is known
        if dist is not None and radius and dist>radius:continue
        matched=[f"{item} Rs{d['price']}"
                 for cat,items in r["menu"].items()
                 for item,d in items.items()
                 if q in item.lower() or any(w in item.lower() for w in q.split())]
        if matched:res.append((dist,rid,r,matched[:3]))

    # Sort: by distance if location known, else by rating
    if ulat:
        res.sort(key=lambda x:x[0] if x[0] is not None else 9999)
    else:
        res.sort(key=lambda x:-x[2]["rating"])
    return res

# ── CART ──────────────────────────────────────────────────────────────────
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
    if not o:return None,f"❌ Coupon *{code}* not found.\nType *offers* to see valid codes."
    if sub<o["min"]:return None,f"❌ Min order Rs{o['min']} needed. Your total: Rs{sub}."
    if o["type"]=="percent":
        d=int(sub*o["discount"]/100)
        return d,f"✅ *{code}* applied! {o['discount']}% off = *Rs{d} saved* 🎉"
    if o["type"]=="flat":
        return o["discount"],f"✅ *{code}* applied! *Rs{o['discount']} off* 🎉"
    if o["type"]=="delivery":
        return r["delivery_charge"],f"✅ *{code}* applied! *Free delivery* 🎉"
    return None,"❌ Invalid coupon."

def upsell_hint(r,cart_sub_val):
    """Suggest adding more to unlock an offer."""
    for code,o in r.get("offers",{}).items():
        gap=o["min"]-cart_sub_val
        if 0<gap<=150:
            if o["type"]=="delivery":
                return f"💡 Add Rs{gap} more → *Free delivery!* (use *{code}*)"
            elif o["type"]=="percent":
                return f"💡 Add Rs{gap} more → *{o['discount']}% off!* (use *{code}*)"
    return None

# ── MESSAGE BUILDERS ──────────────────────────────────────────────────────
def msg_welcome(zone=None,last_order=None,cust_name=None):
    g,meal,foods=greet()
    az=f" | 📍 {zone}" if zone else""
    sug=" | ".join([f"_{f}_" for f in foods[:4]])
    n=len([r for r in RESTAURANTS.values() if r.get("subscription")=="active"])

    t=f"👋 *Welcome to FoodieBot Chennai!*{az}\n"
    t+=f"_NexoraAI SuperBot v6_\n\n"

    if cust_name and last_order:
        t+=f"Hey *{cust_name}*! Welcome back 😊\n"
        t+=f"Last order: {last_order}\n"
        t+="Type *reorder* to order the same again!\n\n"
    else:
        t+=f"{g} Time for *{meal}*!\n"
        t+=f"Try: {sug}\n\n"

    t+=f"━━━━━━━━━━━━━━━━━━━━━━\n"
    t+=f"🗣️ *Just type what you want:*\n"
    t+=f"_biryani · idly · chicken · dosa · fish_\n\n"
    t+=f"📍 *Or type your area:*\n"
    t+=f"_Anna Nagar · Perambur · Velachery · Adyar_\n\n"
    t+=f"*Commands:* nearby · veg · top · all\n"
    t+=f"_{n} restaurants ready_ 🍽️"
    return t

def msg_location(zone,nearby,food_hint=None):
    if not nearby:
        return(f"📍 You're near *{zone}*\n\n"
               f"No restaurants within {RADIUS_KM}km right now.\n"
               f"Type *all* to see all Chennai restaurants\n"
               f"Or *area [zone]* to search elsewhere")
    t=f"📍 You're near *{zone}*\n"
    t+=f"_Showing restaurants within {RADIUS_KM}km_\n\n"
    t+="🍽️ *Restaurants near you:*\n"
    t+="━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i,(d,rid,r) in enumerate(nearby,1):
        v="🟢" if r["type"]=="veg" else"🔴"
        t+=f"{i}. {r['emoji']} *{r['name']}* {v}\n"
        t+=f"   📍 *{d:.1f}km away* | ⭐{r['rating']}/5\n"
        t+=f"   🛵 {r['delivery_time']} | Rs{r['delivery_charge']} delivery\n"
        t+=f"   💰 Min Rs{r['min_order']}\n\n"
    t+="━━━━━━━━━━━━━━━━━━━━━━\n"
    for i,(d,rid,r) in enumerate(nearby,1):
        t+=f"Type *{i}* to open {r['name']}\n"
    if food_hint:
        t+=f"\n💬 *What would you like to eat?*\n"
        t+=f"_Just type: biryani · idly · chicken · dosa_"
    else:
        t+=f"\n_Or type a food name to search_ 🔍"
    return t

def msg_food_search(query,results,ulat=None):
    """
    Smart food search results.
    With location: shows distance, sorted nearest.
    Without location: shows all sorted by rating + asks to share location.
    """
    has_loc=ulat is not None
    t=f"🔍 *{query.title()}* — found at {len(results)} restaurant(s)\n"
    if has_loc:
        t+=f"_Sorted by distance from your location_\n"
    else:
        t+=f"_Sorted by rating_\n"
    t+="━━━━━━━━━━━━━━━━━━━━━━\n\n"

    for i,(d,rid,r,matched) in enumerate(results,1):
        v="🟢" if r["type"]=="veg" else"🔴"
        t+=f"{i}. {r['emoji']} *{r['name']}* {v}\n"
        if d is not None:
            t+=f"   📍 *{d:.1f}km* | ⭐{r['rating']}/5\n"
        else:
            t+=f"   📍 {r['area']} | ⭐{r['rating']}/5\n"
        t+=f"   🛵 {r['delivery_time']} | Rs{r['delivery_charge']} delivery\n"
        t+=f"   🍽️ {' · '.join(matched)}\n\n"

    t+="━━━━━━━━━━━━━━━━━━━━━━\n"
    for i,(d,rid,r,_) in enumerate(results,1):
        t+=f"Type *{i}* to order from {r['name']}\n"

    if not has_loc:
        t+=f"\n📍 *Share your location for nearest results!*\n"
        t+=f"_(tap 📎 → Location)_"
    return t

def msg_all(ulat=None,ulng=None,zone=None,radius=RADIUS_KM):
    if ulat:
        nearby=rests_near(ulat,ulng,20,radius)
        zone_note=f" near *{zone}* ({radius}km)" if zone else""
    else:
        nearby=[(None,rid,r) for rid,r in RESTAURANTS.items()
                if r.get("subscription")=="active"]
        nearby.sort(key=lambda x:-x[2]["rating"])
        zone_note=" — all Chennai"

    t=f"🍽️ *FoodieBot Restaurants*{zone_note}\n_{len(nearby)} found_\n"
    t+="━━━━━━━━━━━━━━━━━━━━━━\n\n"
    if not nearby:
        return t+f"No restaurants within {radius}km.\nType *area [zone]* to expand.",[]
    for i,(d,rid,r) in enumerate(nearby,1):
        v="🟢" if r["type"]=="veg" else"🔴"
        ds=f" | *{d:.1f}km*" if d is not None else""
        t+=f"{i}. {r['emoji']} *{r['name']}* {v}\n"
        t+=f"   📍 {r['area']}{ds} | ⭐{r['rating']}/5\n"
        t+=f"   🛵 {r['delivery_time']} | Min Rs{r['min_order']}\n\n"
    t+="━━━━━━━━━━━━━━━━━━━━━━\n"
    for i,(d,rid,r) in enumerate(nearby,1):
        t+=f"Type *{i}* to order from {r['name']}\n"
    if not ulat:
        t+=f"\n📍 *Share location for distance-sorted results*"
    return t,nearby

def msg_menu(r):
    t=f"{r['emoji']} *{r['name']}*\n"
    t+=f"🍽️ {r['cuisine']}\n"
    t+=f"📍 {r['address']}\n"
    t+=f"⭐ {r['rating']}/5 ({r['reviews']} reviews)\n"
    t+=f"🛵 {r['delivery_time']} | Rs{r['delivery_charge']} delivery\n"
    t+=f"💰 Min order: Rs{r['min_order']} | ⏰ {r['timing']}\n"
    t+="━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for cat,items in r["menu"].items():
        t+=f"*{cat}*\n"
        for item,d in items.items():
            tag="🟢" if d.get("veg") else"🔴"
            t+=f"  {tag} {item} — Rs{d['price']}\n"
        t+="\n"
    t+="━━━━━━━━━━━━━━━━━━━━━━\n"
    t+="🗣️ _Just type what you want to order_\n"
    t+="_e.g. idly · vada · chicken biryani_\n\n"
    if r.get("offers"):
        t+="🎁 *Offers:*\n"
        for code,o in r["offers"].items():
            t+=f"  *{code}* — {o['desc']}\n"
    return t

def msg_cart(r,cart,disc=0):
    sub=cart_sub(cart);total=sub+r["delivery_charge"]-disc
    t=f"🛒 *Your Cart — {r['name']}*\n"
    t+="━━━━━━━━━━━━━━━━━━━━━━\n"
    if not cart:t+="_Empty cart. Type food to add!_\n"
    else:
        for i,(item,d) in enumerate(cart.items(),1):
            t+=f"{i}. {item} ×{d['qty']} = Rs{d['price']*d['qty']}\n"
    t+="━━━━━━━━━━━━━━━━━━━━━━\n"
    t+=f"Subtotal:  Rs{sub}\n"
    t+=f"Delivery:  Rs{r['delivery_charge']}\n"
    if disc:t+=f"Discount: -Rs{disc}\n"
    t+=f"*Total:    Rs{total}*\n\n"

    if 0<sub<MIN_ORDER:
        t+=f"⚠️ Min order is Rs{MIN_ORDER}. Add Rs{MIN_ORDER-sub} more.\n\n"
    elif 0<sub<r["min_order"]:
        t+=f"⚠️ {r['name']} needs min Rs{r['min_order']}. Add Rs{r['min_order']-sub} more.\n\n"
    else:
        hint=upsell_hint(r,sub)
        if hint:t+=hint+"\n\n"

    t+="━━━━━━━━━━━━━━━━━━━━━━\n"
    t+="• *checkout* — place order\n"
    t+="• *remove [item]* — e.g. remove vada\n"
    t+="• *update [item] [qty]* — e.g. update idly 3\n"
    t+="• *clear* — empty cart\n"
    t+="• *menu* — back to menu"
    return t

def msg_payment(total,r):
    return(f"💳 *Payment — Rs{total}*\n\n"
           f"Pay to: *{PLATFORM['upi']}*\nAmount: *Rs{total}*\n\n"
           f"📱 *Quick Pay:*\n"
           f"GPay: gpay://upi/pay?pa={PLATFORM['upi']}&am={total}\n"
           f"PhonePe: phonepe://pay?pa={PLATFORM['upi']}&am={total}\n\n"
           f"Reply *paid* — after UPI\nReply *cod* — Cash on Delivery")

def msg_confirm(oid,r,name,total,ptype,partner):
    return(f"━━━━━━━━━━━━━━━━━━━━━━\n✅ *Order Confirmed!*\n━━━━━━━━━━━━━━━━━━━━━━\n"
           f"Order ID: *{oid}*\nRestaurant: *{r['name']}*\n"
           f"Customer: {name}\nAmount: Rs{total}\nPayment: {ptype}\n\n"
           f"🛵 *Your Delivery Partner:*\n"
           f"   {partner['name']} | {partner['phone']} | ⭐{partner['rating']}\n\n"
           f"⏱️ Estimated: {r['delivery_time']}\n📞 Help: {PLATFORM['phone']}\n\n"
           f"Thank you for ordering on FoodieBot! 🍛\n_Type *review* after eating_ 😊")

# ── TWILIO ────────────────────────────────────────────────────────────────
def send_wa(to,body):
    sid=os.environ.get("TWILIO_ACCOUNT_SID","")
    auth=os.environ.get("TWILIO_AUTH_TOKEN","")
    frm=os.environ.get("TWILIO_FROM","whatsapp:+14155238886")
    if not sid or not auth:log.warning(f"[DRY RUN->{to}]\n{body}");return
    to_n=f"whatsapp:{to}" if not to.startswith("whatsapp:") else to
    for chunk in[body[i:i+1500] for i in range(0,len(body),1500)]:
        try:
            r=requests.post(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                auth=(sid,auth),data={"From":frm,"To":to_n,"Body":chunk},timeout=15)
            log.info(f"[SENT]{r.status_code}->{to_n}")
            if r.status_code not in(200,201):log.error(f"[ERR]{r.text[:150]}")
        except Exception as e:log.error(f"[SEND ERR]{e}")

# ── CORE HANDLER ──────────────────────────────────────────────────────────
def handle(sender,body,lat=None,lng=None):
    text=(body or"").strip();lower=text.lower();now=time.time()
    s=user_state.setdefault(sender,{
        "step":"home","cart":{},"restaurant":None,
        "name":None,"address":None,"disc":0,
        "results":[],"lat":None,"lng":None,"zone":None,
        "order_total":0,"last":now,
        "last_order_summary":None,  # for reorder
        "last_restaurant":None,     # for reorder
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
        return"❓ Please pick a number from the list above."

    # ── RESTAURANT FLOW ────────────────────────────────────────────────────
    if s["step"]=="rest" and s.get("restaurant"):
        r=RESTAURANTS[s["restaurant"]]

        if lower in("cart","view cart","my cart","show cart","basket"):
            return msg_cart(r,s["cart"],s["disc"])

        if lower in("clear","clear cart","empty cart","reset","start over"):
            s["cart"]={};s["disc"]=0
            return"🗑️ Cart cleared!\n_Type what you want to eat_ 😊"

        # REMOVE
        m=re.match(r'^(remove|delete|cancel|rm|drop)\s+(.+)$',lower)
        if m:
            matched=fuzzy_cart(m.group(2).strip(),s["cart"])
            if matched:
                del s["cart"][matched]
                sub=cart_sub(s["cart"]);tot=sub+r["delivery_charge"]-s["disc"]
                t=f"✅ *{matched}* removed.\n\n"
                t+=f"🛒 Cart: Rs{tot} ({len(s['cart'])} items)\n"
                if sub>0 and sub<MIN_ORDER:
                    t+=f"⚠️ Add Rs{MIN_ORDER-sub} more for min order.\n"
                t+="Type *cart* to review | *checkout* to order"
                return t
            return f"❌ *{m.group(2)}* not in cart.\nType *cart* to see items."

        # UPDATE QTY
        m=re.match(r'^(update|change|set|qty|make it)\s+(.+?)\s+(\d+)$',lower)
        if m:
            q=m.group(2).strip();nq=int(m.group(3))
            matched=fuzzy_cart(q,s["cart"])
            if not matched:
                mm=fuzzy_menu(q,r)
                if mm:
                    s["cart"][mm[0]]={"price":mm[1],"qty":nq}
                    return f"✅ *{mm[0]}* ×{nq} added.\n\n"+msg_cart(r,s["cart"],s["disc"])
                return f"❌ *{q}* not found. Type *menu* to see items."
            if nq<=0:
                del s["cart"][matched]
                return f"✅ *{matched}* removed.\n\n"+msg_cart(r,s["cart"],s["disc"])
            s["cart"][matched]["qty"]=nq
            return f"✅ *{matched}* updated to ×{nq}.\n\n"+msg_cart(r,s["cart"],s["disc"])

        # CHECKOUT
        if lower in("checkout","place order","confirm order","done","buy"):
            if not s["cart"]:
                return"🛒 Cart is empty!\n_Type what you want to eat_ 😊"
            sub=cart_sub(s["cart"])
            if sub<MIN_ORDER:
                # Suggest cheapest items to reach minimum
                cheap_items=sorted(
                    [(nm,d["price"]) for cat,its in r["menu"].items()
                     for nm,d in its.items()],key=lambda x:x[1])
                gap=MIN_ORDER-sub
                suggestions=[]
                for nm,price in cheap_items:
                    if price<=gap+50 and nm not in s["cart"]:
                        suggestions.append(f"  • {nm} Rs{price}")
                    if len(suggestions)>=3:break
                t=(f"⚠️ *Minimum order is Rs{MIN_ORDER}.*\n"
                   f"Your cart is Rs{sub}. Add Rs{gap} more.\n\n")
                if suggestions:
                    t+=f"💡 *Quick adds:*\n"+"\n".join(suggestions)+"\n\n"
                t+=msg_cart(r,s["cart"],s["disc"])
                return t
            if sub<r["min_order"]:
                return(f"⚠️ *{r['name']} requires min Rs{r['min_order']}.*\n"
                       f"Add Rs{r['min_order']-sub} more.\n\n"
                       +msg_cart(r,s["cart"],s["disc"]))
            s["step"]="get_name"
            return"📦 Almost there!\nWhat's your *name* for the delivery?"

        # COUPON
        if lower.startswith("coupon ") or lower.startswith("apply "):
            code=text.split(" ",1)[1].strip()
            sub=cart_sub(s["cart"])
            disc,msg=coupon_apply(r,code,sub)
            if disc:s["disc"]=disc
            return msg

        if lower in("offers","coupons","discount","promo","deals"):
            off=r.get("offers",{})
            if not off:return"No active offers right now."
            t="🎁 *Active Offers:*\n\n"
            for code,o in off.items():t+=f"  *{code}* — {o['desc']}\n"
            return t+"\nType *coupon CODE* to apply."

        if lower in("menu","back","more","show menu"):return msg_menu(r)

        # VOICE ORDER
        vi=voice_parse(text,r)
        if vi:
            added=[]
            for nm,price,qty in vi:
                if nm in s["cart"]:s["cart"][nm]["qty"]+=qty
                else:s["cart"][nm]={"price":price,"qty":qty}
                added.append(f"*{nm}* ×{qty}")
            sub=cart_sub(s["cart"]);tot=sub+r["delivery_charge"]-s["disc"]
            t=f"✅ *Added to cart:*\n"
            for a in added:t+=f"  {a}\n"
            t+=f"\n🛒 Cart: Rs{tot} ({len(s['cart'])} items)\n"
            if sub<MIN_ORDER:
                t+=f"\n⚠️ Add Rs{MIN_ORDER-sub} more for Rs{MIN_ORDER} min order."
            else:
                hint=upsell_hint(r,sub)
                if hint:t+=f"\n{hint}"
                t+=f"\n\nType *checkout* to order | *cart* to review"
            return t

        # GPT fallback
        if OPENAI_KEY:
            sessions.setdefault(sender,[])
            sessions[sender].append({"role":"user","content":text})
            if len(sessions[sender])>20:sessions[sender]=sessions[sender][-20:]
            mn=", ".join([f"{nm} Rs{d['price']}"
                          for c,it in r["menu"].items() for nm,d in it.items()])
            sys_p=(f"You are a friendly WhatsApp assistant for {r['name']} on FoodieBot Chennai. "
                   f"Menu: {mn}. Be brief, friendly, use emojis. Help customer order.")
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

        return(f"I didn't catch that 😊\n\n"
               f"Just type what you want:\n_idly · vada · biryani · chicken_\n\n"
               f"Or: *menu* to see all items | *cart* to review")

    # ── ORDER STEPS ────────────────────────────────────────────────────────
    if s["step"]=="get_name":
        s["name"]=text;s["step"]="get_address"
        # Prefill address if they've ordered before
        if s.get("address"):
            hint=f"\n_(Previous: {s['address']}\nReply *same* to use it again)_"
        elif uz:
            hint=f"\n_(near {uz} — type full address)_"
        else:
            hint=""
        return f"🏠 Thanks *{text}*!\nWhat's your *delivery address*?{hint}"

    if s["step"]=="get_address":
        if lower=="same" and s.get("address"):
            pass  # keep existing address
        else:
            s["address"]=text
            # Auto-detect zone from address
            if not uz:
                m=zone_from_text(text)
                if m:s["zone"]=m[0];s["lat"]=m[1];s["lng"]=m[2]
        r=RESTAURANTS[s["restaurant"]]
        sub=cart_sub(s["cart"])
        tot=sub+r["delivery_charge"]-s["disc"]
        s["order_total"]=tot;s["step"]="payment"
        return msg_payment(tot,r)

    if s["step"]=="payment":
        if lower in("paid","done","upi done","gpay","phonepe","paytm"):pt="UPI"
        elif lower in("cod","cash","cash on delivery","pay on delivery"):pt="COD"
        else:return"💳 Reply *paid* after UPI payment\nOr reply *cod* for Cash on Delivery"
        r=RESTAURANTS[s["restaurant"]]
        partner=random.choice(r["partners"])
        oid="FB"+str(uuid.uuid4())[:6].upper()
        total=s.get("order_total",0)
        # Build order summary for reorder
        items_summary=", ".join([f"{nm} ×{d['qty']}" for nm,d in s["cart"].items()])
        s["last_order_summary"]=f"{r['name']}: {items_summary}"
        s["last_restaurant"]=s["restaurant"]
        orders[oid]={"restaurant":s["restaurant"],"name":s["name"],
            "address":s["address"],"cart":s["cart"].copy(),
            "total":total,"payment":pt,"partner":partner,
            "time":datetime.datetime.now().isoformat(),"sender":sender}
        comm=int(total*PLATFORM["commission"])
        payouts[s["restaurant"]]=payouts.get(s["restaurant"],0)+(total-comm)
        msg=msg_confirm(oid,r,s["name"],total,pt,partner)
        s.update({"step":"home","cart":{},"restaurant":None,"disc":0,"results":[]})
        return msg

    # ── HOME COMMANDS ──────────────────────────────────────────────────────
    # REORDER
    if lower in("reorder","order again","same order"):
        if s.get("last_restaurant") and s.get("last_order_summary"):
            rid=s["last_restaurant"];r=RESTAURANTS.get(rid)
            if r:
                s["restaurant"]=rid;s["cart"]={};s["disc"]=0;s["step"]="rest"
                return(f"🔄 *Reordering from {r['name']}*\n\n"
                       f"Previous: _{s['last_order_summary']}_\n\n"
                       +msg_menu(r)+"\n\nJust type items to add!")
        return"No previous order found. Type a restaurant name to order!"

    if lower in("hi","hello","hey","start","hii","help"):
        return msg_welcome(uz,s.get("last_order_summary"),s.get("name"))

    if lower in("nearby","near me","closest","restaurants near me"):
        if ul:
            nb=rests_near(ul,ug,8,RADIUS_KM)
            s["results"]=[(d,rid,r) for d,rid,r in nb];s["step"]="home"
            return msg_location(uz or"your area",nb)
        return("📍 *Share your location first!*\n"
               "_(tap 📎 attachment → Location)_\n\n"
               "Or type any Chennai area:\n"
               "_Anna Nagar · Perambur · Velachery · Adyar_")

    # AREA TYPED WITH OR WITHOUT "area" PREFIX
    if lower.startswith("area "):
        aq=text[5:].strip()
        m=zone_from_text(aq)
        if m:
            zn,zl,zg=m;s.update({"zone":zn,"lat":zl,"lng":zg})
            nb=rests_near(zl,zg,8,RADIUS_KM)
            s["results"]=[(d,rid,r) for d,rid,r in nb];s["step"]="area_search"
            return msg_location(zn,nb,food_hint=True)
        return(f"😕 Couldn't find *{aq}* in Chennai.\n"
               "Try: T Nagar · Adyar · Velachery · Anna Nagar · Perambur · OMR")

    # BARE ZONE NAME — customer types "perambur" / "anna nagar" / "vadapalani"
    zone_match=zone_from_text(lower)
    if zone_match and len(lower.split())<=3:  # avoid matching food sentences
        zn,zl,zg=zone_match;s.update({"zone":zn,"lat":zl,"lng":zg})
        nb=rests_near(zl,zg,8,RADIUS_KM)
        s["results"]=[(d,rid,r) for d,rid,r in nb];s["step"]="area_search"
        return msg_location(zn,nb,food_hint=True)

    if lower=="all":
        result=msg_all(ul,ug,uz,radius=RADIUS_KM if ul else None)
        if isinstance(result,tuple):msg,nb=result
        else:msg,nb=result,[]
        s["results"]=[(d,rid,r) for d,rid,r in nb];s["step"]="all_list"
        return msg

    if lower in("veg","vegetarian","veg only","veg food"):
        veg=[(hav(ul,ug,r["lat"],r["lng"]) if ul else None,rid,r)
             for rid,r in RESTAURANTS.items()
             if r.get("subscription")=="active" and r["type"] in("veg","both")]
        if ul:
            veg=[(d,rid,r) for d,rid,r in veg if d<=RADIUS_KM]
            veg.sort(key=lambda x:x[0])
        else:
            veg.sort(key=lambda x:-x[2]["rating"])
        s["results"]=veg;s["step"]="home"
        if not veg:return f"No veg restaurants within {RADIUS_KM}km.\nType *area [zone]* to search elsewhere."
        t=f"🟢 *Veg Restaurants*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i,(d,rid,r) in enumerate(veg,1):
            ds=f" | *{d:.1f}km*" if d else""
            t+=f"{i}. {r['emoji']} *{r['name']}*{ds}\n   📍 {r['area']} | ⭐{r['rating']}/5\n\n"
        t+="━━━━━━━━━━━━━━━━━━━━━━\n"
        for i,(_,rid,r) in enumerate(veg,1):t+=f"Type *{i}* to order from {r['name']}\n"
        if not ul:t+=f"\n📍 Share location for distance-sorted results"
        return t

    if lower in("top","best","top rated"):
        ranked=sorted([(rid,r) for rid,r in RESTAURANTS.items()
                       if r.get("subscription")=="active"],
                      key=lambda x:x[1]["rating"],reverse=True)
        s["results"]=[(0,rid,r) for rid,r in ranked];s["step"]="home"
        t="⭐ *Top Rated Restaurants*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i,(rid,r) in enumerate(ranked,1):
            t+=f"{i}. {r['emoji']} *{r['name']}* — ⭐{r['rating']}/5\n   📍 {r['area']} | {r['cuisine']}\n\n"
        t+="━━━━━━━━━━━━━━━━━━━━━━\n"
        for i,(rid,r) in enumerate(ranked,1):t+=f"Type *{i}* to order from {r['name']}\n"
        return t

    if lower in("cheap","budget","affordable"):
        cheap=sorted([(rid,r) for rid,r in RESTAURANTS.items()
                      if r.get("subscription")=="active"],
                     key=lambda x:x[1]["min_order"])
        s["results"]=[(0,rid,r) for rid,r in cheap];s["step"]="home"
        t="💰 *Budget Restaurants*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i,(rid,r) in enumerate(cheap,1):
            t+=f"{i}. {r['emoji']} *{r['name']}* — Min Rs{r['min_order']}\n   📍 {r['area']}\n\n"
        t+="━━━━━━━━━━━━━━━━━━━━━━\n"
        for i,(rid,r) in enumerate(cheap,1):t+=f"Type *{i}* to order from {r['name']}\n"
        return t

    if lower.startswith("review"):
        return"⭐ Share your review:\nhttps://g.page/foodiebot-chennai\n_Thank you!_ 🙏"

    if lower in("","?","options","what can you do","help me"):
        _,meal,foods=greet()
        sug=" | ".join([f"_{f}_" for f in foods[:4]])
        return(f"🔥 Popular *{meal}* picks:\n{sug}\n\n"
               f"📍 Type your area to find nearby restaurants:\n"
               f"_Anna Nagar · Perambur · Adyar · Velachery_\n\n"
               f"Or type any food name! 🍽️")

    # ── FOOD SEARCH (default) ─────────────────────────────────────────────
    # Search without radius restriction — show all matches
    results=food_search(lower,ulat=ul,ulng=ug,radius=RADIUS_KM if ul else None)
    if results:
        s["results"]=results;s["step"]="search"
        return msg_food_search(lower,results,ul)

    # Last resort zone check
    zone_fallback=zone_from_text(lower)
    if zone_fallback:
        zn,zl,zg=zone_fallback;s.update({"zone":zn,"lat":zl,"lng":zg})
        nb=rests_near(zl,zg,8,RADIUS_KM)
        s["results"]=[(d,rid,r) for d,rid,r in nb];s["step"]="area_search"
        return msg_location(zn,nb,food_hint=True)

    # Nothing found
    _,meal,foods=greet()
    sug=" | ".join([f"_{f}_" for f in foods[:3]])
    return(f"😕 No result for *{lower}*.\n\n"
           f"Popular *{meal}* picks: {sug}\n\n"
           f"📍 Or type your area to find restaurants:\n"
           f"_Anna Nagar · Perambur · Velachery · Adyar_\n\n"
           f"Type *all* to browse all restaurants")

# ── FLASK ROUTES ──────────────────────────────────────────────────────────
@app.route("/")
def index():return"FoodieBot SuperBot v6 is live! 🚀",200

@app.route("/health")
def health():
    return jsonify({"status":"ok","version":"SuperBot v6",
        "restaurants":len(RESTAURANTS),"radius_km":RADIUS_KM,
        "min_order":MIN_ORDER,"twilio_ok":bool(os.environ.get("TWILIO_ACCOUNT_SID"))})

@app.route("/debug/env")
def debug_env():
    sid=os.environ.get("TWILIO_ACCOUNT_SID","")
    auth=os.environ.get("TWILIO_AUTH_TOKEN","")
    frm=os.environ.get("TWILIO_FROM","")
    return jsonify({"TWILIO_ACCOUNT_SID":sid[:8]+"..." if sid else"MISSING",
        "TWILIO_AUTH_TOKEN":auth[:8]+"..." if auth else"MISSING",
        "TWILIO_FROM":frm or"MISSING",
        "status":"ok" if sid and auth else"MISSING CREDENTIALS"})

@app.route("/webhook",methods=["GET","POST"])
def webhook():
    if request.method=="GET":return"FoodieBot webhook live!",200
    sender=request.form.get("From","").replace("whatsapp:","")
    body=request.form.get("Body","").strip()
    lat=request.form.get("Latitude");lng=request.form.get("Longitude")
    log.info(f"[IN] from={sender!r} body={body!r}")
    if not sender:return jsonify({"status":"no sender"}),400
    def bg():
        try:
            rep=handle(sender,body,lat,lng)
            log.info(f"[OUT]{len(rep)}chars")
            send_wa(sender,rep)
        except Exception as e:log.error(f"[ERR]{e}")
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
    return jsonify({"total_orders":len(orders),"total_revenue":rev,
        "commission":int(rev*PLATFORM["commission"]),
        "active_restaurants":len([r for r in RESTAURANTS.values() if r.get("subscription")=="active"]),
        "active_sessions":len(user_state)})

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
            m=(f"🔥 Craving *{meal}*? Try: {sug}\n\n"
               f"Reply to order on FoodieBot Chennai! 🍽️")
            threading.Thread(target=send_wa,args=(sender,m),daemon=True).start()
            count+=1
    return jsonify({"broadcast_sent":count,"meal":meal})

if __name__=="__main__":
    app.run(debug=True,port=10000)
