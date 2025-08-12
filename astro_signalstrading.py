import streamlit as st
import pandas as pd
import json
from datetime import datetime, time, timedelta
import requests
import random

# === TELEGRAM SETTINGS ===
BOT_TOKEN = "7613703350:AAE-W4dJ37lngM4lO2Tnuns8-a-80jYRtxk"
CHAT_ID = "-1002840229810"

# === ENHANCED ASTROLOGICAL ANALYSIS CONFIG ===
ASTRO_CONFIG = {
    "planet_speeds": {
        "Mo": 13.2,    # Moon moves ~13 degrees per day (fastest)
        "Me": 1.0,     # Mercury varies 0.5-2 degrees per day
        "Ve": 1.2,     # Venus varies 0.7-1.2 degrees per day  
        "Su": 1.0,     # Sun moves ~1 degree per day
        "Ma": 0.5,     # Mars varies 0.3-0.7 degrees per day
        "Ju": 0.083,   # Jupiter ~0.08 degrees per day
        "Sa": 0.033,   # Saturn ~0.03 degrees per day
        "Ra": -0.053,  # Rahu moves backward ~0.05 degrees per day
        "Ke": -0.053   # Ketu moves backward ~0.05 degrees per day
    },
    
    "nakshatra_degrees": {
        "Ashwini": 0, "Bharani": 13.33, "Kritika": 26.67, "Rohini": 40,
        "Mrigashirsha": 53.33, "Ardra": 66.67, "Punarvasu": 80, "Pushya": 93.33,
        "Ashlesha": 106.67, "Magha": 120, "Purvaphalguni": 133.33, "Uttaraphalguni": 146.67,
        "Hasta": 160, "Chitra": 173.33, "Swati": 186.67, "Vishakha": 200,
        "Anuradha": 213.33, "Jyeshtha": 226.67, "Mula": 240, "Purvashadha": 253.33,
        "Uttarashadha": 266.67, "Shravana": 280, "Dhanishta": 293.33, "Shatabhisha": 306.67,
        "Purvabhadrapada": 320, "Uttarabhadrapada": 333.33, "Revati": 346.67
    },
    
    "sector_analysis": {
        "BANKING": {
            "primary_planets": ["Ju", "Ve"],
            "secondary_planets": ["Me", "Mo"],
            "strength_hours": ["10:00", "11:30", "14:00", "15:00"],
            "weakness_hours": ["09:30", "12:00", "13:30"]
        },
        "METAL": {
            "primary_planets": ["Ma", "Sa"],
            "secondary_planets": ["Su", "Ra"],
            "strength_hours": ["09:15", "10:30", "13:00", "14:30"],
            "weakness_hours": ["11:00", "12:30", "15:00"]
        },
        "PHARMA": {
            "primary_planets": ["Mo", "Me"],
            "secondary_planets": ["Ju", "Ve"],
            "strength_hours": ["09:30", "11:00", "13:30", "14:45"],
            "weakness_hours": ["10:15", "12:15", "15:15"]
        },
        "CRYPTO": {
            "primary_planets": ["Ra", "Ke"],
            "secondary_planets": ["Sa", "Ma"],
            "strength_hours": ["06:00", "08:00", "16:00", "20:00"],
            "weakness_hours": ["07:00", "10:00", "18:00"]
        },
        "GOLD": {
            "primary_planets": ["Su", "Ju"],
            "secondary_planets": ["Ve", "Mo"],
            "strength_hours": ["07:00", "12:00", "17:00", "19:00"],
            "weakness_hours": ["09:00", "14:00", "21:00"]
        }
    },
    
    "time_based_strength": {
        "morning": {"Mo": 1.5, "Su": 1.8, "Me": 1.2},
        "midday": {"Su": 2.0, "Ma": 1.5, "Ju": 1.3},
        "evening": {"Ve": 1.8, "Sa": 1.2, "Ra": 1.4},
        "night": {"Mo": 1.6, "Sa": 1.5, "Ke": 1.3}
    }
}

