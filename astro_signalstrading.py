import streamlit as st
from skyfield.api import load
from datetime import datetime
import pytz
import requests

# ==========================
# TELEGRAM CONFIG
# ==========================
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

# ==========================
# LOAD SYMBOLS FROM FILE
# ==========================
with open("watchlist.txt", "r") as f:
    all_symbols = sorted(set(line.strip() for line in f if line.strip()))

# ==========================
# AUTO-SECTOR CLASSIFICATION
# ==========================
def classify_sector(symbol):
    s = symbol.upper()
    if any(x in s for x in ["BANK", "HDFC", "ICICI", "SBI", "AXIS", "KOTAK"]):
        return "banking"
    elif any(x in s for x in ["GOLD", "SILVER", "METAL", "STEEL", "CEM"]):
        return "metals"
    elif any(x in s for x in ["CRUDE", "OIL", "GAS", "ONGC", "POWER", "ENERGY"]):
        return "energy"
    elif any(x in s for x in ["TECH", "INFY", "TCS", "WIPRO", "HCL", "US100", "NASDAQ"]):
        return "tech"
    elif any(x in s for x in ["BTC", "ETH", "DOGE", "SHIB", "CRYPTO"]):
        return "crypto"
    elif any(x in s for x in ["US500", "US30", "S&P", "DOW", "NIFTY", "SENSEX"]):
        return "indices"
    else:
        return "other"

symbol_sector_map = {sym: classify_sector(sym) for sym in all_symbols}

# ==========================
# ASTRO CALCULATION
# ==========================
def get_planet_positions(dt):
    eph = load('de421.bsp')
    planets = {
        "Sun": eph['sun'],
        "Moon": eph['moon'],
        "Mercury": eph['mercury'],
        "Venus": eph['venus'],
        "Mars": eph['mars'],
        "Jupiter": eph['jupiter barycenter'],
        "Saturn": eph['saturn barycenter'],
        "Uranus": eph['uranus barycenter'],
        "Neptune": eph['neptune barycenter'],
        "Pluto": eph['pluto barycenter']
    }
    ts = load.timescale()
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute)
    positions = {}
    for name, planet in planets.items():
        astrometric = eph['earth'].at(t).observe(planet)
        lon, lat, distance = astrometric.ecliptic_latlon()
        positions[name] = lon.degrees
    return positions

def score_sector(sector, positions):
    score = 0
    if sector == "banking":
        score += 1 if positions["Jupiter"] > 180 else -1
    elif sector == "metals":
        score += 1 if positions["Venus"] > 180 else -1
    elif sector == "energy":
        score += 1 if positions["Mars"] > 180 else -1
    elif sector == "tech":
        score += 1 if positions["Mercury"] > 180 else -1
    elif sector == "crypto":
        score += 1 if positions["Uranus"] > 180 else -1
    elif sector == "indices":
        score += 1 if positions["Sun"] > 180 else -1
    else:
        score += 1 if positions["Moon"] > 180 else -1
    return "Bullish" if score > 0 else "Bearish"

# ==========================
# MAIN APP
# ==========================
st.title("📅 Astro-Trading Signals")

now = datetime.now(pytz.timezone("Asia/Kolkata"))
positions = get_planet_positions(now)

results = []
for symbol, sector in symbol_sector_map.items():
    sentiment = score_sector(sector, positions)
    if symbol.startswith(("NSE", "BSE")):
        entry, exit = "09:15", "15:30"
    else:
        entry, exit = "05:00", "21:00"
    results.append((symbol, sentiment, entry, exit))

# Display results
st.write(f"📅 Astro-Trading Signals — {now.strftime('%d-%b-%Y')} (Generated {now.strftime('%H:%M')})")
for sym, sentiment, entry, exit in results:
    icon = "🟢" if sentiment == "Bullish" else "🔴"
    st.write(f"{icon} {sym} → {sentiment} | Entry: {entry} | Exit: {exit}")

# Send to Telegram
if st.button("Send to Telegram"):
    message = f"📅 Astro-Trading Signals — {now.strftime('%d-%b-%Y')} (Generated {now.strftime('%H:%M')})\n"
    for sym, sentiment, entry, exit in results:
        icon = "🟢" if sentiment == "Bullish" else "🔴"
        message += f"{icon} {sym} → {sentiment} | Entry: {entry} | Exit: {exit}\n"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    r = requests.post(url, data=payload)
    if r.status_code == 200:
        st.success("Sent to Telegram!")
    else:
        st.error(f"Failed to send: {r.text}")
