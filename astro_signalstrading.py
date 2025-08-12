import streamlit as st
import pandas as pd
import json
import datetime
import requests

# === TELEGRAM SETTINGS ===
BOT_TOKEN = "7613703350:AAE-W4dJ37lngM4lO2Tnuns8-a-80jYRtxk"
CHAT_ID = "-1002840229810"

# === MARKET TIMINGS ===
NSE_START = datetime.time(9, 15)
NSE_END = datetime.time(15, 30)
GLOBAL_START = datetime.time(5, 0)
GLOBAL_END = datetime.time(21, 0)

# === LOAD CONFIG ===
with open("config.json", "r") as f:
    config = json.load(f)

# === LOAD WATCHLIST ===
watchlist_df = pd.read_csv("watchlist.txt", names=["Symbol", "Sector"], sep=",", engine="python")

# === HELPER FUNCTIONS ===
def is_friendly(planet, nakshatra):
    return nakshatra in config["friendly_nakshatras"].get(planet, [])

def is_enemy(planet, nakshatra):
    return nakshatra in config["enemy_nakshatras"].get(planet, [])

def get_market_times(symbol):
    if symbol.startswith("NSE:"):
        return NSE_START, NSE_END
    else:
        return GLOBAL_START, GLOBAL_END

# === STREAMLIT UI ===
st.title("📅 Astro-Trading Signals Generator")
uploaded_file = st.file_uploader("Upload planetary transit file", type=["txt", "csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file, sep="\t|,", engine="python")
    st.write("### Uploaded Planetary Data", df)

    signals_list = []

    for _, sym_row in watchlist_df.iterrows():
        symbol = sym_row["Symbol"]
        sector = sym_row["Sector"]

        # Find planets linked to this sector
        planets = config["sector_planets"].get(sector, [])

        start_time, end_time = get_market_times(symbol)

        # Filter transits for relevant planets & within market hours
        planet_transits = df[df["Planet"].isin(planets)].copy()
        planet_transits["TimeObj"] = pd.to_datetime(planet_transits["Time"], format="%H:%M:%S").dt.time
        planet_transits = planet_transits[
            planet_transits["TimeObj"].between(start_time, end_time)
        ].sort_values("TimeObj")

        if planet_transits.empty:
            continue

        # Track sentiment changes
        current_sentiment = None
        entry_time = None

        for _, t_row in planet_transits.iterrows():
            sentiment = None
            if is_friendly(t_row["Planet"], t_row["Nakshatra"]):
                sentiment = "Bullish"
            elif is_enemy(t_row["Planet"], t_row["Nakshatra"]):
                sentiment = "Bearish"

            if sentiment != current_sentiment:
                if current_sentiment is not None:
                    signals_list.append({
                        "Symbol": symbol,
                        "Sentiment": current_sentiment,
                        "Entry": entry_time.strftime("%H:%M"),
                        "Exit": t_row["TimeObj"].strftime("%H:%M")
                    })
                current_sentiment = sentiment
                entry_time = datetime.datetime.combine(datetime.date.today(), t_row["TimeObj"])

        # Close last period at market end
        if current_sentiment is not None:
            signals_list.append({
                "Symbol": symbol,
                "Sentiment": current_sentiment,
                "Entry": entry_time.strftime("%H:%M"),
                "Exit": end_time.strftime("%H:%M")
            })

    signals_df = pd.DataFrame(signals_list)
    signals_df = signals_df.dropna().reset_index(drop=True)

    st.write("### Today's Bullish & Bearish Windows", signals_df)

    # === Format for Telegram ===
    today_str = datetime.date.today().strftime("%d-%b-%Y")
    now_str = datetime.datetime.now().strftime("%d-%b-%Y %H:%M")

    message = f"📅 Astro-Trading Signals — {today_str} (Generated {now_str})\n"
    for _, row in signals_df.iterrows():
        emoji = "🟢" if row["Sentiment"] == "Bullish" else "🔴"
        message += f"{emoji} {row['Symbol']} → {row['Sentiment']} | Entry: {row['Entry']} | Exit: {row['Exit']}\n"

    # === Telegram send button ===
    if st.button("📤 Send to Telegram"):
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message}
        r = requests.post(url, data=payload)
        if r.status_code == 200:
            st.success("✅ Sent to Telegram")
        else:
            st.error(f"❌ Failed to send: {r.text}")
