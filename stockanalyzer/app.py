# app.py

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import date, timedelta

from config import DB_URL

# ─── Initialize DB Engine ──────────────────────────────────────────────────────
engine = create_engine(DB_URL)

# ─── Streamlit App ───────────────────────────────────────────────────────────
st.set_page_config(page_title="Stock Prices Dashboard", layout="wide")
st.title("📈 Stock Prices Dashboard")

# ─── Sidebar Controls ─────────────────────────────────────────────────────────
# Fetch distinct tickers from the database
@st.cache_data

def load_tickers():
    query = "SELECT DISTINCT ticker FROM stock_prices;"
    df = pd.read_sql(query, engine)
    return df['ticker'].tolist()

tickers = load_tickers()
selected = st.sidebar.multiselect(
    "Select Tickers", options=tickers, default=tickers[:3]
)

start_date = st.sidebar.date_input(
    "Start date", value=date.today() - timedelta(days=30)
)
end_date = st.sidebar.date_input(
    "End date", value=date.today()
)

if start_date > end_date:
    st.sidebar.error("Error: Start date must be before end date.")

# ─── Load Data ────────────────────────────────────────────────────────────────
@st.cache_data

def load_data(tickers, start, end):
    # Query data between dates for selected tickers
    query = f"""
        SELECT ticker, timestamp, close, volume
        FROM stock_prices
        WHERE ticker IN ({', '.join([f"'{t}'" for t in tickers])})
          AND timestamp::date BETWEEN '{start}' AND '{end}'
        ORDER BY timestamp;
    """
    df = pd.read_sql(query, engine, parse_dates=['timestamp'])
    return df

if not selected:
    st.warning("Please select at least one ticker to display the dashboard.")
    st.stop()

data = load_data(selected, start_date, end_date)

# ─── KPI Metrics ──────────────────────────────────────────────────────────────
st.header("Key Metrics")
cols = st.columns(len(selected))
for idx, ticker in enumerate(selected):
    df_t = data[data['ticker'] == ticker]
    if df_t.empty:
        cols[idx].warning(f"No data for {ticker}")
        continue
    avg = df_t['close'].mean()
    max_val = df_t['close'].max()
    min_val = df_t['close'].min()
    vol = df_t['volume'].mean()
    cols[idx].metric(label=f"{ticker} Average Close", value=f"{avg:.2f}")
    cols[idx].metric(label=f"{ticker} Max Close", value=f"{max_val:.2f}")
    cols[idx].metric(label=f"{ticker} Min Close", value=f"{min_val:.2f}")
    cols[idx].metric(label=f"{ticker} Volume", value=f"{vol:.0f}")

# ─── Line Charts ─────────────────────────────────────────────────────────────
for ticker in selected:
    st.header(f"{ticker}")
    df_t = data[data['ticker'] == ticker]
    if df_t.empty:
        continue
    st.subheader("Price")
    chart_data = df_t.set_index('timestamp')['close']
    st.line_chart(chart_data)

    st.subheader("Volume")
    vol_data = df_t.set_index('timestamp')['volume']
    st.line_chart(vol_data)

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Data sourced from Yahoo Finance via yfinance.")