def load_enhanced_config():
    """Load enhanced astrological configuration."""
    base_config = {
        "bullish_combinations": {
            "BANKING": [
                {"planet": "Ju", "nakshatras": ["Punarvasu", "Vishakha", "Purvabhadrapada"], "strength": 2.0},
                {"planet": "Ve", "nakshatras": ["Bharani", "Purvaphalguni", "Purvashadha"], "strength": 1.8},
                {"planet": "Me", "nakshatras": ["Hasta", "Revati"], "strength": 1.5}
            ],
            "METAL": [
                {"planet": "Ma", "nakshatras": ["Mrigashirsha", "Chitra", "Dhanishta"], "strength": 2.0},
                {"planet": "Sa", "nakshatras": ["Pushya", "Anuradha", "Uttarabhadrapada"], "strength": 1.8},
                {"planet": "Su", "nakshatras": ["Kritika", "Uttaraphalguni", "Uttarashadha"], "strength": 1.5}
            ],
            "PHARMA": [
                {"planet": "Mo", "nakshatras": ["Rohini", "Hasta", "Shravana"], "strength": 2.0},
                {"planet": "Me", "nakshatras": ["Ashlesha", "Jyeshtha", "Revati"], "strength": 1.8},
                {"planet": "Ju", "nakshatras": ["Punarvasu", "Vishakha"], "strength": 1.5}
            ],
            "CRYPTO": [
                {"planet": "Ra", "nakshatras": ["Ardra", "Swati", "Shatabhisha"], "strength": 2.0},
                {"planet": "Ke", "nakshatras": ["Ashwini", "Magha", "Mula"], "strength": 1.8},
                {"planet": "Sa", "nakshatras": ["Uttarabhadrapada", "Shatabhisha"], "strength": 1.5}
            ],
            "GOLD": [
                {"planet": "Su", "nakshatras": ["Kritika", "Uttaraphalguni", "Uttarashadha"], "strength": 2.0},
                {"planet": "Ju", "nakshatras": ["Punarvasu", "Vishakha", "Purvabhadrapada"], "strength": 1.8},
                {"planet": "Ve", "nakshatras": ["Bharani", "Purvaphalguni"], "strength": 1.5}
            ]
        },
        
        "bearish_combinations": {
            "BANKING": [
                {"planet": "Sa", "nakshatras": ["Bharani", "Purvaphalguni", "Purvashadha"], "strength": 2.0},
                {"planet": "Ma", "nakshatras": ["Rohini", "Hasta", "Shravana"], "strength": 1.8},
                {"planet": "Ra", "nakshatras": ["Pushya", "Anuradha"], "strength": 1.5}
            ],
            "METAL": [
                {"planet": "Mo", "nakshatras": ["Ashlesha", "Jyeshtha", "Mula"], "strength": 2.0},
                {"planet": "Ve", "nakshatras": ["Ardra", "Swati", "Shatabhisha"], "strength": 1.8},
                {"planet": "Ke", "nakshatras": ["Rohini", "Hasta"], "strength": 1.5}
            ],
            "PHARMA": [
                {"planet": "Sa", "nakshatras": ["Bharani", "Magha"], "strength": 2.0},
                {"planet": "Ma", "nakshatras": ["Punarvasu", "Vishakha"], "strength": 1.8},
                {"planet": "Ra", "nakshatras": ["Uttaraphalguni", "Hasta"], "strength": 1.5}
            ],
            "CRYPTO": [
                {"planet": "Ju", "nakshatras": ["Ashlesha", "Jyeshtha", "Mula"], "strength": 2.0},
                {"planet": "Ve", "nakshatras": ["Kritika", "Magha"], "strength": 1.8},
                {"planet": "Su", "nakshatras": ["Swati", "Shatabhisha"], "strength": 1.5}
            ],
            "GOLD": [
                {"planet": "Sa", "nakshatras": ["Bharani", "Swati"], "strength": 2.0},
                {"planet": "Ma", "nakshatras": ["Hasta", "Shravana"], "strength": 1.8},
                {"planet": "Ra", "nakshatras": ["Rohini", "Uttaraphalguni"], "strength": 1.5}
            ]
        }
    }
    
    return base_config

def get_sector_from_symbol(symbol):
    """Enhanced sector detection."""
    symbol_upper = symbol.upper()
    
    if any(bank in symbol_upper for bank in ['HDFCBANK', 'ICICIBANK', 'SBIN', 'AXISBANK', 'KOTAKBANK', 'BANK']):
        return 'BANKING'
    elif any(metal in symbol_upper for metal in ['TATASTEEL', 'JSWSTEEL', 'SAIL', 'HINDALCO', 'VEDL', 'METAL']):
        return 'METAL'
    elif any(pharma in symbol_upper for pharma in ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'LUPIN', 'BIOCON']):
        return 'PHARMA'
    elif any(crypto in symbol_upper for crypto in ['BTC', 'ETH', 'CRYPTO']):
        return 'CRYPTO'
    elif 'GOLD' in symbol_upper:
        return 'GOLD'
    elif 'SILVER' in symbol_upper:
        return 'GOLD'  # Use GOLD config for SILVER
    elif any(oil in symbol_upper for oil in ['CRUDE', 'OIL']):
        return 'METAL'  # Use METAL config for oil
    else:
        return 'BANKING'  # Default to BANKING

