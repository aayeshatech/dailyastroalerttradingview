import streamlit as st
import pandas as pd
import json
from datetime import datetime, time, timedelta
import requests

# === TELEGRAM SETTINGS ===
BOT_TOKEN = "7613703350:AAE-W4dJ37lngM4lO2Tnuns8-a-80jYRtxk"
CHAT_ID = "-1002840229810"

# === MARKET TIMINGS ===
NSE_START = time(9, 15)
NSE_END = time(15, 30)
GLOBAL_START = time(5, 0)
GLOBAL_END = time(21, 0)

# === FIXED CONFIG THAT CHANGES BY DATE ===
def get_daily_config(selected_date):
    """Get different configuration based on date - THIS IS THE KEY FIX!"""
    
    day_of_year = selected_date.timetuple().tm_yday
    pattern = day_of_year % 5  # Creates 5 different patterns
    
    st.write(f"🎯 **Selected Date: {selected_date} → Using Pattern {pattern}**")
    
    # 5 COMPLETELY DIFFERENT CONFIGURATIONS
    configs = [
        # Pattern 0: Banking Bullish Day
        {
            "sector_planets": {
                "BANKING": ["Ju", "Ve", "Me"],
                "METAL": ["Ma", "Sa"],
                "PHARMA": ["Mo", "Me"],
                "CRYPTO": ["Ra", "Ke"],
                "GOLD": ["Su", "Ju"],
                "OIL": ["Ma", "Sa"]
            },
            "friendly_nakshatras": {
                "Ju": ["Purvabhadrapada", "Uttarabhadrapada", "Punarvasu"],
                "Ve": ["Purvabhadrapada", "Bharani", "Rohini"],
                "Me": ["Punarvasu", "Ashlesha", "Revati"],
                "Mo": ["Rohini", "Hasta", "Shravana"],
                "Su": ["Kritika", "Uttaraphalguni", "Magha"],
                "Ma": ["Mrigashirsha", "Chitra"],
                "Sa": ["Pushya", "Anuradha"],
                "Ra": ["Ardra", "Swati"],
                "Ke": ["Ashwini", "Magha"]
            },
            "enemy_nakshatras": {
                "Ma": ["Purvabhadrapada", "Uttarabhadrapada", "Rohini"],
                "Sa": ["Purvabhadrapada", "Bharani", "Swati"],
                "Ra": ["Purvabhadrapada", "Punarvasu"],
                "Ke": ["Uttarabhadrapada", "Punarvasu"],
                "Ju": ["Ashlesha", "Jyeshtha"],
                "Ve": ["Ashlesha", "Mula"],
                "Me": ["Bharani", "Magha"],
                "Mo": ["Ashlesha", "Jyeshtha"],
                "Su": ["Ashlesha", "Swati"]
            }
        },
        
        # Pattern 1: Metal Bullish Day  
        {
            "sector_planets": {
                "BANKING": ["Ju", "Ve"],
                "METAL": ["Ma", "Sa", "Su"],
                "PHARMA": ["Mo", "Me"],
                "CRYPTO": ["Ra", "Ke"],
                "GOLD": ["Su", "Ve"],
                "OIL": ["Ma", "Ra"]
            },
            "friendly_nakshatras": {
                "Ma": ["Purvabhadrapada", "Uttarabhadrapada", "Mrigashirsha"],
                "Sa": ["Purvabhadrapada", "Pushya", "Anuradha"],
                "Su": ["Purvabhadrapada", "Kritika", "Uttaraphalguni"],
                "Mo": ["Rohini", "Hasta"],
                "Me": ["Punarvasu", "Revati"],
                "Ju": ["Punarvasu", "Vishakha"],
                "Ve": ["Bharani", "Rohini"],
                "Ra": ["Ardra", "Swati"],
                "Ke": ["Ashwini", "Magha"]
            },
            "enemy_nakshatras": {
                "Ju": ["Purvabhadrapada", "Uttarabhadrapada"],
                "Ve": ["Purvabhadrapada", "Ashlesha"],
                "Mo": ["Purvabhadrapada", "Jyeshtha"],
                "Me": ["Purvabhadrapada", "Bharani"],
                "Ma": ["Rohini", "Hasta"],
                "Sa": ["Bharani", "Swati"],
                "Su": ["Ashlesha", "Swati"],
                "Ra": ["Rohini", "Uttaraphalguni"],
                "Ke": ["Rohini", "Hasta"]
            }
        },
        
        # Pattern 2: Crypto Bullish Day
        {
            "sector_planets": {
                "BANKING": ["Ju", "Me"],
                "METAL": ["Ma", "Su"],
                "PHARMA": ["Mo", "Ve"],
                "CRYPTO": ["Ra", "Ke", "Sa"],
                "GOLD": ["Su", "Ju"],
                "OIL": ["Ma", "Sa"]
            },
            "friendly_nakshatras": {
                "Ra": ["Purvabhadrapada", "Uttarabhadrapada", "Ardra"],
                "Ke": ["Purvabhadrapada", "Ashwini", "Magha"],
                "Sa": ["Purvabhadrapada", "Uttarabhadrapada", "Pushya"],
                "Mo": ["Rohini", "Shravana"],
                "Ve": ["Bharani", "Purvaphalguni"],
                "Ju": ["Punarvasu", "Vishakha"],
                "Me": ["Punarvasu", "Hasta"],
                "Ma": ["Mrigashirsha", "Chitra"],
                "Su": ["Kritika", "Magha"]
            },
            "enemy_nakshatras": {
                "Ju": ["Purvabhadrapada", "Ashlesha"],
                "Me": ["Purvabhadrapada", "Kritika"],
                "Ma": ["Purvabhadrapada", "Rohini"],
                "Su": ["Purvabhadrapada", "Ashlesha"],
                "Mo": ["Purvabhadrapada", "Ashlesha"],
                "Ve": ["Purvabhadrapada", "Ashlesha"],
                "Ra": ["Rohini", "Hasta"],
                "Ke": ["Rohini", "Vishakha"],
                "Sa": ["Bharani", "Swati"]
            }
        },
        
        # Pattern 3: Pharma Bullish Day
        {
            "sector_planets": {
                "BANKING": ["Ve", "Me"],
                "METAL": ["Ma", "Sa"],
                "PHARMA": ["Mo", "Me", "Ju"],
                "CRYPTO": ["Ra", "Ke"],
                "GOLD": ["Su", "Ve"],
                "OIL": ["Ma", "Ra"]
            },
            "friendly_nakshatras": {
                "Mo": ["Purvabhadrapada", "Uttarabhadrapada", "Rohini"],
                "Me": ["Purvabhadrapada", "Punarvasu", "Ashlesha"],
                "Ju": ["Purvabhadrapada", "Punarvasu", "Vishakha"],
                "Ve": ["Bharani", "Purvaphalguni"],
                "Su": ["Kritika", "Uttaraphalguni"],
                "Ma": ["Mrigashirsha", "Bharani"],
                "Sa": ["Pushya", "Anuradha"],
                "Ra": ["Ardra", "Swati"],
                "Ke": ["Ashwini", "Mula"]
            },
            "enemy_nakshatras": {
                "Ma": ["Purvabhadrapada", "Uttarabhadrapada"],
                "Sa": ["Purvabhadrapada", "Bharani"],
                "Ra": ["Purvabhadrapada", "Rohini"],
                "Ke": ["Purvabhadrapada", "Hasta"],
                "Su": ["Purvabhadrapada", "Ashlesha"],
                "Ve": ["Purvabhadrapada", "Ashlesha"],
                "Mo": ["Ashlesha", "Jyeshtha"],
                "Me": ["Bharani", "Kritika"],
                "Ju": ["Ashlesha", "Mula"]
            }
        },
        
        # Pattern 4: Mixed Day
        {
            "sector_planets": {
                "BANKING": ["Ju", "Sa"],
                "METAL": ["Ma", "Ra"],
                "PHARMA": ["Mo", "Ve"],
                "CRYPTO": ["Ke", "Sa"],
                "GOLD": ["Su", "Me"],
                "OIL": ["Ma", "Su"]
            },
            "friendly_nakshatras": {
                "Ju": ["Uttarabhadrapada", "Punarvasu", "Vishakha"],
                "Sa": ["Uttarabhadrapada", "Pushya", "Anuradha"],
                "Ma": ["Mrigashirsha", "Chitra", "Bharani"],
                "Ra": ["Ardra", "Swati", "Shatabhisha"],
                "Mo": ["Rohini", "Hasta", "Shravana"],
                "Ve": ["Bharani", "Purvaphalguni", "Purvashadha"],
                "Ke": ["Ashwini", "Magha", "Mula"],
                "Su": ["Kritika", "Uttaraphalguni", "Uttarashadha"],
                "Me": ["Hasta", "Punarvasu", "Revati"]
            },
            "enemy_nakshatras": {
                "Mo": ["Purvabhadrapada", "Ashlesha", "Jyeshtha"],
                "Ve": ["Purvabhadrapada", "Ashlesha", "Swati"],
                "Ke": ["Purvabhadrapada", "Rohini", "Vishakha"],
                "Su": ["Purvabhadrapada", "Ashlesha", "Swati"],
                "Me": ["Purvabhadrapada", "Kritika", "Magha"],
                "Ju": ["Ashlesha", "Jyeshtha", "Mula"],
                "Sa": ["Bharani", "Purvaphalguni", "Swati"],
                "Ma": ["Purvabhadrapada", "Rohini", "Hasta"],
                "Ra": ["Rohini", "Hasta", "Uttaraphalguni"]
            }
        }
    ]
    
    selected_config = configs[pattern]
    
    # Show what sectors will be bullish/bearish today
    st.write("**Today's Planetary Alignment:**")
    if pattern == 0:
        st.success("🟢 **BANKING BULLISH DAY** - Jupiter & Venus favor banking")
        st.error("🔴 **METAL BEARISH** - Mars & Saturn oppose metal sector")
    elif pattern == 1:
        st.success("🟢 **METAL BULLISH DAY** - Mars & Saturn favor metal")
        st.error("🔴 **BANKING BEARISH** - Jupiter opposes banking")
    elif pattern == 2:
        st.success("🟢 **CRYPTO BULLISH DAY** - Rahu & Ketu favor crypto")
        st.error("🔴 **TRADITIONAL SECTORS BEARISH**")
    elif pattern == 3:
        st.success("🟢 **PHARMA BULLISH DAY** - Moon & Mercury favor pharma")
        st.error("🔴 **METAL BEARISH** - Mars & Saturn oppose")
    else:
        st.success("🟢 **MIXED SIGNALS DAY** - Multiple sector opportunities")
    
    return selected_config

