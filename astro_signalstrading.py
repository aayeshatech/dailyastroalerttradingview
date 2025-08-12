import streamlit as st
import pandas as pd
import json
import datetime
import requests

# === USER TELEGRAM CONFIG ===
BOT_TOKEN = "7613703350:AAE-W4dJ37lngM4lO2Tnuns8-a-80jYRtxk"
CHAT_ID = "-1002840229810"

# === LOAD CONFIG ===
with open("config.json", "r") as f:
    config = json.load(f)

# === LOAD WATCHLIST ===
with open("watchlist.txt", "r") as f:
    watchlist = [line.strip() for line in f if line.strip()]

# === MARKET TIMINGS ===
NSE_START = datetime.time(9, 15)
NSE_END = datetime.time(15, 30)
GLOBAL_START = datetime.time(5, 0)
GLOBAL_END = datetime.time(21, 0)

# === STREAMLIT UI ===
st.title("📅 Astro-Trading Signal Generator")
uploaded_file = st.file_uploader("Upload planetary transit file (TXT/CSV)", type=["txt", "csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file, sep="\t|,", engine="python")
    st.write("### Uploaded Planetary Data", df)

    def is_friendly(planet, nakshatra):
        return nakshatra in config["friendly_nakshatras"].get(planet, [])

    def is_enemy(planet, nakshatra):
        return nakshatra in config["enemy_nakshatras"].get(planet, [])

    # === Function to determine sentiment ===
    def get_sentiment(planet, nakshatra):
        if is_friendly(planet, nakshatra):
            return "Bullish"
        elif is_enemy(planet, nakshatra):
            return "Bearish"
        else:
            return None

    # === Generate Signals ===
    signals = []
    for _, row in df.iterrows():
        planet = row["Planet"]
        nakshatra = row["Nakshatra"]
        time_str = row["Time"]
        time_obj = datetime.datetime.strptime(time_str, "%H:%M:%S").time()

        sentiment = get_sentiment(planet, nakshatra)
        if sentiment:
            for symbol in watchlist:
                # Example sector mapping: match symbol to sector manually
                # For now, assume all are GLOBAL for demonstration
                if "NSE:" in symbol:
                    start_time, end_time = NSE_START, NSE_END
                else:
                    start_time, end_time = GLOBAL_START, GLOBAL_END

                if start_time <= time_obj <= end_time:
                    signals.append({
                        "Symbol": symbol,
                        "Sentiment": sentiment,
                        "Entry": time_obj.strftime("%H:%M"),
                        "Exit": end_time.strftime("%H:%M")
                    })

    signals_df = pd.DataFrame(signals)
    st.write("### Generated Signals", signals_df)

    # === Format for Telegram ===
    today_str = datetime.date.today().strftime("%d-%b-%Y")
    now_str = datetime.datetime.now().strftime("%d-%b-%Y %H:%M")

    message = f"📅 Astro-Trading Signals — {today_str} (Generated {now_str})\n"
    for _, row in signals_df.iterrows():
        emoji = "🟢" if row["Sentiment"] == "Bullish" else "🔴"
        message += f"{emoji} {row['Symbol']} → {row['Sentiment']} | Entry: {row['Entry']} | Exit: {row['Exit']}\n"

    # === Send to Telegram ===
    if st.button("📤 Send to Telegram"):
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message}
        r = requests.post(url, data=payload)
        if r.status_code == 200:
            st.success("✅ Sent to Telegram")
        else:
            st.error(f"❌ Failed to send: {r.text}")
