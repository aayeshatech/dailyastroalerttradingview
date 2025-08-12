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

# === DEFAULT CONFIG (if config.json is missing) ===
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
        "Mo": ["Rohini", "Hasta", "Shravana", "Mrigashirsha", "Chitra"],
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

# === PLANET MAPPING ===
PLANET_MAPPING = {
    "Mo": "Moon",
    "Ma": "Mars", 
    "Me": "Mercury",
    "Ju": "Jupiter",
    "Ve": "Venus",
    "Sa": "Saturn",
    "Ra": "Rahu",
    "Ke": "Ketu",
    "Su": "Sun"
}

def load_config():
    """Load configuration from file or use default."""
    try:
        with open("config.json") as f:
            config = json.load(f)
        return config
    except:
        st.warning("⚠️ config.json not found. Using default configuration.")
        return DEFAULT_CONFIG

def normalize_nakshatra(name):
    """Normalize nakshatra names for matching."""
    # Common variations mapping
    nakshatra_variations = {
        "purvabhadrapada": ["purvabhadrapada", "purva bhadrapada", "p.bhadrapada"],
        "uttarabhadrapada": ["uttarabhadrapada", "uttara bhadrapada", "u.bhadrapada"],
        "purvashadha": ["purvashadha", "purva ashadha", "p.ashadha"],
        "uttarashadha": ["uttarashadha", "uttara ashadha", "u.ashadha"],
        "purvaphalguni": ["purvaphalguni", "purva phalguni", "p.phalguni"],
        "uttaraphalguni": ["uttaraphalguni", "uttara phalguni", "u.phalguni"],
        "ashlesha": ["ashlesha", "aslesha"],
        "mrigashirsha": ["mrigashirsha", "mrigasira", "mrugasira"],
        "ardra": ["ardra", "arudra"],
        "punarvasu": ["punarvasu", "punarpoosam"],
        "ashwini": ["ashwini", "aswini"],
        "kritika": ["kritika", "krittika"],
        "bharani": ["bharani"],
        "rohini": ["rohini"],
        "pushya": ["pushya", "poosam"],
        "magha": ["magha"],
        "chitra": ["chitra", "chithra"],
        "swati": ["swati"],
        "vishakha": ["vishakha", "visakha"],
        "anuradha": ["anuradha"],
        "jyeshtha": ["jyeshtha", "jyesta"],
        "mula": ["mula", "moola"],
        "dhanishta": ["dhanishta", "dhanishtha"],
        "shatabhisha": ["shatabhisha", "satabhisha"],
        "revati": ["revati"],
        "hasta": ["hasta"],
        "shravana": ["shravana", "sravana"]
    }
    
    normalized = name.strip().lower().replace(" ", "").replace("-", "")
    
    # Find the standard name
    for standard, variations in nakshatra_variations.items():
        if normalized in [v.replace(" ", "").replace("-", "") for v in variations]:
            return standard
    
    return normalized

def parse_transit_data(transit_text):
    """Parse the transit data format."""
    lines = transit_text.strip().split('\n')
    data = []
    
    for line in lines[1:]:  # Skip header
        if line.strip():
            parts = line.split('\t')
            if len(parts) >= 9:
                try:
                    planet_code = parts[0].strip('*')
                    date_time = parts[1] + ' ' + parts[2]
                    nakshatra = parts[7]
                    
                    # Convert datetime
                    dt = datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')
                    
                    data.append({
                        'Planet': planet_code,
                        'DateTime': dt,
                        'Time': dt.strftime('%H:%M:%S'),
                        'Nakshatra': nakshatra,
                        'Date': dt.date()
                    })
                except:
                    continue
    
    return pd.DataFrame(data)

def get_market_timing(symbol):
    """Get market timing based on symbol."""
    if symbol.startswith('NSE:') or symbol.startswith('BSE:'):
        return NSE_START, NSE_END
    else:
        return GLOBAL_START, GLOBAL_END

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

def get_sector_from_symbol(symbol):
    """Extract sector from symbol."""
    symbol_upper = symbol.upper()
    
    # Banking
    if any(bank in symbol_upper for bank in ['HDFCBANK', 'ICICIBANK', 'SBIN', 'AXISBANK', 'KOTAKBANK', 'BANK']):
        return 'BANKING'
    # Metal/Steel
    elif any(metal in symbol_upper for metal in ['TATASTEEL', 'JSWSTEEL', 'SAIL', 'HINDALCO', 'VEDL', 'METAL']):
        return 'METAL'
    # IT
    elif any(it in symbol_upper for it in ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM']):
        return 'IT'
    # Auto
    elif any(auto in symbol_upper for auto in ['MARUTI', 'TATAMOTORS', 'BAJAJ', 'HEROMOTOCO', 'EICHER']):
        return 'AUTO'
    # Pharma
    elif any(pharma in symbol_upper for pharma in ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'LUPIN', 'BIOCON']):
        return 'PHARMA'
    # Oil & Gas
    elif any(oil in symbol_upper for oil in ['CRUDE', 'OIL', 'ONGC', 'BPCL', 'HINDPETRO']):
        return 'OIL'
    # Gold
    elif 'GOLD' in symbol_upper:
        return 'GOLD'
    # Silver
    elif 'SILVER' in symbol_upper:
        return 'SILVER'
    # Crypto
    elif any(crypto in symbol_upper for crypto in ['BTC', 'ETH', 'CRYPTO']):
        return 'CRYPTO'
    # FMCG
    elif any(fmcg in symbol_upper for fmcg in ['BRITANNIA', 'HINDUNILVR', 'NESTLEIND', 'DABUR', 'MARICO']):
        return 'FMCG'
    else:
        return 'GENERAL'

