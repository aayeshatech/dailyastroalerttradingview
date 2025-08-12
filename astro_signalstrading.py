import streamlit as st
import datetime
import requests
import threading
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const

BOT_TOKEN = '7613703350:AAE-W4dJ37lngM4lO2Tnuns8-a-80jYRtxk'
CHAT_ID = '-1002840229810'

sign_strength = {
    "Leo": 2, "Cancer": 1, "Virgo": 2, "Taurus": 2, "Pisces": -1, "Capricorn": -2,
    "Scorpio": 0, "Gemini": 1, "Aries": 2, "Libra": 0, "Sagittarius": 1, "Aquarius": -1
}

planet_influence = {
    "banking": {"positive": ["Jupiter", "Venus"], "negative": ["Saturn", "Mars"]},
    "metals": {"positive": ["Venus", "Sun"], "negative": ["Saturn", "Mars"]},
    "energy": {"positive": ["Sun", "Mars"], "negative": ["Saturn", "Neptune"]},
    "tech": {"positive": ["Mercury", "Uranus"], "negative": ["Saturn", "Neptune"]},
    "crypto": {"positive": ["Uranus", "Mercury"], "negative": ["Saturn", "Neptune"]},
    "indices": {"positive": ["Jupiter", "Sun"], "negative": ["Saturn", "Neptune"]},
    "other": {"positive": ["Jupiter"], "negative": ["Saturn"]}
}

symbol_sector_map = {
    "AMEX:DIA": "indices", "AMEX:FXE": "indices", "AMEX:GLD": "metals", "AMEX:SPY": "indices",
    "BINANCE:LTCUSD": "crypto", "BIST:XAGUSD1!": "metals", "BITSTAMP:BTCUSD": "crypto",
    "BITSTAMP:ETHUSD": "crypto", "BSE:DECNGOLD": "metals", "BSE:ARFIN": "banking",
    "BSE:M_MFIN": "banking", "BSE:SGFIN": "banking", "BSE:TITANSEC": "tech", "BSE:VERITAS": "tech",
    "CFI:US100": "tech", "CAPITALCOM:US500": "indices", "FX:US30": "indices", "MCX:GOLD1!": "metals",
    "MCX:SILVER1!": "metals", "MCX:CRUDEOIL1!": "energy", "NSE:HDFCBANK": "banking",
    "NSE:ICICIBANK": "banking", "NSE:TATASTEEL": "metals", "NSE:RELIANCE": "energy",
    "COINBASE:ETHUSD": "crypto"
}

def get_planetary_positions(date_obj):
    pos = GeoPos("51.48", "0.0")  
    dt = Datetime(date_obj.strftime("%Y/%m/%d"), date_obj.strftime("%H:%M"), "+00:00")
    chart = Chart(dt, pos)
    planet_map = {
        "Sun": const.SUN, "Moon": const.MOON, "Mercury": const.MERCURY, "Venus": const.VENUS,
        "Mars": const.MARS, "Jupiter": const.JUPITER, "Saturn": const.SATURN,
        "Uranus": const.URANUS, "Neptune": const.NEPTUNE, "Pluto": const.PLUTO
    }
    return {name: chart.get(code).sign for name, code in planet_map.items()}

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
st.title("🔮 Astro Trading Signal Generator")

date = st.date_input("Select Date", datetime.date.today())
time = st.time_input("Select Time", datetime.datetime.now().time())

if st.button("Generate Signals"):
    dt = datetime.datetime.combine(date, time)
    signals_text = generate_signals(dt)
    st.text_area("Generated Signals", signals_text, height=500)
    st.success("✅ Signals generated instantly")
    threading.Thread(target=send_to_telegram, args=(signals_text,), daemon=True).start()
    st.caption("📩 Sending to Telegram in background...")
