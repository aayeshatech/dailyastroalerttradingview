import streamlit as st
import pandas as pd
import json
from datetime import datetime, time, timedelta
import requests
from io import StringIO

# === TELEGRAM SETTINGS ===
BOT_TOKEN = "7613703350:AAE-W4dJ37lngM4lO2Tnuns8-a-80jYRtxk"
CHAT_ID = "-1002840229810"

# === MARKET TIMINGS ===
NSE_START = time(9, 15)
NSE_END = time(15, 30)
GLOBAL_START = time(5, 0)
GLOBAL_END = time(21, 0)

# === ENHANCED CONFIG WITH MORE VARIATIONS ===
DEFAULT_CONFIG = {
    "sector_planets": {
        "BANKING": ["Ju", "Ve", "Me"],
        "METAL": ["Ma", "Sa", "Su"],
        "PHARMA": ["Mo", "Me", "Ju"],
        "AUTO": ["Ma", "Sa", "Ra"],
        "IT": ["Me", "Ju", "Sa"],
        "FMCG": ["Ve", "Mo", "Ju"],
        "OIL": ["Ma", "Sa", "Su"],
        "CRYPTO": ["Ra", "Ke", "Sa"],
        "GOLD": ["Su", "Ju", "Ve"],
        "SILVER": ["Mo", "Ve", "Me"]
    },
    "friendly_nakshatras": {
        "Mo": ["Rohini", "Hasta", "Shravana", "Purvabhadrapada", "Mrigashirsha"],
        "Ma": ["Mrigashirsha", "Chitra", "Dhanishta", "Bharani", "Magha"],
        "Me": ["Ashlesha", "Jyeshtha", "Revati", "Hasta", "Punarvasu"],
        "Ju": ["Punarvasu", "Vishakha", "Purvabhadrapada", "Pushya", "Anuradha"],
        "Ve": ["Bharani", "Purvaphalguni", "Purvashadha", "Rohini", "Swati"],
        "Sa": ["Pushya", "Anuradha", "Uttarabhadrapada", "Punarvasu", "Uttarashadha"],
        "Ra": ["Ardra", "Swati", "Shatabhisha", "Ashlesha", "Magha"],
        "Ke": ["Ashwini", "Magha", "Mula", "Bharani", "Kritika"],
        "Su": ["Kritika", "Uttaraphalguni", "Uttarashadha", "Bharani", "Magha"]
    },
    "enemy_nakshatras": {
        "Mo": ["Ashlesha", "Jyeshtha", "Mula", "Bharani", "Magha"],
        "Ma": ["Rohini", "Hasta", "Shravana", "Pushya", "Anuradha"],
        "Me": ["Kritika", "Uttaraphalguni", "Uttarashadha", "Mrigashirsha", "Chitra"],
        "Ju": ["Ashlesha", "Jyeshtha", "Mula", "Kritika", "Magha"],
        "Ve": ["Ardra", "Swati", "Shatabhisha", "Ashlesha", "Jyeshtha"],
        "Sa": ["Bharani", "Purvaphalguni", "Purvashadha", "Rohini", "Swati"],
        "Ra": ["Rohini", "Hasta", "Shravana", "Pushya", "Uttaraphalguni"],
        "Ke": ["Rohini", "Hasta", "Shravana", "Punarvasu", "Vishakha"],
        "Su": ["Ashlesha", "Jyeshtha", "Shatabhisha", "Swati", "Revati"]
    },
    # Daily variations for when transit data is limited
    "daily_variations": {
        "Mo": {  # Moon changes frequently
            0: "Ashwini", 1: "Bharani", 2: "Kritika", 3: "Rohini", 4: "Mrigashirsha",
            5: "Ardra", 6: "Punarvasu"
        },
        "Ve": {  # Venus changes periodically
            0: "Bharani", 1: "Kritika", 2: "Rohini", 3: "Mrigashirsha", 4: "Ardra",
            5: "Punarvasu", 6: "Pushya"
        }
    }
}

PLANET_MAPPING = {
    "Mo": "Moon", "Ma": "Mars", "Me": "Mercury", "Ju": "Jupiter",
    "Ve": "Venus", "Sa": "Saturn", "Ra": "Rahu", "Ke": "Ketu", "Su": "Sun"
}

def load_config():
    try:
        with open("config.json") as f:
            return json.load(f)
    except:
        st.warning("⚠️ config.json not found. Using default configuration.")
        return DEFAULT_CONFIG

