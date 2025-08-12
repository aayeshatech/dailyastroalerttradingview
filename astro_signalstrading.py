import streamlit as st
import datetime
import requests
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const

# === TELEGRAM BOT CONFIGURATION ===
BOT_TOKEN = '7613703350:AAE-W4dJ37lngM4lO2Tnuns8-a-80jYRtxk'
CHAT_ID = '-1002840229810'

# === PLANET SIGN STRENGTHS (Vedic style) ===
sign_strength = {
    "Leo": 2, "Cancer": 1, "Virgo": 2, "Taurus": 2, "Pisces": -1, "Capricorn": -2,
    "Scorpio": 0, "Gemini": 1, "Aries": 2, "Libra": 0, "Sagittarius": 1, "Aquarius": -1
}

# === Sector → Planets mapping ===
planet_influence = {
    "banking": {"positive": ["Jupiter", "Venus"], "negative": ["Saturn", "Mars"]},
    "metals": {"positive": ["Venus", "Sun"], "negative": ["Saturn", "Mars"]},
    "energy": {"positive": ["Sun", "Mars"], "negative": ["Saturn", "Neptune"]},
    "tech": {"positive": ["Mercury", "Uranus"], "negative": ["Saturn", "Neptune"]},
    "crypto": {"positive": ["Uranus", "Mercury"], "negative": ["Saturn", "Neptune"]},
    "indices": {"positive": ["Jupiter", "Sun"], "negative": ["Saturn", "Neptune"]},
    "other": {"positive": ["Jupiter"], "negative": ["Saturn"]}
}

# === FULL Symbol → Sector mapping (from your watchlists) ===
symbol_sector_map = {
    "AMEX:DIA": "indices",
    "AMEX:FXE": "indices",
    "AMEX:GLD": "metals",
    "AMEX:SPY": "indices",
    "BINANCE:LTCUSD": "crypto",
    "BIST:XAGUSD1!": "metals",
    "BITSTAMP:BTCUSD": "crypto",
    "BITSTAMP:ETHUSD": "crypto",
    "BSE:DECNGOLD": "metals",
    "BSE:ARFIN": "banking",
    "BSE:M_MFIN": "banking",
    "BSE:SGFIN": "banking",
    "BSE:TITANSEC": "tech",
    "BSE:VERITAS": "tech",
    "CFI:US100": "tech",
    "CAPITALCOM:US500": "indices",
    "FX:US30": "indices",
    "MCX:GOLD1!": "metals",
    "MCX:SILVER1!": "metals",
    "MCX:CRUDEOIL1!": "energy",
    "NSE:HDFCBANK": "banking",
    "NSE:ICICIBANK": "banking",
    "NSE:TATASTEEL": "metals",
    "NSE:RELIANCE": "energy",
    "COINBASE:ETHUSD": "crypto"
}

# === Flatlib Planetary Position Calculation ===
def get_planetary_positions(date_obj):
    date_str = date_obj.strftime("%Y/%m/%d")
    time_str = date_obj.strftime("%H:%M")
    pos = GeoPos("51.48", "0.0")  # Greenwich
    dt = Datetime(date_str, time_str, "+00:00")
    chart = Chart(dt, pos)

    planet_map = {
        "Sun": const.SUN,
        "Moon": const.MOON,
        "Mercury": const.MERCURY,
        "Venus": const.VENUS,
        "Mars": const.MARS,
        "Jupiter": const.JUPITER,
        "Saturn": const.SATURN,
        "Uranus": const.URANUS,
        "Neptune": const.NEPTUNE,
        "Pluto": const.PLUTO
    }

    positions = {}
    for name, pl_code in planet_map.items():
        pl = chart.get(pl_code)
        positions[name] = pl.sign
    return positions

# === Sentiment calculation ===
def get_sentiment(sector, planetary_positions):
    positive_planets = planet_influence[sector]["positive"]
    negative_planets = planet_influence[sector]["negative"]
    pos_score = sum(sign_strength.get(planetary_positions[p], 0) for p in positive_planets)
    neg_score = sum(sign_strength.get(planetary_positions[p], 0) for p in negative_planets)
    return "Bullish" if pos_score > abs(neg_score) else "Bearish"

# === Market session times ===
def get_market_times(symbol):
    if symbol.startswith("NSE:"):
        return "09:15", "15:30"
    else:
        return "05:00", "21:00"

# === Generate & Send Signals ===
def generate_signals(selected_datetime):
    astro_date = selected_datetime.strftime("%d-%b-%Y")
    planetary_positions = get_planetary_positions(selected_datetime)

    astro_signals = []
    for symbol, sector in symbol_sector_map.items():
        sentiment = get_sentiment(sector, planetary_positions)
        entry, exit_ = get_market_times(symbol)
        astro_signals.append((symbol, sentiment, entry, exit_))

    # Format message
    now_str = selected_datetime.strftime("%d-%b-%Y %H:%M")
    message_lines = [f"📅 Astro-Trading Signals — {astro_date} (Generated {now_str})"]
    for symbol, sentiment, entry, exit_ in astro_signals:
        emoji = "🟢" if sentiment == "Bullish" else "🔴"
        message_lines.append(f"{emoji} {symbol} → {sentiment} | Entry: {entry} | Exit: {exit_}")
    message_text = "\n".join(message_lines)

    # Send to Telegram
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message_text, "parse_mode": "HTML"}
    requests.post(url, data=payload)

    return message_text

# === Streamlit UI ===
st.title("🔮 Astro Trading Signal Generator")

default_time = datetime.datetime.now()
selected_date = st.date_input("Select Date", default_time.date())
selected_time = st.time_input("Select Time", default_time.time())

if st.button("Generate Signals"):
    dt = datetime.datetime.combine(selected_date, selected_time)
    st.info("Calculating planetary positions and generating signals...")
    signals = generate_signals(dt)
    st.text_area("Generated Signals", signals, height=500)
    st.success("✅ Signals generated and sent to Telegram!")
