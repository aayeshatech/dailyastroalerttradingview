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

# === DEFAULT CONFIG ===
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
        "punarvasu": "punarvasu"
    }
    
    normalized = name.strip().lower().replace(" ", "").replace("-", "")
    return nakshatra_map.get(normalized, normalized)

def parse_transit_data(transit_text):
    """Parse the planetary transit data."""
    lines = transit_text.strip().split('\n')
    data = []
    
    st.write("**🔍 Parsing Transit Data:**")
    
    for i, line in enumerate(lines):
        if line.strip() and not line.startswith('Planet'):
            try:
                # Split by multiple delimiters
                if '\t' in line:
                    parts = line.split('\t')
                else:
                    parts = line.split()
                
                if len(parts) >= 9:
                    planet_code = parts[0].strip('*')
                    date_str = parts[1]
                    time_str = parts[2]
                    nakshatra = parts[7]
                    
                    # Parse date and time
                    dt = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M:%S')
                    
                    data.append({
                        'Planet': planet_code,
                        'DateTime': dt,
                        'Date': dt.date(),
                        'Time': dt.strftime('%H:%M:%S'),
                        'Nakshatra': nakshatra,
                        'Raw_Line': line[:50] + "..." if len(line) > 50 else line
                    })
                    
                    if i < 5:  # Show first 5 entries for debugging
                        st.write(f"✅ Parsed: {planet_code} on {dt.date()} at {dt.time()} in {nakshatra}")
                        
            except Exception as e:
                if i < 5:
                    st.write(f"❌ Failed to parse line {i}: {line[:30]}... Error: {e}")
                continue
    
    df = pd.DataFrame(data)
    return df

def get_market_timing(symbol):
    """Get market timing based on symbol."""
    if symbol.startswith('NSE:') or symbol.startswith('BSE:'):
        return NSE_START, NSE_END
    else:
        return GLOBAL_START, GLOBAL_END

def get_sector_from_symbol(symbol):
    """Extract sector from symbol."""
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
    """Check if planet-nakshatra combination is friendly."""
    if planet not in config['friendly_nakshatras']:
        return False
    
    norm_nakshatra = normalize_nakshatra(nakshatra)
    friendly_list = [normalize_nakshatra(n) for n in config['friendly_nakshatras'][planet]]
    
    return norm_nakshatra in friendly_list

def is_enemy(planet, nakshatra, config):
    """Check if planet-nakshatra combination is enemy."""
    if planet not in config['enemy_nakshatras']:
        return False
    
    norm_nakshatra = normalize_nakshatra(nakshatra)
    enemy_list = [normalize_nakshatra(n) for n in config['enemy_nakshatras'][planet]]
    
    return norm_nakshatra in enemy_list

def get_latest_position_for_date(df_transit, planet, target_date):
    """Get the latest planetary position for a specific date."""
    
    # Get all positions for this planet up to and including the target date
    planet_data = df_transit[
        (df_transit['Planet'] == planet) & 
        (df_transit['Date'] <= target_date)
    ].sort_values('DateTime')
    
    if planet_data.empty:
        return None
    
    # Get the latest position
    latest = planet_data.iloc[-1]
    return latest

def generate_signals_for_date(df_transit, watchlist_symbols, selected_date, config):
    """Generate trading signals for a specific date using latest planetary positions."""
    
    signals = []
    debug_info = []
    
    st.write(f"**🔍 Generating signals for {selected_date}**")
    
    # Show available dates in data
    available_dates = sorted(df_transit['Date'].unique())
    st.write(f"**Available dates in transit data:** {available_dates}")
    
    # Check if we have data for or before the selected date
    valid_dates = [d for d in available_dates if d <= selected_date]
    if not valid_dates:
        return [], f"No transit data available for {selected_date} or earlier dates"
    
    # Group symbols by sector
    sector_symbols = {}
    for symbol in watchlist_symbols:
        sector = get_sector_from_symbol(symbol)
        if sector not in sector_symbols:
            sector_symbols[sector] = []
        sector_symbols[sector].append(symbol)
    
    st.write(f"**Sectors found:** {list(sector_symbols.keys())}")
    
    # Process each sector
    for sector, symbols in sector_symbols.items():
        if sector not in config['sector_planets']:
            continue
            
        st.write(f"**Processing sector {sector} with {len(symbols)} symbols**")
        
        # Get planets for this sector
        planets = config['sector_planets'][sector]
        
        # Process each planet
        for planet in planets:
            # Get latest position for this planet as of the selected date
            latest_position = get_latest_position_for_date(df_transit, planet, selected_date)
            
            if latest_position is None:
                st.write(f"⚠️ No data for {planet} on or before {selected_date}")
                continue
            
            nakshatra = latest_position['Nakshatra']
            position_date = latest_position['Date']
            position_time = latest_position['DateTime'].time()
            
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
                'Position_Date': position_date,
                'Sentiment': sentiment,
                'Sector': sector,
                'Symbols_Count': len(symbols)
            })
            
            st.write(f"  {PLANET_MAPPING.get(planet, planet)} in {nakshatra} = {sentiment}")
            
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
                        'Position_Date': position_date
                    })
    
    return signals, debug_info