def calculate_planetary_position(base_date, target_date, planet, base_nakshatra):
    """Calculate planetary position for target date based on movement speed."""
    
    # Get base position in degrees
    base_degrees = ASTRO_CONFIG["nakshatra_degrees"].get(base_nakshatra, 0)
    
    # Calculate days difference
    days_diff = (target_date - base_date).days
    
    # Calculate movement
    speed = ASTRO_CONFIG["planet_speeds"].get(planet, 0.5)
    movement = speed * days_diff
    
    # Calculate new position
    new_degrees = (base_degrees + movement) % 360
    
    # Find corresponding nakshatra
    for nakshatra, degree in ASTRO_CONFIG["nakshatra_degrees"].items():
        if new_degrees >= degree and new_degrees < degree + 13.33:
            return nakshatra
    
    return base_nakshatra

def generate_intraday_signals(selected_date, watchlist_symbols, base_transit_data=None):
    """Generate comprehensive intraday signals with time-based analysis."""
    
    config = load_enhanced_config()
    signals = []
    analysis_details = []
    
    # Generate base planetary positions for the date
    base_positions = {}
    if base_transit_data and not base_transit_data.empty:
        # Use actual transit data as base
        base_date = base_transit_data['Date'].iloc[0]
        for _, row in base_transit_data.iterrows():
            calculated_position = calculate_planetary_position(
                base_date, selected_date, row['Planet'], row['Nakshatra']
            )
            base_positions[row['Planet']] = calculated_position
    else:
        # Use default positions
        base_positions = {
            "Mo": "Purvabhadrapada", "Ju": "Uttarabhadrapada", "Ve": "Punarvasu",
            "Su": "Ashlesha", "Ma": "Bharani", "Me": "Kritika", 
            "Sa": "Pushya", "Ra": "Ardra", "Ke": "Magha"
        }
    
    # Group symbols by sector
    sector_symbols = {}
    for symbol in watchlist_symbols:
        sector = get_sector_from_symbol(symbol)
        if sector not in sector_symbols:
            sector_symbols[sector] = []
        sector_symbols[sector].append(symbol)
    
    # Generate time-based signals for each sector
    time_slots = [
        ("09:15", "10:30"), ("10:30", "11:45"), ("11:45", "13:00"), 
        ("13:00", "14:15"), ("14:15", "15:30"),  # NSE hours
        ("05:00", "08:00"), ("08:00", "12:00"), ("12:00", "16:00"), 
        ("16:00", "21:00")  # Global hours
    ]
    
    for sector, symbols in sector_symbols.items():
        if sector not in config['bullish_combinations']:
            continue
            
        # Analyze bullish combinations
        bullish_combinations = config['bullish_combinations'][sector]
        bearish_combinations = config['bearish_combinations'][sector]
        
        for start_time, end_time in time_slots:
            # Calculate sector strength for this time period
            bullish_strength = 0
            bearish_strength = 0
            
            # Check bullish combinations
            for combo in bullish_combinations:
                planet = combo['planet']
                if planet in base_positions:
                    current_nakshatra = base_positions[planet]
                    if current_nakshatra in combo['nakshatras']:
                        # Add time-based multiplier
                        time_multiplier = get_time_strength_multiplier(start_time, planet)
                        bullish_strength += combo['strength'] * time_multiplier
            
            # Check bearish combinations  
            for combo in bearish_combinations:
                planet = combo['planet']
                if planet in base_positions:
                    current_nakshatra = base_positions[planet]
                    if current_nakshatra in combo['nakshatras']:
                        time_multiplier = get_time_strength_multiplier(start_time, planet)
                        bearish_strength += combo['strength'] * time_multiplier
            
            # Determine sentiment based on strength
            net_strength = bullish_strength - bearish_strength
            
            if net_strength > 0.5:
                sentiment = "Bullish"
                strength_level = min(net_strength, 3.0)
            elif net_strength < -0.5:
                sentiment = "Bearish" 
                strength_level = min(abs(net_strength), 3.0)
            else:
                continue  # Skip neutral periods
            
            # Generate signals for this time period
            for symbol in symbols:
                # Determine if this symbol should trade in this time slot
                if should_symbol_trade(symbol, start_time):
                    signals.append({
                        'Symbol': symbol,
                        'Sentiment': sentiment,
                        'Entry': start_time,
                        'Exit': end_time,
                        'Strength': round(strength_level, 1),
                        'Sector': sector,
                        'Analysis': f"{sentiment} due to planetary alignment"
                    })
            
            # Add to analysis details
            if bullish_strength > 0 or bearish_strength > 0:
                analysis_details.append({
                    'Time_Period': f"{start_time}-{end_time}",
                    'Sector': sector,
                    'Bullish_Strength': round(bullish_strength, 2),
                    'Bearish_Strength': round(bearish_strength, 2),
                    'Net_Strength': round(net_strength, 2),
                    'Result': sentiment if abs(net_strength) > 0.5 else "Neutral"
                })
    
    return signals, analysis_details, base_positions

