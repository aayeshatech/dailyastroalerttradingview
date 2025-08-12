import streamlit as st
import pandas as pd
from datetime import datetime, time
import requests

# === TELEGRAM SETTINGS ===
BOT_TOKEN = "7613703350:AAE-W4dJ37lngM4lO2Tnuns8-a-80jYRtxk"
CHAT_ID = "-1002840229810"

# === MAIN APP ===
st.set_page_config(page_title="Astro Trading", page_icon="🔮", layout="wide")

st.title("🔮 Professional Astro-Trading Signal Generator")
st.markdown("---")

# === DATE SELECTION ===
col1, col2 = st.columns([1, 2])

with col1:
    selected_date = st.date_input(
        "📅 Select Trading Date",
        value=datetime.now().date(),
        help="Different dates will generate completely different signals"
    )

with col2:
    # Calculate pattern based on date
    day_of_year = selected_date.timetuple().tm_yday
    pattern = day_of_year % 5
    
    pattern_names = {
        0: "🏦 Banking Bullish Day",
        1: "⚙️ Metal & Industrial Bullish Day", 
        2: "💊 Pharma & Healthcare Bullish Day",
        3: "💰 Crypto & Gold Bullish Day",
        4: "🔄 Mixed Sector Day"
    }
    
    st.info(f"**Today's Pattern:** {pattern_names[pattern]}")
    st.metric("Pattern Number", f"#{pattern}")

# === FILE UPLOAD ===
st.subheader("📁 Upload Your Watchlist")
watchlist_file = st.file_uploader(
    "Choose your watchlist file", 
    type=['txt', 'csv'],
    help="Upload a text file with one symbol per line (e.g., NSE:HDFCBANK)"
)

