import streamlit as st
import pandas as pd
import json
from datetime import datetime
import requests

# === TELEGRAM SETTINGS ===
BOT_TOKEN = "7613703350:AAE-W4dJ37lngM4lO2Tnuns8-a-80jYRtxk"
CHAT_ID = "-1002840229810"

# === Load Config ===
try:
    with open("config.json") as f:
        config = json.load(f)
    st.success("✅ Config loaded successfully")
except Exception as e:
    st.error(f"❌ Error loading config.json: {e}")
    st.stop()

def normalize_name(name):
    """Normalize nakshatra names for matching."""
    return name.strip().lower().replace(" ", "").replace("-", "")

def is_friendly(planet, nakshatra):
    """Check if nakshatra is friendly for the planet."""
    if planet not in config.get("friendly_nakshatras", {}):
        return False
    
    nak_norm = normalize_name(nakshatra)
    friendly_list = config["friendly_nakshatras"][planet]
    
    for friendly_nak in friendly_list:
        if nak_norm == normalize_name(friendly_nak):
            return True
    return False

def is_enemy(planet, nakshatra):
    """Check if nakshatra is enemy for the planet."""
    if planet not in config.get("enemy_nakshatras", {}):
        return False
        
    nak_norm = normalize_name(nakshatra)
    enemy_list = config["enemy_nakshatras"][planet]
    
    for enemy_nak in enemy_list:
        if nak_norm == normalize_name(enemy_nak):
            return True
    return False

st.title("📅 Astro-Trading Signals — Intraday Windows")

# === Debug Section ===
with st.expander("🔍 Debug Information"):
    st.write("**Config Structure:**")
    st.json(config)

# === File Uploaders ===
watchlist_file = st.file_uploader("Upload Watchlist TXT", type="txt")
transit_file = st.file_uploader("Upload Planetary Transit TXT", type="txt")

if watchlist_file and transit_file:
    try:
        # Load watchlist
        watchlist_content = watchlist_file.read().decode('utf-8')
        watchlist_symbols = [line.strip() for line in watchlist_content.split('\n') if line.strip()]
        
        st.write(f"**Loaded {len(watchlist_symbols)} symbols from watchlist**")
        st.write("Sample symbols:", watchlist_symbols[:5])
        
        # Load planetary transit
        df_transit = pd.read_csv(transit_file, sep="\t")
        df_transit.columns = [c.strip() for c in df_transit.columns]
        
        st.write("**Planetary Transit Data:**")
        st.dataframe(df_transit.head())
        
        # Debug: Show unique planets and nakshatras
        st.write("**Unique Planets in data:**", df_transit["Planet"].unique().tolist())
        st.write("**Unique Nakshatras in data:**", df_transit["Nakshatra"].unique().tolist())
        
        today_str = datetime.now().strftime("%d-%b-%Y")
        generated_time = datetime.now().strftime("%d-%b-%Y %H:%M")
        
        all_signals = []
        debug_info = []
        
        # === Process each sector ===
        sectors_key = "sectors" if "sectors" in config else "sector_planets"
        
        for sector, planets in config[sectors_key].items():
            st.write(f"**Processing Sector: {sector}**")
            
            # Filter symbols for this sector
            sector_symbols = [s for s in watchlist_symbols if sector.upper() in s.upper()]
            st.write(f"Symbols for {sector}: {sector_symbols}")
            
            for planet in planets:
                st.write(f"Processing Planet: {planet}")
                
                # Filter transit data for this planet
                planet_rows = df_transit[df_transit["Planet"].str.strip() == planet].sort_values(by="Time")
                
                if planet_rows.empty:
                    st.warning(f"No transit data found for planet: {planet}")
                    continue
                
                sentiment_rows = []
                
                # FIXED: Correct syntax for iterrows()
                for _, row in planet_rows.iterrows():
                    nakshatra = row["Nakshatra"].strip()
                    time_val = row["Time"]
                    
                    # Debug each nakshatra check
                    is_friend = is_friendly(planet, nakshatra)
                    is_enem = is_enemy(planet, nakshatra)
                    
                    debug_info.append({
                        "Planet": planet,
                        "Nakshatra": nakshatra,
                        "Time": time_val,
                        "Is_Friendly": is_friend,
                        "Is_Enemy": is_enem
                    })
                    
                    if is_friend:
                        sentiment_rows.append((time_val, "Bullish"))
                        st.success(f"✅ BULLISH: {planet} in {nakshatra} at {time_val}")
                    elif is_enem:
                        sentiment_rows.append((time_val, "Bearish"))
                        st.error(f"❌ BEARISH: {planet} in {nakshatra} at {time_val}")
                    else:
                        st.info(f"⚪ NEUTRAL: {planet} in {nakshatra} at {time_val}")
                
                # === Group continuous sentiment periods ===
                grouped = []
                if sentiment_rows:
                    current_sentiment = sentiment_rows[0][1]
                    start_time = sentiment_rows[0][0]
                    
                    for i in range(1, len(sentiment_rows)):
                        time_val, sentiment = sentiment_rows[i]
                        if sentiment != current_sentiment:
                            grouped.append((current_sentiment, start_time, sentiment_rows[i-1][0]))
                            current_sentiment = sentiment
                            start_time = time_val
                    
                    # Don't forget the last group
                    grouped.append((current_sentiment, start_time, sentiment_rows[-1][0]))
                
                # === Map to symbols ===
                for sentiment, entry, exit_time in grouped:
                    for symbol in sector_symbols:
                        all_signals.append((symbol, sentiment, entry, exit_time))
        
        # === Show Debug Information ===
        with st.expander("🔍 Detailed Debug Info"):
            debug_df = pd.DataFrame(debug_info)
            st.dataframe(debug_df)
            
            bullish_count = debug_df["Is_Friendly"].sum()
            bearish_count = debug_df["Is_Enemy"].sum()
            neutral_count = len(debug_df) - bullish_count - bearish_count
            
            st.metric("Bullish Signals", bullish_count)
            st.metric("Bearish Signals", bearish_count) 
            st.metric("Neutral Signals", neutral_count)
        
        # === Output Final Signals ===
        if all_signals:
            st.write(f"📅 **Astro-Trading Signals — {today_str} (Generated {generated_time})**")
            
            signal_message = f"📅 Astro-Trading Signals — {today_str} (Generated {generated_time})\n"
            
            for symbol, sentiment, entry, exit_time in all_signals:
                emoji = "🟢" if sentiment == "Bullish" else "🔴"
                signal_line = f"{emoji} {symbol} → {sentiment} | Entry: {entry} | Exit: {exit_time}"
                st.write(signal_line)
                signal_message += signal_line + "\n"
            
            # === Telegram Send Button ===
            if st.button("📤 Send to Telegram"):
                try:
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    payload = {"chat_id": CHAT_ID, "text": signal_message}
                    response = requests.post(url, data=payload)
                    
                    if response.status_code == 200:
                        st.success("✅ Sent to Telegram successfully!")
                    else:
                        st.error(f"❌ Failed to send: {response.text}")
                except Exception as e:
                    st.error(f"❌ Error sending to Telegram: {e}")
        else:
            st.warning("⚠️ No bullish or bearish signals found for today.")
            st.info("Check the debug information above to see why signals might not be generated.")
            
    except Exception as e:
        st.error(f"❌ Error processing files: {e}")
        st.write("**Error details:**", str(e))