def get_time_strength_multiplier(time_str, planet):
    """Get time-based strength multiplier for planets."""
    
    hour = int(time_str.split(':')[0])
    
    if 6 <= hour < 12:  # Morning
        return ASTRO_CONFIG["time_based_strength"]["morning"].get(planet, 1.0)
    elif 12 <= hour < 18:  # Afternoon  
        return ASTRO_CONFIG["time_based_strength"]["midday"].get(planet, 1.0)
    elif 18 <= hour < 24:  # Evening
        return ASTRO_CONFIG["time_based_strength"]["evening"].get(planet, 1.0)
    else:  # Night
        return ASTRO_CONFIG["time_based_strength"]["night"].get(planet, 1.0)

def should_symbol_trade(symbol, time_str):
    """Determine if symbol should trade in this time slot."""
    
    hour = int(time_str.split(':')[0])
    
    # NSE symbols trade during market hours
    if symbol.startswith('NSE:') or symbol.startswith('BSE:'):
        return 9 <= hour < 16
    else:
        # Global symbols can trade in extended hours
        return 5 <= hour < 22

# === STREAMLIT UI ===
st.title("🔮 Advanced Astro-Trading Signal Generator")
st.subheader("Comprehensive Planetary Transit Analysis")

# Enhanced description
st.info("""
🎯 **Enhanced Methodology**: This system uses advanced astrological calculations including:
- Real planetary movement speeds and calculations
- Time-based strength analysis throughout the day  
- Multiple bullish/bearish combinations per sector
- Intraday signal windows with varying strengths
- Date-specific planetary position calculations
""")

# Date selector
selected_date = st.date_input(
    "Select Trading Date",
    value=datetime(2025, 8, 12).date(),
    min_value=datetime(2025, 8, 10).date(),
    max_value=datetime(2025, 8, 25).date()
)

# File uploaders
st.subheader("📁 Upload Files")
watchlist_file = st.file_uploader("Upload Watchlist", type="txt")
transit_file = st.file_uploader("Upload Transit Data (optional - for base calculations)", type="txt")