if watchlist_file:
    try:
        # Read watchlist properly
        if watchlist_file.type == "text/plain":
            content = watchlist_file.read().decode('utf-8')
            symbols = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
        else:
            df = pd.read_csv(watchlist_file)
            symbols = df.iloc[:, 0].astype(str).tolist()
        
        # Clean symbols
        symbols = [s for s in symbols if s and len(s) > 3]
        
        st.success(f"✅ Successfully loaded **{len(symbols)}** symbols")
        
        # Show first few symbols
        with st.expander("👀 Preview Loaded Symbols"):
            for i, symbol in enumerate(symbols[:10]):
                st.write(f"{i+1}. {symbol}")
            if len(symbols) > 10:
                st.write(f"... and {len(symbols)-10} more symbols")
        
        # === GENERATE SIGNALS ===
        st.subheader("🎯 Generated Trading Signals")
        
        # Define sector patterns for each day
        if pattern == 0:  # Banking Bullish Day
            bullish_keywords = ['HDFCBANK', 'ICICIBANK', 'SBIN', 'AXISBANK', 'KOTAKBANK', 'BANK', 'FINANCE']
            bearish_keywords = ['TATASTEEL', 'JSWSTEEL', 'SAIL', 'HINDALCO', 'VEDL', 'METAL', 'STEEL']
            neutral_keywords = ['GOLD', 'SILVER', 'CRYPTO']
            
        elif pattern == 1:  # Metal Bullish Day
            bullish_keywords = ['TATASTEEL', 'JSWSTEEL', 'SAIL', 'HINDALCO', 'VEDL', 'METAL', 'STEEL', 'COPPER', 'ALUMINIUM']
            bearish_keywords = ['HDFCBANK', 'ICICIBANK', 'SBIN', 'BANK', 'FINANCE']
            neutral_keywords = ['PHARMA', 'BIOCON']
            
        elif pattern == 2:  # Pharma Bullish Day
            bullish_keywords = ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'LUPIN', 'BIOCON', 'PHARMA', 'DRUG', 'HEALTHCARE']
            bearish_keywords = ['TATASTEEL', 'JSWSTEEL', 'METAL', 'STEEL']
            neutral_keywords = ['BANK', 'FINANCE']
            
        elif pattern == 3:  # Crypto & Gold Bullish Day
            bullish_keywords = ['BTC', 'ETH', 'CRYPTO', 'GOLD', 'SILVER']
            bearish_keywords = ['HDFCBANK', 'SBIN', 'BANK', 'TATASTEEL', 'METAL']
            neutral_keywords = ['PHARMA', 'DRUG']
            
        else:  # Mixed Day
            bullish_keywords = ['GOLD', 'SILVER', 'PHARMA', 'HEALTHCARE']
            bearish_keywords = ['CRUDE', 'OIL', 'ENERGY']
            neutral_keywords = ['BANK', 'METAL']
        
        # Generate signals
        bullish_signals = []
        bearish_signals = []
        neutral_signals = []
        
        for symbol in symbols:
            symbol_upper = symbol.upper()
            
            # Determine sentiment based on keywords
            sentiment = "Neutral"
            reason = "No specific sector alignment"
            
            # Check for bullish keywords
            for keyword in bullish_keywords:
                if keyword in symbol_upper:
                    sentiment = "Bullish"
                    reason = f"{keyword} sector favorable today"
                    break
            
            # Check for bearish keywords
            if sentiment == "Neutral":
                for keyword in bearish_keywords:
                    if keyword in symbol_upper:
                        sentiment = "Bearish" 
                        reason = f"{keyword} sector unfavorable today"
                        break
            
            # Determine market timing
            if symbol.startswith(('NSE:', 'BSE:')):
                entry_time = "09:15"
                exit_time = "15:30"
                market = "Indian"
            else:
                entry_time = "05:00"
                exit_time = "21:00"
                market = "Global"
            
            # Create signal
            signal = {
                'Symbol': symbol,
                'Sentiment': sentiment,
                'Entry': entry_time,
                'Exit': exit_time,
                'Market': market,
                'Reason': reason,
                'Pattern': pattern
            }
            
            if sentiment == "Bullish":
                bullish_signals.append(signal)
            elif sentiment == "Bearish":
                bearish_signals.append(signal)
            else:
                neutral_signals.append(signal)
        
        # === DISPLAY RESULTS ===
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🟢 Bullish Signals", len(bullish_signals))
        with col2:
            st.metric("🔴 Bearish Signals", len(bearish_signals))
        with col3:
            st.metric("⚪ Neutral Signals", len(neutral_signals))
        
        # Show signals in tabs
        tab1, tab2, tab3 = st.tabs(["🟢 Bullish Signals", "🔴 Bearish Signals", "⚪ Neutral Signals"])
        
        with tab1:
            if bullish_signals:
                st.write(f"**{len(bullish_signals)} Bullish Trading Opportunities:**")
                for i, signal in enumerate(bullish_signals, 1):
                    st.success(f"🟢 **{i}.** {signal['Symbol']} → Bullish | {signal['Entry']}-{signal['Exit']} | {signal['Market']} Market | *{signal['Reason']}*")
            else:
                st.info("No bullish signals for today's pattern")
        
        with tab2:
            if bearish_signals:
                st.write(f"**{len(bearish_signals)} Bearish Trading Opportunities:**")
                for i, signal in enumerate(bearish_signals, 1):
                    st.error(f"🔴 **{i}.** {signal['Symbol']} → Bearish | {signal['Entry']}-{signal['Exit']} | {signal['Market']} Market | *{signal['Reason']}*")
            else:
                st.info("No bearish signals for today's pattern")
        
        with tab3:
            if neutral_signals:
                st.write(f"**{len(neutral_signals)} Neutral Signals:**")
                for i, signal in enumerate(neutral_signals[:5], 1):  # Show first 5
                    st.warning(f"⚪ **{i}.** {signal['Symbol']} → Neutral | {signal['Entry']}-{signal['Exit']} | {signal['Market']} Market")
                if len(neutral_signals) > 5:
                    st.info(f"... and {len(neutral_signals)-5} more neutral signals")
            else:
                st.info("No neutral signals")
        
        # === TELEGRAM INTEGRATION ===
        st.subheader("📱 Send to Telegram")
        
        # Create telegram message
        current_time = datetime.now().strftime("%d-%b-%Y %H:%M")
        message = f"🔮 Astro-Trading Signals — {selected_date.strftime('%d-%b-%Y')} (Generated {current_time})\n"
        message += f"📊 Pattern: {pattern_names[pattern]}\n\n"
        
        if bullish_signals:
            message += f"🟢 BULLISH SIGNALS ({len(bullish_signals)}):\n"
            for signal in bullish_signals[:8]:  # Top 8
                message += f"🟢 {signal['Symbol']} → Bullish | {signal['Entry']}-{signal['Exit']}\n"
            if len(bullish_signals) > 8:
                message += f"... and {len(bullish_signals)-8} more bullish signals\n"
            message += "\n"
        
        if bearish_signals:
            message += f"🔴 BEARISH SIGNALS ({len(bearish_signals)}):\n"
            for signal in bearish_signals[:8]:  # Top 8
                message += f"🔴 {signal['Symbol']} → Bearish | {signal['Entry']}-{signal['Exit']}\n"
            if len(bearish_signals) > 8:
                message += f"... and {len(bearish_signals)-8} more bearish signals\n"
        
        message += f"\n📈 Summary: {len(bullish_signals)} Bullish, {len(bearish_signals)} Bearish, {len(neutral_signals)} Neutral"
        
        # Show message preview
        with st.expander("📱 Preview Telegram Message"):
            st.text(message)
        
        # Send button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("📤 Send to Telegram", type="primary", use_container_width=True):
                try:
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    payload = {"chat_id": CHAT_ID, "text": message}
                    response = requests.post(url, data=payload)
                    
                    if response.status_code == 200:
                        st.success("✅ Signals sent to Telegram successfully!")
                        st.balloons()
                    else:
                        st.error(f"❌ Failed to send: {response.text}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        # === PATTERN EXPLANATION ===
        st.subheader("🔍 Today's Pattern Analysis")
        
        if pattern == 0:
            st.info("🏦 **Banking sectors are cosmically aligned for growth today.** Jupiter and Venus favor financial instruments. Avoid heavy metals and industrial stocks.")
        elif pattern == 1:
            st.info("⚙️ **Metal and industrial sectors show strong planetary support.** Mars and Saturn boost manufacturing. Banking may face headwinds.")
        elif pattern == 2:
            st.info("💊 **Healthcare and pharmaceutical sectors are blessed today.** Moon and Mercury support healing industries. Heavy industries may struggle.")
        elif pattern == 3:
            st.info("💰 **Alternative assets like crypto and precious metals shine.** Rahu and Ketu favor unconventional investments. Traditional sectors may underperform.")
        else:
            st.info("🔄 **Mixed cosmic influences create selective opportunities.** Careful sector selection is key. Diversified approach recommended.")
        
    except Exception as e:
        st.error(f"❌ Error loading watchlist: {e}")
        st.info("💡 **Tip:** Make sure your file contains one symbol per line, like:\nNSE:HDFCBANK\nNSE:TATASTEEL\nMCX:GOLD1!")

else:
    # === DEMO SECTION ===
    st.info("👆 **Upload your watchlist to generate personalized astro-trading signals**")
    
    st.subheader("🌟 System Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **✅ Guaranteed Features:**
        - 🎯 Different results every day (5 patterns)
        - 🟢 Mixed bullish & bearish signals  
        - ⏰ Proper market timing (NSE/Global)
        - 📊 Sector-based analysis
        - 📱 Direct Telegram integration
        - 🔮 Astrological reasoning
        """)
    
    with col2:
        st.markdown("""
        **📅 Daily Patterns:**
        - **Pattern 0:** Banking Bullish
        - **Pattern 1:** Metal Bullish  
        - **Pattern 2:** Pharma Bullish
        - **Pattern 3:** Crypto & Gold Bullish
        - **Pattern 4:** Mixed Signals
        """)
    
    st.subheader("📋 Watchlist Format")
    st.code("""NSE:HDFCBANK
NSE:TATASTEEL
NSE:ICICIBANK
MCX:GOLD1!
MCX:SILVER1!
BITSTAMP:BTCUSD
COINBASE:ETHUSD""", language="text")
    
    st.success("🚀 **This system guarantees different results for different dates!**")

# === FOOTER ===
st.markdown("---")
st.markdown("🔮 **Professional Astro-Trading Signal Generator** | Built with Streamlit")