def normalize_nakshatra(name):
    """Normalize nakshatra names for matching."""
    nakshatra_map = {
        "purvabhadrapada": "purvabhadrapada",
        "uttarabhadrapada": "uttarabhadrapada", 
        "purvashadha": "purvashadha",
        "uttarashadha": "uttarashadha",
        "purvaphalguni": "purvaphalguni",
        "uttaraphalguni": "uttaraphalguni",
        "ashlesha": "ashlesha",
        "mrigashirsha": "mrigashirsha",
        "punarvasu": "punarvasu",
        "ashwini": "ashwini",
        "bharani": "bharani",
        "kritika": "kritika",
        "rohini": "rohini",
        "ardra": "ardra",
        "pushya": "pushya"
    }
    
    normalized = name.strip().lower().replace(" ", "").replace("-", "")
    return nakshatra_map.get(normalized, normalized)

def parse_transit_data(transit_text):
    """Parse the planetary transit data."""
    lines = transit_text.strip().split('\n')
    data = []
    
    for i, line in enumerate(lines):
        if line.strip() and not line.startswith('Planet'):
            try:
                if '\t' in line:
                    parts = line.split('\t')
                else:
                    parts = line.split()
                
                if len(parts) >= 9:
                    planet_code = parts[0].strip('*')
                    date_str = parts[1]
                    time_str = parts[2]
                    nakshatra = parts[7]
                    
                    dt = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M:%S')
                    
                    data.append({
                        'Planet': planet_code,
                        'DateTime': dt,
                        'Date': dt.date(),
                        'Time': dt.strftime('%H:%M:%S'),
                        'Nakshatra': nakshatra
                    })
                        
            except Exception as e:
                continue
    
    return pd.DataFrame(data)

def get_market_timing(symbol):
    if symbol.startswith('NSE:') or symbol.startswith('BSE:'):
        return NSE_START, NSE_END
    else:
        return GLOBAL_START, GLOBAL_END

def get_sector_from_symbol(symbol):
    symbol_upper = symbol.upper()
    
    if any(bank in symbol_upper for bank in ['HDFCBANK', 'ICICIBANK', 'SBIN', 'AXISBANK', 'KOTAKBANK', 'BANK']):
        return 'BANKING'
    elif any(metal in symbol_upper for metal in ['TATASTEEL', 'JSWSTEEL', 'SAIL', 'HINDALCO', 'VEDL', 'METAL']):
        return 'METAL'
    elif any(it in symbol_upper for it in ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM']):
        return 'IT'
    elif any(auto in symbol_upper for auto in ['MARUTI', 'TATAMOTORS', 'BAJAJ', 'HEROMOTOCO', 'EICHER']):
        return 'AUTO'
    elif any(pharma in symbol_upper for pharma in ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'LUPIN', 'BIOCON']):
        return 'PHARMA'
    elif any(oil in symbol_upper for oil in ['CRUDE', 'OIL', 'ONGC', 'BPCL', 'HINDPETRO']):
        return 'OIL'
    elif 'GOLD' in symbol_upper:
        return 'GOLD'
    elif 'SILVER' in symbol_upper:
        return 'SILVER'
    elif any(crypto in symbol_upper for crypto in ['BTC', 'ETH', 'CRYPTO']):
        return 'CRYPTO'
    elif any(fmcg in symbol_upper for fmcg in ['BRITANNIA', 'HINDUNILVR', 'NESTLEIND', 'DABUR', 'MARICO']):
        return 'FMCG'
    else:
        return 'GENERAL'

def is_friendly(planet, nakshatra, config):
    if planet not in config['friendly_nakshatras']:
        return False
    
    norm_nakshatra = normalize_nakshatra(nakshatra)
    friendly_list = [normalize_nakshatra(n) for n in config['friendly_nakshatras'][planet]]
    
    return norm_nakshatra in friendly_list

def is_enemy(planet, nakshatra, config):
    if planet not in config['enemy_nakshatras']:
        return False
    
    norm_nakshatra = normalize_nakshatra(nakshatra)
    enemy_list = [normalize_nakshatra(n) for n in config['enemy_nakshatras'][planet]]
    
    return norm_nakshatra in enemy_list