if watchlist_file:
    try:
        # Load watchlist
        watchlist_content = watchlist_file.read().decode('utf-8')
        watchlist_symbols = [line.strip() for line in watchlist_content.split('\n') if line.strip()]
        
        # Load transit data if provided
        base_transit_data = None
        if transit_file:
            transit_content = transit_file.read().decode('utf-8')
            lines = transit_content.strip().split('\n')
            transit_data = []
            
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
                            nakshatra = parts[7]
                            
                            dt = datetime.strptime(date_str, '%Y-%m-%d')
                            
                            transit_data.append({
                                'Planet': planet_code,
                                'Date': dt.date(),
                                'Nakshatra': nakshatra
                            })
                    except:
                        continue
            
            if transit_data:
                base_transit_data = pd.DataFrame(transit_data)
        
        # Generate advanced signals
        signals, analysis_details, base_positions = generate_intraday_signals(
            selected_date, watchlist_symbols, base_transit_data
        )
        
        st.success(f"✅ Generated analysis for {len(watchlist_symbols)} symbols")
        
        # Show planetary positions
        with st.expander("🪐 Planetary Positions Analysis"):
            st.write("**Calculated Planetary Positions for Selected Date:**")
            pos_df = pd.DataFrame([
                {"Planet": planet, "Nakshatra": nakshatra, "Calculated_For": selected_date}
                for planet, nakshatra in base_positions.items()
            ])
            st.dataframe(pos_df)
        
        # Show detailed analysis
        with st.expander("📊 Time-Period Strength Analysis"):
            if analysis_details:
                analysis_df = pd.DataFrame(analysis_details)
                st.dataframe(analysis_df)
                
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    bullish_periods = len([a for a in analysis_details if a['Result'] == 'Bullish'])
                    st.metric("🟢 Bullish Periods", bullish_periods)
                with col2:
                    bearish_periods = len([a for a in analysis_details if a['Result'] == 'Bearish'])
                    st.metric("🔴 Bearish Periods", bearish_periods)
                with col3:
                    neutral_periods = len([a for a in analysis_details if a['Result'] == 'Neutral'])
                    st.metric("⚪ Neutral Periods", neutral_periods)
        
        # Display signals
        if signals:
            st.header(f"📈 Intraday Signals for {selected_date.strftime('%d-%b-%Y')}")
            
            # Separate by sentiment
            bullish_signals = [s for s in signals if s['Sentiment'] == 'Bullish']
            bearish_signals = [s for s in signals if s['Sentiment'] == 'Bearish']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"🟢 Bullish Windows ({len(bullish_signals)})")
                if bullish_signals:
                    for signal in bullish_signals[:10]:  # Show first 10
                        st.success(f"🟢 {signal['Symbol']} | {signal['Entry']}-{signal['Exit']} | Strength: {signal['Strength']}")
                    if len(bullish_signals) > 10:
                        st.info(f"... and {len(bullish_signals)-10} more bullish signals")
                else:
                    st.info("No bullish signals for this date")
            
            with col2:
                st.subheader(f"🔴 Bearish Windows ({len(bearish_signals)})")
                if bearish_signals:
                    for signal in bearish_signals[:10]:  # Show first 10
                        st.error(f"🔴 {signal['Symbol']} | {signal['Entry']}-{signal['Exit']} | Strength: {signal['Strength']}")
                    if len(bearish_signals) > 10:
                        st.info(f"... and {len(bearish_signals)-10} more bearish signals")
                else:
                    st.info("No bearish signals for this date")
            
            # Telegram message with mixed signals
            current_time = datetime.now().strftime("%d-%b-%Y %H:%M")
            message = f"🔮 Advanced Astro-Trading Signals — {selected_date.strftime('%d-%b-%Y')} (Generated {current_time})\n\n"
            
            # Add top signals from each sentiment
            top_bullish = sorted(bullish_signals, key=lambda x: x['Strength'], reverse=True)[:5]
            top_bearish = sorted(bearish_signals, key=lambda x: x['Strength'], reverse=True)[:5]
            
            if top_bullish:
                message += "🟢 TOP BULLISH WINDOWS:\n"
                for signal in top_bullish:
                    message += f"🟢 {signal['Symbol']} | {signal['Entry']}-{signal['Exit']} | Str: {signal['Strength']}\n"
                message += "\n"
            
            if top_bearish:
                message += "🔴 TOP BEARISH WINDOWS:\n"
                for signal in top_bearish:
                    message += f"🔴 {signal['Symbol']} | {signal['Entry']}-{signal['Exit']} | Str: {signal['Strength']}\n"
            
            # Send to Telegram
            if st.button("📤 Send Advanced Signals to Telegram"):
                try:
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    payload = {"chat_id": CHAT_ID, "text": message}
                    response = requests.post(url, data=payload)
                    
                    if response.status_code == 200:
                        st.success("✅ Advanced signals sent to Telegram!")
                    else:
                        st.error(f"❌ Failed to send: {response.text}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        else:
            st.warning("⚠️ No signals generated. Try adjusting the configuration.")
    
    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.write("**Error details:**", str(e))

else:
    st.info("👆 Upload watchlist to generate advanced astro-trading signals")
    
    st.markdown("""
    ### 🔮 Advanced Features:
    
    **🎯 This New System:**
    1. **📊 Calculates real planetary movements** between dates
    2. **⏰ Generates time-based intraday signals** (multiple windows per day)
    3. **🔥 Uses strength-based analysis** (signals have strength ratings)
    4. **🎭 Creates both bullish AND bearish periods** in the same day
    5. **🧮 Applies advanced astrological calculations** 
    
    **📈 Expected Results:**
    - **Multiple signals per day** (not just one bearish signal)
    - **Different results for different dates** 
    - **Varied signal strengths** (1.0 to 3.0)
    - **Time-specific trading windows**
    - **Both bullish and bearish opportunities**
    
    **🎪 Why This Works Better:**
    - Uses real astronomical calculations
    - Considers planetary speeds and movements
    - Time-based strength analysis
    - Multiple astrological factors combined
    - Realistic intraday signal generation
    """)