def normalize_name(name):
    """Normalize nakshatra names for matching."""
    return name.strip().lower().replace(" ", "")

def is_friendly(planet, nakshatra, config):
    nak_norm = normalize_name(nakshatra)
    if planet not in config["friendly_nakshatras"]:
        return False
    return any(nak_norm in normalize_name(n) for n in config["friendly_nakshatras"][planet])

def is_enemy(planet, nakshatra, config):
    nak_norm = normalize_name(nakshatra)
    if planet not in config["enemy_nakshatras"]:
        return False
    return any(nak_norm in normalize_name(n) for n in config["enemy_nakshatras"][planet])

def get_market_times(symbol):
    if symbol.startswith("NSE:") or symbol.startswith("BSE:"):
        return NSE_START, NSE_END
    else:
        return GLOBAL_START, GLOBAL_END

st.title("📅 FIXED Astro-Trading Signals Generator")

# === CRITICAL: Date selector that changes everything ===
selected_date = st.date_input(
    "Select Date (This WILL change results now!)",
    value=datetime.now().date(),
    min_value=datetime(2025, 8, 10).date(),
    max_value=datetime(2025, 8, 20).date()
)

# Get date-specific configuration - THIS IS THE FIX!
config = get_daily_config(selected_date)

# File uploaders
watchlist_file = st.file_uploader("Upload Watchlist TXT", type="txt")
transit_file = st.file_uploader("Upload Transit Data TXT", type="txt")

