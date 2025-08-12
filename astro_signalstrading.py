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

# === ENHANCED CONFIG ===
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

def parse_multiple_transit_files(uploaded_files):
    """Parse multiple transit files and combine them."""
    all_data = []
    file_info = {}
    
    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        file_content = uploaded_file.read().decode('utf-8')
        
        # Reset file pointer for multiple reads
        uploaded_file.seek(0)
        
        lines = file_content.strip().split('\n')
        file_data = []
        
        for line in lines:
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
                        
                        entry = {
                            'Planet': planet_code,
                            'DateTime': dt,
                            'Date': dt.date(),
                            'Time': dt.strftime('%H:%M:%S'),
                            'Nakshatra': nakshatra,
                            'Source_File': file_name
                        }
                        
                        file_data.append(entry)
                        all_data.append(entry)
                        
                except Exception as e:
                    continue
        
        file_info[file_name] = {
            'records': len(file_data),
            'dates': list(set([d['Date'] for d in file_data])),
            'planets': list(set([d['Planet'] for d in file_data]))
        }
    
    return pd.DataFrame(all_data), file_info

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

def compare_planetary_positions(df_transit, date1, date2):
    """Compare planetary positions between two dates."""
    
    comparisons = []
    
    # Get unique planets
    planets = df_transit['Planet'].unique()
    
    for planet in planets:
        # Get positions for date1
        pos1_data = df_transit[
            (df_transit['Planet'] == planet) & 
            (df_transit['Date'] <= date1)
        ].sort_values('DateTime')
        
        # Get positions for date2
        pos2_data = df_transit[
            (df_transit['Planet'] == planet) & 
            (df_transit['Date'] <= date2)
        ].sort_values('DateTime')
        
        pos1 = pos1_data.iloc[-1]['Nakshatra'] if not pos1_data.empty else "No Data"
        pos2 = pos2_data.iloc[-1]['Nakshatra'] if not pos2_data.empty else "No Data"
        
        comparisons.append({
            'Planet': PLANET_MAPPING.get(planet, planet),
            f'Position_{date1}': pos1,
            f'Position_{date2}': pos2,
            'Changed': pos1 != pos2,
            'Same': pos1 == pos2
        })
    
    return pd.DataFrame(comparisons)

def generate_signals_with_comparison(df_transit, watchlist_symbols, selected_date, config):
    """Generate signals and show comparison."""
    
    signals = []
    debug_info = []
    
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
            # Get latest position for selected date
            planet_data = df_transit[
                (df_transit['Planet'] == planet) & 
                (df_transit['Date'] <= selected_date)
            ].sort_values('DateTime')
            
            if planet_data.empty:
                continue
                
            latest = planet_data.iloc[-1]
            nakshatra = latest['Nakshatra']
            
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
                'Sentiment': sentiment,
                'Sector': sector,
                'Data_Date': latest['Date'],
                'Source_File': latest['Source_File']
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
                        'Nakshatra': nakshatra
                    })
    
    return signals, debug_info

# === STREAMLIT UI ===
st.title("📅 Multi-File Astro-Trading Signals Analyzer")

# Important notice
st.info("📊 **Enhanced System**: Upload multiple transit files to compare different dates and see exactly why results might be the same.")

config = load_config()

# Date selector
selected_date = st.date_input(
    "Select Date for Analysis",
    value=datetime(2025, 8, 12).date(),
    min_value=datetime(2025, 8, 10).date(),
    max_value=datetime(2025, 8, 20).date()
)

# File uploaders
st.subheader("📁 Upload Files")
watchlist_file = st.file_uploader("Upload Watchlist", type="txt")
transit_files = st.file_uploader(
    "Upload Transit Files (multiple files supported)", 
    type="txt", 
    accept_multiple_files=True,
    help="Upload both transit_aug12.txt and transit_aug13.txt to compare"
)

if watchlist_file and transit_files:
    try:
        # Load watchlist
        watchlist_content = watchlist_file.read().decode('utf-8')
        watchlist_symbols = [line.strip() for line in watchlist_content.split('\n') if line.strip()]
        
        # Parse multiple transit files
        df_transit, file_info = parse_multiple_transit_files(transit_files)
        
        # Display file information
        st.success(f"✅ Loaded {len(watchlist_symbols)} symbols from {len(transit_files)} transit files")
        
        # Show file details
        with st.expander("📊 File Information"):
            for filename, info in file_info.items():
                st.write(f"**{filename}:**")
                st.write(f"  - Records: {info['records']}")
                st.write(f"  - Dates: {info['dates']}")
                st.write(f"  - Planets: {info['planets']}")
        
        # Show comparison if multiple dates available
        available_dates = sorted(df_transit['Date'].unique())
        if len(available_dates) >= 2:
            st.subheader("🔍 Planetary Position Comparison")
            
            date1 = available_dates[0]
            date2 = available_dates[1] if len(available_dates) > 1 else available_dates[0]
            
            comparison_df = compare_planetary_positions(df_transit, date1, date2)
            
            st.write(f"**Comparing {date1} vs {date2}:**")
            st.dataframe(comparison_df)
            
            # Count changes
            changed_count = comparison_df['Changed'].sum()
            same_count = comparison_df['Same'].sum()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🔄 Planets Changed", changed_count)
            with col2:
                st.metric("⚪ Planets Same", same_count)
            
            if changed_count == 0:
                st.warning("⚠️ **No planetary positions changed!** This is why you're getting identical results.")
            else:
                st.success(f"✅ {changed_count} planets changed positions, so signals should be different.")
        
        # Generate signals for selected date
        signals, debug_info = generate_signals_with_comparison(df_transit, watchlist_symbols, selected_date, config)
        
        # Display debug information
        with st.expander("🔍 Detailed Planetary Analysis"):
            if debug_info:
                debug_df = pd.DataFrame(debug_info)
                st.dataframe(debug_df)
                
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
                        st.success(f"🟢 {signal['Symbol']} | {signal['Entry']}-{signal['Exit']} | {signal['Planet']} in {signal['Nakshatra']}")
                else:
                    st.info("No bullish signals found")
            
            with col2:
                st.subheader(f"🔴 Bearish Signals ({len(bearish_signals)})")
                if bearish_signals:
                    for signal in bearish_signals:
                        st.error(f"🔴 {signal['Symbol']} | {signal['Entry']}-{signal['Exit']} | {signal['Planet']} in {signal['Nakshatra']}")
                else:
                    st.info("No bearish signals found")
            
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
        st.write("**Error details:**", str(e))
else:
    st.info("👆 Please upload watchlist and transit files to analyze.")
    
    st.markdown("""
    ### 🔍 Why You're Getting Same Results:
    
    **Most Likely Causes:**
    1. 📊 **Identical planetary positions** in both transit files
    2. 🕐 **Same time periods** covered in both files  
    3. ⚪ **All planets in neutral nakshatras** for both dates
    
    ### 📋 How This Enhanced System Helps:
    
    1. **📁 Multi-File Support**: Upload both transit_aug12.txt and transit_aug13.txt
    2. **🔍 Position Comparison**: See exactly which planets changed
    3. **📊 Detailed Analysis**: Understand why signals are same/different
    4. **🎯 Root Cause**: Identify the exact reason for identical results
    
    ### 💡 Expected Behavior:
    - If planetary positions are **identical** → Same signals ✅
    - If planetary positions **changed** → Different signals ✅
    """)