# === STREAMLIT UI ===
st.title("📅 Astro-Trading Signals Generator (Date-Specific)")
st.sidebar.header("⚙️ Settings")

# Load configuration
config = load_config()

# Date selector
selected_date = st.sidebar.date_input(
    "Select Date for Signals",
    value=datetime.now().date(),
    min_value=datetime(2020, 1, 1).date(),
    max_value=datetime(2030, 12, 31).date()
)

# Show selected date prominently
st.sidebar.success(f"📅 Selected: {selected_date}")

# File uploaders
st.sidebar.subheader("📁 Upload Files")
watchlist_file = st.sidebar.file_uploader("Upload Watchlist", type="txt")
transit_file = st.sidebar.file_uploader("Upload Transit Data", type="txt")

# Auto-refresh option
auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh every 30 seconds")
if auto_refresh:
    st.rerun()

if watchlist_file and transit_file:
    try:
        # Load watchlist
        watchlist_content = watchlist_file.read().decode('utf-8')
        watchlist_symbols = [line.strip() for line in watchlist_content.split('\n') if line.strip()]
        
        # Load and parse transit data
        transit_content = transit_file.read().decode('utf-8')
        df_transit = parse_transit_data(transit_content)
        
        if df_transit.empty:
            st.error("❌ No valid transit data found!")
            st.stop()
        
        # Display data summary
        st.success(f"✅ Loaded {len(watchlist_symbols)} symbols and {len(df_transit)} transit records")
        
        # Show date range in data
        min_date = df_transit['Date'].min()
        max_date = df_transit['Date'].max()
        st.info(f"📊 Transit data covers: {min_date} to {max_date}")
        
        # Show transit data preview
        with st.expander("📊 Transit Data Preview"):
            st.dataframe(df_transit)
        
        # Generate date-specific signals
        signals, debug_info = generate_signals_for_date(df_transit, watchlist_symbols, selected_date, config)
        
        # Display debug information
        with st.expander("🔍 Debug Information"):
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
                    st.info("No bullish signals")
            
            with col2:
                st.subheader(f"🔴 Bearish Signals ({len(bearish_signals)})")
                if bearish_signals:
                    for signal in bearish_signals:
                        st.error(f"🔴 {signal['Symbol']} | {signal['Entry']}-{signal['Exit']} | {signal['Planet']} in {signal['Nakshatra']}")
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
            st.info("All planetary positions may be neutral or no data available for this date.")
    
    except Exception as e:
        st.error(f"❌ Error processing data: {e}")
        st.write("**Error details:**", str(e))
else:
    st.info("👆 Please upload both watchlist and transit data files to generate signals.")
    
    # Instructions
    st.markdown("""
    ### 📋 Instructions:
    1. **Upload Watchlist**: Text file with one symbol per line
    2. **Upload Transit Data**: Your planetary transit data
    3. **Select Date**: Choose any date to get signals for that specific day
    4. **View Signals**: See bullish/bearish signals for that date
    5. **Send to Telegram**: Share signals instantly
    
    ### 🔧 Why dates were showing same results:
    - System was not properly filtering by date
    - Now uses latest planetary positions as of selected date
    - Each date will show different results based on planetary movements
    """)
