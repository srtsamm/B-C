import streamlit as st
import pandas as pd
import ccxt
import numpy as np

def fetch_ohlcv(symbol, timeframe='5m', limit=100):
    exchange = ccxt.bybit()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    return macd, macd_signal

def compute_vwap(df):
    tp = (df['high'] + df['low'] + df['close']) / 3
    vwap = (tp * df['volume']).cumsum() / df['volume'].cumsum()
    return vwap

def calculate_score(symbol='BTC/USDT'):
    timeframes = ['1m', '5m', '15m', '1h', '4h']
    weight = 100 / len(timeframes)
    total_score = 0

    for tf in timeframes:
        df = fetch_ohlcv(symbol, tf, 100)
        df['rsi'] = compute_rsi(df['close'])
        df['macd'], df['macd_signal'] = compute_macd(df['close'])
        df['vwap'] = compute_vwap(df)

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

        avg_vol = df['volume'].tail(10).mean()
        if latest['volume'] > avg_vol:
            score += 10
        else:
            score += 5

        total_score += (score / 100) * weight

    return round(total_score, 2)

st.set_page_config(page_title="Crypto Score Bot", layout="centered")
st.title("📊 Real-Time Crypto Scoring Bot (Bybit)")

symbol = st.text_input("Enter pair (e.g. BTC/USDT):", "BTC/USDT")
if st.button("Get Score"):
    with st.spinner("Calculating score..."):
        try:
            score = calculate_score(symbol.upper())
            st.metric("📈 Score", f"{score}/100")
            if score >= 70:
                st.success("🔼 Strong Buy")
            elif score <= 30:
                st.error("🔽 Strong Sell")
            else:
                st.warning("⏸️ Neutral")
            st.progress(score / 100)
        except Exception as e:
            st.error(f"Error: {e}")