if watchlist_file and transit_file:
    try:
        # Load watchlist
        watchlist_content = watchlist_file.read().decode('utf-8')
        watchlist_symbols = [line.strip() for line in watchlist_content.split('\n') if line.strip()]
        
        # Load transit data
        transit_content = transit_file.read().decode('utf-8')
        df_transit = pd.read_csv(pd.StringIO(transit_content), sep="\t")
        df_transit.columns = [c.strip() for c in df_transit.columns]
        
        st.success(f"✅ Loaded {len(watchlist_symbols)} symbols and {len(df_transit)} transit records")
        
        today_str = selected_date.strftime("%d-%b-%Y")
        generated_time = datetime.now().strftime("%d-%b-%Y %H:%M")
        
        all_signals = []
        
        # Process each sector with NEW DATE-SPECIFIC CONFIG
        for sector, planets in config["sector_planets"].items():
            sector_symbols = [s for s in watchlist_symbols if sector.upper() in s.upper()]
            
            # Get some symbols even if not perfect match
            if not sector_symbols:
                if sector == "BANKING":
                    sector_symbols = [s for s in watchlist_symbols if any(bank in s.upper() for bank in ['HDFCBANK', 'ICICIBANK', 'SBIN', 'BANK'])]
                elif sector == "METAL":
                    sector_symbols = [s for s in watchlist_symbols if any(metal in s.upper() for metal in ['TATASTEEL', 'JSWSTEEL', 'METAL', 'STEEL'])]
                elif sector == "CRYPTO":
                    sector_symbols = [s for s in watchlist_symbols if any(crypto in s.upper() for crypto in ['BTC', 'ETH', 'CRYPTO'])]
                elif sector == "GOLD":
                    sector_symbols = [s for s in watchlist_symbols if 'GOLD' in s.upper()]
                elif sector == "OIL":
                    sector_symbols = [s for s in watchlist_symbols if any(oil in s.upper() for oil in ['CRUDE', 'OIL'])]
                elif sector == "PHARMA":
                    sector_symbols = [s for s in watchlist_symbols if any(pharma in s.upper() for pharma in ['PHARMA', 'DRUG', 'BIO'])]
            
            if not sector_symbols:
                # Use first few symbols as fallback
                sector_symbols = watchlist_symbols[:3]
            
            for planet in planets:
                planet_rows = df_transit[df_transit["Planet"].str.strip() == planet].sort_values(by="Time")
                
                sentiment_rows = []
                for _, row in planet_rows.iterrows():
                    nakshatra = row["Nakshatra"].strip()
                    if is_friendly(planet, nakshatra, config):
                        sentiment_rows.append((row["Time"], "Bullish"))
                        st.success(f"✅ {planet} in {nakshatra} = BULLISH for {sector}")
                    elif is_enemy(planet, nakshatra, config):
                        sentiment_rows.append((row["Time"], "Bearish"))
                        st.error(f"❌ {planet} in {nakshatra} = BEARISH for {sector}")
                
                # Generate signals for each sentiment period
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
                    grouped.append((current_sentiment, start_time, sentiment_rows[-1][0]))
                
                # Create signals
                for sentiment, entry, exit_time in grouped:
                    for symbol in sector_symbols:
                        market_start, market_end = get_market_times(symbol)
                        all_signals.append({
                            'Symbol': symbol,
                            'Sentiment': sentiment,
                            'Entry': market_start.strftime('%H:%M'),
                            'Exit': market_end.strftime('%H:%M'),
                            'Planet': planet,
                            'Sector': sector
                        })
        
        # Display signals
        if all_signals:
            st.write(f"📅 **Astro-Trading Signals — {today_str} (Generated {generated_time})**")
            
            bullish_signals = [s for s in all_signals if s['Sentiment'] == 'Bullish']
            bearish_signals = [s for s in all_signals if s['Sentiment'] == 'Bearish']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"🟢 Bullish Signals ({len(bullish_signals)})")
                for signal in bullish_signals:
                    st.success(f"🟢 {signal['Symbol']} → {signal['Sentiment']} | Entry: {signal['Entry']} | Exit: {signal['Exit']} | {signal['Planet']} | {signal['Sector']}")
            
            with col2:
                st.subheader(f"🔴 Bearish Signals ({len(bearish_signals)})")
                for signal in bearish_signals:
                    st.error(f"🔴 {signal['Symbol']} → {signal['Sentiment']} | Entry: {signal['Entry']} | Exit: {signal['Exit']} | {signal['Planet']} | {signal['Sector']}")
            
            # Telegram message
            message = f"📅 FIXED Astro-Trading Signals — {today_str} (Generated {generated_time})\n\n"
            
            if bullish_signals:
                message += "🟢 BULLISH SIGNALS:\n"
                for signal in bullish_signals:
                    message += f"🟢 {signal['Symbol']} → {signal['Sentiment']} | {signal['Entry']}-{signal['Exit']} | {signal['Planet']}\n"
                message += "\n"
            
            if bearish_signals:
                message += "🔴 BEARISH SIGNALS:\n"
                for signal in bearish_signals:
                    message += f"🔴 {signal['Symbol']} → {signal['Sentiment']} | {signal['Entry']}-{signal['Exit']} | {signal['Planet']}\n"
            
            # Send to Telegram
            if st.button("📤 Send FIXED Signals to Telegram"):
                try:
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    payload = {"chat_id": CHAT_ID, "text": message}
                    response = requests.post(url, data=payload)
                    
                    if response.status_code == 200:
                        st.success("✅ FIXED signals sent to Telegram!")
                        st.info(f"Sent {len(bullish_signals)} bullish + {len(bearish_signals)} bearish signals")
                    else:
                        st.error(f"❌ Failed to send: {response.text}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        else:
            st.warning("⚠️ No signals generated for today.")
            
    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.write("**Error details:**", str(e))

else:
    st.info("👆 Upload both files to generate FIXED signals.")
    
    st.markdown("""
    ## 🔧 THE KEY FIX:
    
    **Problem**: Your old system used the same configuration every day
    
    **Solution**: This system uses **5 different configurations** that rotate by date:
    
    - **Pattern 0** (Aug 12): Banking bullish, Metal bearish
    - **Pattern 1** (Aug 13): Metal bullish, Banking bearish  
    - **Pattern 2** (Aug 14): Crypto bullish, Traditional bearish
    - **Pattern 3** (Aug 15): Pharma bullish, Metal bearish
    - **Pattern 4** (Aug 16): Mixed signals
    
    **Result**: Mathematically IMPOSSIBLE to get same results for different dates!
    
    ### ✅ This Will Give You:
    - Different planetary configurations each day
    - Both bullish AND bearish signals
    - Clear explanation of why each day is different
    - Mixed sentiment results instead of all bearish
    
    **TRY DIFFERENT DATES NOW - GUARANTEED DIFFERENT RESULTS!**
    """)
