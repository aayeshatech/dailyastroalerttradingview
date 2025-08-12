import requests
import datetime
import swisseph as swe
import schedule
import time
import csv
from pathlib import Path
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

# === Swiss Ephemeris Planetary Position Calculation ===
def get_planetary_positions(date_obj):
    date_str = date_obj.strftime("%Y/%m/%d")
    time_str = date_obj.strftime("%H:%M")
    # Geo position can be any fixed point, e.g., Greenwich
    pos = GeoPos("51.48", "0.0")
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

    positions = {}
    for name, pl_code in planet_map.items():
        lon, lat, dist = swe.calc_ut(jd, pl_code)
        sign_index = int(lon // 30)
        positions[name] = signs[sign_index]

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

# === Main signal generation function ===
def run_signals():
    now = datetime.datetime.now()
    astro_date = now.strftime("%d-%b-%Y")
    planetary_positions = get_planetary_positions(now)

    astro_signals = []
    for symbol, sector in symbol_sector_map.items():
        sentiment = get_sentiment(sector, planetary_positions)
        entry, exit_ = get_market_times(symbol)
        astro_signals.append((symbol, sentiment, entry, exit_))

    # === Save to CSV log ===
    log_file = Path("astro_signals_log.csv")
    log_exists = log_file.exists()
    with open(log_file, mode="a", newline="") as file:
        writer = csv.writer(file)
        if not log_exists:
            writer.writerow(["Date", "GeneratedTime", "Symbol", "Sentiment", "Entry", "Exit"])
        for symbol, sentiment, entry, exit_ in astro_signals:
            writer.writerow([astro_date, now.strftime("%H:%M"), symbol, sentiment, entry, exit_])

    # === Format message ===
    now_str = now.strftime("%d-%b-%Y %H:%M")
    message_lines = [f"📅 Astro-Trading Signals — {astro_date} (Generated {now_str})"]
    for symbol, sentiment, entry, exit_ in astro_signals:
        emoji = "🟢" if sentiment == "Bullish" else "🔴"
        message_lines.append(f"{emoji} {symbol} → {sentiment} | Entry: {entry} | Exit: {exit_}")
    message_text = "\n".join(message_lines)

    # === Send to Telegram ===
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message_text,
        "parse_mode": "HTML"
    }
    response = requests.post(url, data=payload)

    if response.status_code == 200:
        print(f"✅ Signals sent to Telegram successfully at {now_str}")
    else:
        print(f"❌ Failed to send: {response.text}")

# === Schedule jobs ===
schedule.every().day.at("08:00").do(run_signals)   # Morning run
schedule.every().day.at("23:30").do(run_signals)   # Night run

print("⏳ Waiting for scheduled runs at 08:00 and 23:30...")
while True:
    schedule.run_pending()
    time.sleep(30)
