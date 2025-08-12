import streamlit as st
import pandas as pd
from datetime import datetime, time
import requests

# === TELEGRAM SETTINGS ===
BOT_TOKEN = "7613703350:AAE-W4dJ37lngM4lO2Tnuns8-a-80jYRtxk"
CHAT_ID = "-1002840229810"

st.title("🎯 FIXED - Actual Stock Symbols Processing")

# Date selector
selected_date = st.date_input("Select Date", value=datetime.now().date())

# Calculate pattern
day_number = selected_date.timetuple().tm_yday
pattern = day_number % 3

st.error(f"📅 DATE: {selected_date} | PATTERN: {pattern}")

# Two separate file uploaders
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Upload Watchlist (Your Stocks)")
    watchlist_file = st.file_uploader(
        "Upload your stock symbols file", 
        type="txt", 
        key="watchlist",
        help="File with NSE:HDFCBANK, MCX:GOLD1!, etc."
    )

with col2:
    st.subheader("🌙 Upload Transit Data (Optional)")
    transit_file = st.file_uploader(
        "Upload planetary data", 
        type="txt", 
        key="transit",
        help="Your planetary transit file"
    )

# Only process if we have the watchlist
if watchlist_file:
    # Read ACTUAL stock symbols from watchlist
    try:
        watchlist_content = watchlist_file.read().decode('utf-8')
        
        # Extract actual stock symbols (skip headers and planetary data)
        stock_symbols = []
        for line in watchlist_content.split('\n'):
            line = line.strip()
            
            # Skip empty lines, headers, and planetary data
            if (line and 
                not line.startswith('#') and
                not line.startswith('Planet') and
                not line.startswith('Mo ') and
                not line.startswith('Ma ') and
                not line.startswith('Me ') and
                not line.startswith('Ju ') and
                not line.startswith('Ve ') and
                not line.startswith('Sa ') and
                not line.startswith('Ra ') and
                not line.startswith('Ke ') and
                not line.startswith('Su ') and
                ':' in line):  # Must contain ':' for proper symbols
                stock_symbols.append(line)
        
        st.success(f"✅ Found {len(stock_symbols)} actual stock symbols")
        
        # Show the symbols we found
        with st.expander("👀 Detected Stock Symbols"):
            for i, symbol in enumerate(stock_symbols[:10], 1):
                st.write(f"{i}. {symbol}")
            if len(stock_symbols) > 10:
                st.write(f"... and {len(stock_symbols)-10} more")
        
        if stock_symbols:
            # Apply pattern-based logic to ACTUAL stock symbols
            signals = []
            
            for symbol in stock_symbols:
                symbol_upper = symbol.upper()
                
                # Pattern 0: Banking Bearish Day
                if pattern == 0:
                    if any(bank in symbol_upper for bank in ['HDFCBANK', 'ICICIBANK', 'SBIN', 'AXISBANK', 'KOTAKBANK', 'BANK']):
                        sentiment = 'Bearish'
                        reason = 'Banking sector unfavorable'
                    elif any(metal in symbol_upper for metal in ['TATASTEEL', 'JSWSTEEL', 'METAL', 'STEEL']):
                        sentiment = 'Bullish'
                        reason = 'Metal sector favorable'
                    elif any(crypto in symbol_upper for crypto in ['BTC', 'ETH', 'CRYPTO']):
                        sentiment = 'Bullish'
                        reason = 'Crypto favorable'
                    else:
                        sentiment = 'Bearish'
                        reason = 'General market unfavorable'
                
                # Pattern 1: Metal Bearish Day  
                elif pattern == 1:
                    if any(metal in symbol_upper for metal in ['TATASTEEL', 'JSWSTEEL', 'METAL', 'STEEL']):
                        sentiment = 'Bearish'
                        reason = 'Metal sector unfavorable'
                    elif any(bank in symbol_upper for bank in ['HDFCBANK', 'ICICIBANK', 'SBIN', 'AXISBANK', 'BANK']):
                        sentiment = 'Bullish'
                        reason = 'Banking sector favorable'
                    elif 'GOLD' in symbol_upper or 'SILVER' in symbol_upper:
                        sentiment = 'Bullish'
                        reason = 'Precious metals favorable'
                    else:
                        sentiment = 'Bearish'
                        reason = 'General market unfavorable'
                
                # Pattern 2: Crypto Bearish Day
                else:
                    if any(crypto in symbol_upper for crypto in ['BTC', 'ETH', 'CRYPTO']):
                        sentiment = 'Bearish'
                        reason = 'Crypto sector unfavorable'
                    elif any(bank in symbol_upper for bank in ['HDFCBANK', 'ICICIBANK', 'SBIN', 'BANK']):
                        sentiment = 'Bullish'
                        reason = 'Banking sector favorable'
                    elif any(pharma in symbol_upper for pharma in ['PHARMA', 'DRUG', 'BIO']):
                        sentiment = 'Bullish'
                        reason = 'Pharma sector favorable'
                    else:
                        sentiment = 'Bearish'
                        reason = 'General market unfavorable'
                
                # Determine market timing
                if symbol.startswith(('NSE:', 'BSE:')):
                    entry, exit = '09:15', '15:30'
                else:
                    entry, exit = '05:00', '21:00'
                
                signals.append({
                    'Symbol': symbol,
                    'Sentiment': sentiment,
                    'Entry': entry,
                    'Exit': exit,
                    'Reason': reason
                })
            
            # Display results
            bullish_signals = [s for s in signals if s['Sentiment'] == 'Bullish']
            bearish_signals = [s for s in signals if s['Sentiment'] == 'Bearish']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🟢 Bullish Count", len(bullish_signals))
            with col2:
                st.metric("🔴 Bearish Count", len(bearish_signals))
            with col3:
                st.metric("📊 Total Signals", len(signals))
            
            # Show signals
            st.subheader("🎯 Trading Signals for Your Stocks")
            
            if bullish_signals:
                st.write("**🟢 BULLISH SIGNALS (BUY):**")
                for signal in bullish_signals:
                    st.success(f"🟢 **{signal['Symbol']}** → BUY | Entry: {signal['Entry']} | Exit: {signal['Exit']} | *{signal['Reason']}*")
            
            if bearish_signals:
                st.write("**🔴 BEARISH SIGNALS (SELL):**")
                for signal in bearish_signals:
                    st.error(f"🔴 **{signal['Symbol']}** → SELL | Entry: {signal['Entry']} | Exit: {signal['Exit']} | *{signal['Reason']}*")
            
            # Telegram message
            current_time = datetime.now().strftime("%d-%b-%Y %H:%M")
            message = f"🎯 Stock Trading Signals — {selected_date.strftime('%d-%b-%Y')} Pattern {pattern} (Generated {current_time})\n\n"
            
            if bullish_signals:
                message += f"🟢 BUY SIGNALS ({len(bullish_signals)}):\n"
                for signal in bullish_signals:
                    message += f"🟢 {signal['Symbol']} → BUY | {signal['Entry']}-{signal['Exit']}\n"
                message += "\n"
            
            if bearish_signals:
                message += f"🔴 SELL SIGNALS ({len(bearish_signals)}):\n"
                for signal in bearish_signals:
                    message += f"🔴 {signal['Symbol']} → SELL | {signal['Entry']}-{signal['Exit']}\n"
            
            # Send button
            if st.button("📤 Send Stock Signals to Telegram"):
                try:
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    payload = {"chat_id": CHAT_ID, "text": message}
                    response = requests.post(url, data=payload)
                    
                    if response.status_code == 200:
                        st.success("✅ Stock signals sent!")
                        st.balloons()
                    else:
                        st.error(f"❌ Failed: {response.text}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            
        else:
            st.error("❌ No valid stock symbols found in your watchlist!")
            st.info("💡 Make sure your file contains lines like:\nNSE:HDFCBANK\nNSE:TATASTEEL\nMCX:GOLD1!")
    
    except Exception as e:
        st.error(f"❌ Error reading watchlist: {e}")

else:
    st.warning("📈 Upload your stock watchlist to see which stocks to buy/sell")
    
    st.markdown("""
    ## 🎯 What This Fix Does:
    
    **❌ Before:** Processing planetary data as stock symbols  
    **✅ After:** Processing your actual stock symbols
    
    ### 📋 Expected Results:
    ```
    🔴 NSE:HDFCBANK → SELL | Entry: 09:15 | Exit: 15:30
    🟢 NSE:TATASTEEL → BUY | Entry: 09:15 | Exit: 15:30  
    🔴 MCX:GOLD1! → SELL | Entry: 05:00 | Exit: 21:00
    🟢 BITSTAMP:BTCUSD → BUY | Entry: 05:00 | Exit: 21:00
    ```
    
    ### 📁 Watchlist File Format:
    ```
    NSE:HDFCBANK
    NSE:TATASTEEL
    NSE:ICICIBANK
    MCX:GOLD1!
    MCX:SILVER1!
    BITSTAMP:BTCUSD
    COINBASE:ETHUSD
    ```
    
    **Now you'll see exactly which stocks to buy and which to sell!** 🎯
    """)