def generate_signals(df_transit, watchlist_symbols, selected_date, config):
    """Generate trading signals for the selected date."""
    
    # Filter transit data for selected date
    date_transits = df_transit[df_transit['Date'] == selected_date].copy()
    
    if date_transits.empty:
        return [], f"No transit data found for {selected_date}"
    
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
            
        # Get planets for this sector
        planets = config['sector_planets'][sector]
        
        # Process each planet
        for planet in planets:
            planet_transits = date_transits[date_transits['Planet'] == planet].sort_values('DateTime')
            
            if planet_transits.empty:
                continue
            
            # Analyze each transit
            current_sentiment = None
            last_time = None
            
            for _, transit in planet_transits.iterrows():
                nakshatra = transit['Nakshatra']
                transit_time = transit['DateTime'].time()
                
                # Determine sentiment
                sentiment = None
                if is_friendly(planet, nakshatra, config):
                    sentiment = 'Bullish'
                elif is_enemy(planet, nakshatra, config):
                    sentiment = 'Bearish'
                
                debug_info.append({
                    'Planet': PLANET_MAPPING.get(planet, planet),
                    'Nakshatra': nakshatra,
                    'Time': transit['Time'],
                    'Sentiment': sentiment or 'Neutral',
                    'Sector': sector
                })
                
                if sentiment and sentiment != current_sentiment:
                    # End previous sentiment period
                    if current_sentiment and last_time:
                        for symbol in symbols:
                            start_time, end_time = get_market_timing(symbol)
                            if start_time <= last_time <= end_time:
                                signals.append({
                                    'Symbol': symbol,
                                    'Sentiment': current_sentiment,
                                    'Entry': last_time.strftime('%H:%M'),
                                    'Exit': transit_time.strftime('%H:%M'),
                                    'Planet': PLANET_MAPPING.get(planet, planet),
                                    'Nakshatra': nakshatra
                                })
                    
                    current_sentiment = sentiment
                    last_time = transit_time
            
            # Close final period at market end
            if current_sentiment and last_time:
                for symbol in symbols:
                    start_time, end_time = get_market_timing(symbol)
                    if start_time <= last_time <= end_time:
                        signals.append({
                            'Symbol': symbol,
                            'Sentiment': current_sentiment,
                            'Entry': last_time.strftime('%H:%M'),
                            'Exit': end_time.strftime('%H:%M'),
                            'Planet': PLANET_MAPPING.get(planet, planet),
                            'Nakshatra': 'Market Close'
                        })
    
    return signals, debug_info

# === STREAMLIT UI ===
st.title("📅 Astro-Trading Signals Generator")
st.sidebar.header("⚙️ Settings")

# Load configuration
config = load_config()

# Date selector
selected_date = st.sidebar.date_input(
    "Select Date",
    value=datetime.now().date(),
    min_value=datetime(2020, 1, 1).date(),
    max_value=datetime(2030, 12, 31).date()
)

# File uploaders
st.sidebar.subheader("📁 Upload Files")
watchlist_file = st.sidebar.file_uploader("Upload Watchlist", type="txt")
transit_file = st.sidebar.file_uploader("Upload Transit Data", type="txt")

# Configuration display
with st.expander("⚙️ View Configuration"):
    st.json(config)

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
        
        # Display data info
        st.success(f"✅ Loaded {len(watchlist_symbols)} symbols and {len(df_transit)} transit records")
        
        # Show transit data preview
        with st.expander("📊 Transit Data Preview"):
            st.dataframe(df_transit.head(10))
        
        # Generate signals
        signals, debug_info = generate_signals(df_transit, watchlist_symbols, selected_date, config)
        
        # Display debug information
        with st.expander("🔍 Debug Information"):
            if debug_info:
                debug_df = pd.DataFrame(debug_info)
                st.dataframe(debug_df)
                
                # Signal counts
                col1, col2, col3 = st.columns(3)
                with col1:
                    bullish_count = len([d for d in debug_info if d['Sentiment'] == 'Bullish'])
                    st.metric("🟢 Bullish Transits", bullish_count)
                with col2:
                    bearish_count = len([d for d in debug_info if d['Sentiment'] == 'Bearish'])
                    st.metric("🔴 Bearish Transits", bearish_count)
                with col3:
                    neutral_count = len([d for d in debug_info if d['Sentiment'] == 'Neutral'])
                    st.metric("⚪ Neutral Transits", neutral_count)
        
        # Display signals
        if signals:
            st.header(f"📈 Trading Signals for {selected_date.strftime('%d-%b-%Y')}")
            
            # Separate bullish and bearish signals
            bullish_signals = [s for s in signals if s['Sentiment'] == 'Bullish']
            bearish_signals = [s for s in signals if s['Sentiment'] == 'Bearish']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🟢 Bullish Signals")
                if bullish_signals:
                    for signal in bullish_signals:
                        st.success(f"🟢 {signal['Symbol']} | {signal['Entry']}-{signal['Exit']} | {signal['Planet']}")
                else:
                    st.info("No bullish signals found")
            
            with col2:
                st.subheader("🔴 Bearish Signals")
                if bearish_signals:
                    for signal in bearish_signals:
                        st.error(f"🔴 {signal['Symbol']} | {signal['Entry']}-{signal['Exit']} | {signal['Planet']}")
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
            st.info("This could mean all transits are neutral or outside market hours.")
    
    except Exception as e:
        st.error(f"❌ Error processing data: {e}")
        st.write("**Error details:**", str(e))
else:
    st.info("👆 Please upload both watchlist and transit data files to generate signals.")
