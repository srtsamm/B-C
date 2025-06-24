import streamlit as st
import pandas as pd
import pandas_ta as ta
import ccxt

def fetch_ohlcv(symbol, timeframe='5m', limit=100):
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def calculate_score(symbol='BTC/USDT'):
    try:
        timeframes = ['1m', '5m', '15m', '1h', '4h']
        weight_per_tf = 100 / len(timeframes)
        total_score = 0

        for tf in timeframes:
            df = fetch_ohlcv(symbol, tf, limit=100)
            df['rsi'] = ta.rsi(df['close'], length=14)
            macd = ta.macd(df['close'])
            df['macd'] = macd['MACD_12_26_9']
            df['macd_signal'] = macd['MACDs_12_26_9']
            df['vwap'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])

            latest = df.iloc[-1]
            score = 0

            if latest['macd'] > latest['macd_signal']:
                score += 30
            elif latest['macd'] < latest['macd_signal']:
                score += 10

            if latest['rsi'] < 30:
                score += 30
            elif latest['rsi'] > 70:
                score += 10
            else:
                score += 20

            if latest['close'] > latest['vwap']:
                score += 30
            else:
                score += 10

            avg_volume = df['volume'].tail(10).mean()
            if latest['volume'] > avg_volume:
                score += 10
            else:
                score += 5

            weighted_score = (score / 100) * weight_per_tf
            total_score += weighted_score

        return round(total_score, 2)
    except Exception as e:
        return f"Error: {str(e)}"

st.set_page_config(page_title="Crypto Score Dashboard", layout="centered")
st.title("📊 Real-Time Crypto Scoring Bot")

symbol_input = st.text_input("Enter coin pair (format: COIN/QUOTE, e.g. BTC/USDT):", "BTC/USDT")
if st.button("Get Score"):
    with st.spinner("Fetching data and calculating score..."):
        score = calculate_score(symbol_input.upper())
        if isinstance(score, str):
            st.error(score)
        else:
            st.metric("📈 Buy/Sell Score", f"{score}/100")
            if score >= 70:
                st.success("🔼 Strong Buy")
            elif score <= 30:
                st.error("🔽 Strong Sell")
            else:
                st.warning("⏸️ Neutral")
            st.progress(score / 100)
