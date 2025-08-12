import streamlit as st
from skyfield.api import load
from datetime import datetime, time
import pytz
import requests

# ==========================
# TELEGRAM CONFIG
# ==========================
BOT_TOKEN = "7613703350:AAE-W4dJ37lngM4lO2Tnuns8-a-80jYRtxk"
CHAT_ID = "-1002840229810"

# ==========================
# MERGED SYMBOL SECTOR MAP
# (From your 3 watchlists)
# ==========================
symbol_sector_map = {
    # Auto-generated from merged watchlists
    "NSE:HDFCBANK": "banking",
    "NSE:TATASTEEL": "metals",
    "MCX:GOLD1!": "metals",
    "MCX:SILVER1!": "metals",
    "MCX:CRUDEOIL1!": "energy",
    "CFI:US100": "tech",
    "CAPITALCOM:US500": "indices",
    "FX:US30": "indices",
    "BITSTAMP:BTCUSD": "crypto",
    "COINBASE:ETHUSD": "crypto",
    # ... Add rest of merged symbols here from extracted list
}

# Auto-classification fallback
def classify_sector(symbol):
    s = symbol.upper()
    if "BANK" in s or "HDFC" in s or "ICICI" in s or "SBI" in s:
        return "banking"
    elif "GOLD" in s or "SILVER" in s or "METAL" in s or "STEEL" in s:
        return "metals"
    elif "CRUDE" in s or "OIL" in s or "GAS" in s or "ENERGY" in s:
        return "energy"
    elif "TECH" in s or "INFY" in s or "TCS" in s or "WIPRO" in s or "US100" in s or "NASDAQ" in s:
        return "tech"
    elif "BTC" in s or "ETH" in s or "DOGE" in s or "SHIB" in s or "CRYPTO" in s:
        return "crypto"
    elif "US500" in s or "US30" in s or "S&P" in s or "DOW" in s or "NIFTY" in s or "SENSEX" in s:
        return "indices"
    else:
        return "other"

# Ensure all symbols in map
for sym in list(symbol_sector_map.keys()):
    if not symbol_sector_map[sym]:
        symbol_sector_map[sym] = classify_sector(sym)

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

# Simple scoring logic per sector
def score_sector(sector, positions):
    score = 0
    if sector == "banking":
        if positions["Jupiter"] > 180: score += 1
        else: score -= 1
    elif sector == "metals":
        if positions["Venus"] > 180: score += 1
        else: score -= 1
    elif sector == "energy":
        if positions["Mars"] > 180: score += 1
        else: score -= 1
    elif sector == "tech":
        if positions["Mercury"] > 180: score += 1
        else: score -= 1
    elif sector == "crypto":
        if positions["Uranus"] > 180: score += 1
        else: score -= 1
    elif sector == "indices":
        if positions["Sun"] > 180: score += 1
        else: score -= 1
    else:
        if positions["Moon"] > 180: score += 1
        else: score -= 1
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
    if symbol.startswith("NSE") or symbol.startswith("BSE"):
        entry, exit = "09:15", "15:30"
    else:
        entry, exit = "05:00", "21:00"
    results.append((symbol, sentiment, entry, exit))

# Display
st.write(f"📅 Astro-Trading Signals — {now.strftime('%d-%b-%Y')} (Generated {now.strftime('%H:%M')})")
for sym, sentiment, entry, exit in results:
    icon = "🟢" if sentiment == "Bullish" else "🔴"
    st.write(f"{icon} {sym} → {sentiment} | Entry: {entry} | Exit: {exit}")

# ==========================
# TELEGRAM SEND
# ==========================
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
