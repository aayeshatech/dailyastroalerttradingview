import streamlit as st
import datetime
import threading
import requests
from skyfield.api import load

# === TELEGRAM CONFIG ===
BOT_TOKEN = '7613703350:AAE-W4dJ37lngM4lO2Tnuns8-a-80jYRtxk'
CHAT_ID = '-1002840229810'

# === Vedic Sign Strengths ===
sign_strength = {
    "Leo": 2, "Cancer": 1, "Virgo": 2, "Taurus": 2, "Pisces": -1, "Capricorn": -2,
    "Scorpio": 0, "Gemini": 1, "Aries": 2, "Libra": 0, "Sagittarius": 1, "Aquarius": -1
}

# === Planet influence mapping ===
planet_influence = {
    "banking": {"positive": ["Jupiter", "Venus"], "negative": ["Saturn", "Mars"]},
    "metals": {"positive": ["Venus", "Sun"], "negative": ["Saturn", "Mars"]},
    "energy": {"positive": ["Sun", "Mars"], "negative": ["Saturn", "Neptune"]},
    "tech": {"positive": ["Mercury", "Uranus"], "negative": ["Saturn", "Neptune"]},
    "crypto": {"positive": ["Uranus", "Mercury"], "negative": ["Saturn", "Neptune"]},
    "indices": {"positive": ["Jupiter", "Sun"], "negative": ["Saturn", "Neptune"]},
    "other": {"positive": ["Jupiter"], "negative": ["Saturn"]}
}

# === Symbol to sector mapping ===
symbol_sector_map = {
    "NSE:HDFCBANK": "banking",
    "NSE:TATASTEEL": "metals",
    "MCX:GOLD1!": "metals",
    "MCX:SILVER1!": "metals",
    "MCX:CRUDEOIL1!": "energy",
    "CFI:US100": "tech",
    "CAPITALCOM:US500": "indices",
    "FX:US30": "indices",
    "BITSTAMP:BTCUSD": "crypto",
    "COINBASE:ETHUSD": "crypto"
}

# === Load Skyfield ephemeris ===
planets = load('de421.bsp')
earth = planets['earth']
ts = load.timescale()

# Map planet names to Skyfield bodies
skyfield_planet_map = {
    "Sun": planets['sun'],
    "Moon": planets['moon'],
    "Mercury": planets['mercury'],
    "Venus": planets['venus'],
    "Mars": planets['mars'],
    "Jupiter": planets['jupiter barycenter'],
    "Saturn": planets['saturn barycenter'],
    "Uranus": planets['uranus barycenter'],
    "Neptune": planets['neptune barycenter'],
    "Pluto": planets['pluto barycenter']
}

# Zodiac signs in order
zodiac_signs = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def get_sign(longitude):
    index = int(longitude / 30) % 12
    return zodiac_signs[index]

def get_planetary_positions(date_obj):
    t = ts.utc(date_obj.year, date_obj.month, date_obj.day, date_obj.hour, date_obj.minute)
    positions = {}
    for name, planet in skyfield_planet_map.items():
        astrometric = earth.at(t).observe(planet).apparent()
        lon, lat, dist = astrometric.ecliptic_latlon()
        positions[name] = get_sign(lon.degrees)
    return positions

def get_sentiment(sector, planetary_positions):
    pos_score = sum(sign_strength.get(planetary_positions[p], 0) for p in planet_influence[sector]["positive"])
    neg_score = sum(sign_strength.get(planetary_positions[p], 0) for p in planet_influence[sector]["negative"])
    return "Bullish" if pos_score > abs(neg_score) else "Bearish"

def get_market_times(symbol):
    return ("09:15", "15:30") if symbol.startswith("NSE:") else ("05:00", "21:00")

def generate_signals(selected_datetime):
    planetary_positions = get_planetary_positions(selected_datetime)
    astro_date = selected_datetime.strftime("%d-%b-%Y")
    now_str = selected_datetime.strftime("%d-%b-%Y %H:%M")
    lines = [f"📅 Astro-Trading Signals — {astro_date} (Generated {now_str})"]

    for symbol, sector in symbol_sector_map.items():
        sentiment = get_sentiment(sector, planetary_positions)
        entry, exit_ = get_market_times(symbol)
        emoji = "🟢" if sentiment == "Bullish" else "🔴"
        lines.append(f"{emoji} {symbol} → {sentiment} | Entry: {entry} | Exit: {exit_}")
    return "\n".join(lines)

def send_to_telegram(message):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                  data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})

# --- Streamlit UI ---
st.title("🔮 Morning Astro Trading Signals (Skyfield Version)")

default_datetime = datetime.datetime.combine(datetime.date.today(), datetime.time(9, 15))
date = st.date_input("Date", default_datetime.date())
time = st.time_input("Time", default_datetime.time())

if st.button("Generate Morning Signals"):
    dt = datetime.datetime.combine(date, time)
    signals_text = generate_signals(dt)
    st.text_area("Today's Signals", signals_text, height=500)
    st.success("✅ Morning signals generated")
    threading.Thread(target=send_to_telegram, args=(signals_text,), daemon=True).start()
    st.caption("📩 Telegram sending in background...")