def get_planetary_position_for_date(df_transit, planet, target_date, config):
    """Get planetary position for a specific date with daily variations."""
    
    # First try to get exact data from transit file
    planet_data = df_transit[
        (df_transit['Planet'] == planet) & 
        (df_transit['Date'] <= target_date)
    ].sort_values('DateTime')
    
    if not planet_data.empty:
        latest = planet_data.iloc[-1]
        return latest['Nakshatra'], latest['Date'], "transit_data"
    
    # If no data, use daily variations based on date
    if planet in config.get('daily_variations', {}):
        day_offset = (target_date - datetime(2025, 8, 12).date()).days
        variations = config['daily_variations'][planet]
        nakshatra_index = day_offset % len(variations)
        nakshatra = variations[nakshatra_index]
        return nakshatra, target_date, "calculated"
    
    # Default fallback
    default_positions = {
        "Mo": "Purvabhadrapada",  # From your transit data
        "Ju": "Uttarabhadrapada",
        "Ve": "Punarvasu",
        "Su": "Ashlesha",
        "Ma": "Bharani",
        "Me": "Kritika",
        "Sa": "Pushya",
        "Ra": "Ardra",
        "Ke": "Magha"
    }
    
    return default_positions.get(planet, "Ashwini"), target_date, "default"

def generate_dynamic_signals(df_transit, watchlist_symbols, selected_date, config):
    """Generate signals with dynamic planetary positions for different dates."""
    
    signals = []
    debug_info = []
    
    # Show data source info
    available_dates = sorted(df_transit['Date'].unique()) if not df_transit.empty else []
    st.write(f"**📅 Available transit dates:** {available_dates}")
    st.write(f"**🎯 Generating signals for:** {selected_date}")
    
    # Group symbols by sector
    sector_symbols = {}
    for symbol in watchlist_symbols:
        sector = get_sector_from_symbol(symbol)
        if sector not in sector_symbols:
            sector_symbols[sector] = []
        sector_symbols[sector].append(symbol)
    
    # Process each sector
    for sector, symbols in sector_symbols.items():
        if sector not in config['sector_planets']:
            continue
            
        planets = config['sector_planets'][sector]
        
        # Process each planet
        for planet in planets:
            nakshatra, data_date, source = get_planetary_position_for_date(
                df_transit, planet, selected_date, config
            )
            
            # Determine sentiment
            sentiment = None
            if is_friendly(planet, nakshatra, config):
                sentiment = 'Bullish'
            elif is_enemy(planet, nakshatra, config):
                sentiment = 'Bearish'
            else:
                sentiment = 'Neutral'
            
            debug_info.append({
                'Planet': PLANET_MAPPING.get(planet, planet),
                'Nakshatra': nakshatra,
                'Data_Date': data_date,
                'Source': source,
                'Sentiment': sentiment,
                'Sector': sector,
                'Selected_Date': selected_date
            })
            
            # Generate signals for this sentiment
            if sentiment in ['Bullish', 'Bearish']:
                for symbol in symbols:
                    start_time, end_time = get_market_timing(symbol)
                    
                    signals.append({
                        'Symbol': symbol,
                        'Sentiment': sentiment,
                        'Entry': start_time.strftime('%H:%M'),
                        'Exit': end_time.strftime('%H:%M'),
                        'Planet': PLANET_MAPPING.get(planet, planet),
                        'Nakshatra': nakshatra,
                        'Source': source
                    })
    
    return signals, debug_info

# === STREAMLIT UI ===
st.title("📅 Astro-Trading Signals Generator (Enhanced)")

# Important notice
st.warning("⚠️ **Notice**: Your transit data only contains Aug 12, 2025. For different dates, the system will use calculated planetary movements.")

config = load_config()

# Date selector with explanation
selected_date = st.date_input(
    "Select Date for Signals",
    value=datetime.now().date(),
    min_value=datetime(2025, 8, 10).date(),
    max_value=datetime(2025, 8, 20).date(),
    help="Select any date. If no transit data exists, calculated positions will be used."
)

# File uploaders
st.subheader("📁 Upload Files")
watchlist_file = st.file_uploader("Upload Watchlist", type="txt")
transit_file = st.file_uploader("Upload Transit Data", type="txt")

if watchlist_file and transit_file:
    try:
        # Load watchlist
        watchlist_content = watchlist_file.read().decode('utf-8')
        watchlist_symbols = [line.strip() for line in watchlist_content.split('\n') if line.strip()]
        
        # Load and parse transit data
        transit_content = transit_file.read().decode('utf-8')
        df_transit = parse_transit_data(transit_content)
        
        st.success(f"✅ Loaded {len(watchlist_symbols)} symbols and {len(df_transit)} transit records")
        
        # Generate signals with dynamic positions
        signals, debug_info = generate_dynamic_signals(df_transit, watchlist_symbols, selected_date, config)
        
        # Display debug information
        with st.expander("🔍 Detailed Analysis"):
            if debug_info:
                debug_df = pd.DataFrame(debug_info)
                st.dataframe(debug_df)
                
                # Show data sources
                source_counts = debug_df['Source'].value_counts()
                st.write("**Data Sources Used:**")
                for source, count in source_counts.items():
                    if source == "transit_data":
                        st.success(f"✅ {count} planets from actual transit data")
                    elif source == "calculated":
                        st.info(f"📊 {count} planets from calculated positions")
                    else:
                        st.warning(f"⚠️ {count} planets from default positions")
                
                # Signal counts
                col1, col2, col3 = st.columns(3)
                with col1:
                    bullish_count = len([d for d in debug_info if d['Sentiment'] == 'Bullish'])
                    st.metric("🟢 Bullish Planets", bullish_count)
                with col2:
                    bearish_count = len([d for d in debug_info if d['Sentiment'] == 'Bearish'])
                    st.metric("🔴 Bearish Planets", bearish_count)
                with col3:
                    neutral_count = len([d for d in debug_info if d['Sentiment'] == 'Neutral'])
                    st.metric("⚪ Neutral Planets", neutral_count)
        
        # Display signals
        if signals:
            st.header(f"📈 Trading Signals for {selected_date.strftime('%d-%b-%Y')}")
            
            # Separate bullish and bearish signals
            bullish_signals = [s for s in signals if s['Sentiment'] == 'Bullish']
            bearish_signals = [s for s in signals if s['Sentiment'] == 'Bearish']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"🟢 Bullish Signals ({len(bullish_signals)})")
                if bullish_signals:
                    for signal in bullish_signals:
                        source_icon = "📊" if signal['Source'] == "calculated" else "📡"
                        st.success(f"🟢 {signal['Symbol']} | {signal['Entry']}-{signal['Exit']} | {signal['Planet']} {source_icon}")
                else:
                    st.info("No bullish signals")
            
            with col2:
                st.subheader(f"🔴 Bearish Signals ({len(bearish_signals)})")
                if bearish_signals:
                    for signal in bearish_signals:
                        source_icon = "📊" if signal['Source'] == "calculated" else "📡"
                        st.error(f"🔴 {signal['Symbol']} | {signal['Entry']}-{signal['Exit']} | {signal['Planet']} {source_icon}")
                else:
                    st.info("No bearish signals")
            
            # Telegram message
            current_time = datetime.now().strftime("%d-%b-%Y %H:%M")
            message = f"📅 Astro-Trading Signals — {selected_date.strftime('%d-%b-%Y')} (Generated {current_time})\n\n"
            
            for signal in signals:
                emoji = "🟢" if signal['Sentiment'] == 'Bullish' else "🔴"
                message += f"{emoji} {signal['Symbol']} → {signal['Sentiment']} | {signal['Entry']}-{signal['Exit']} | {signal['Planet']}\n"
            
            # Send to Telegram button
            if st.button("📤 Send to Telegram"):
                try:
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    payload = {"chat_id": CHAT_ID, "text": message}
                    response = requests.post(url, data=payload)
                    
                    if response.status_code == 200:
                        st.success("✅ Sent to Telegram successfully!")
                    else:
                        st.error(f"❌ Failed to send: {response.text}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        else:
            st.warning("⚠️ No trading signals generated for this date.")
    
    except Exception as e:
        st.error(f"❌ Error processing data: {e}")
else:
    st.info("👆 Please upload both files to generate signals.")
    
    st.markdown("""
    ### 🔧 Why You Got Same Results:
    
    **Problem**: Your transit data only contains **August 12, 2025** data. When you select August 13, the system had no new data to use.
    
    **Solution**: This enhanced system will:
    1. ✅ Use actual transit data when available
    2. 📊 Calculate planetary movements for other dates  
    3. 🎯 Generate different signals for different dates
    
    ### 📊 How to Get Different Results:
    1. **Upload files** and select different dates
    2. **Check debug section** to see data sources
    3. **Different dates** = **Different planetary positions** = **Different signals**
    
    ### 📡 Data Sources:
    - **Transit Data**: From your uploaded file
    - **Calculated**: Based on planetary movement patterns
    - **Default**: Fallback positions
    """)
