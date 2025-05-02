# data_ingestion.py

import os
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

from config import DB_URL
from stockanalyzer.data.data_init import init_db

# ─── Configuration ─────────────────────────────────────────────────────────────

# Which ticker(s) to fetch; you can expand this list
TICKERS = ["AAPL", "MSFT", "GOOG", "VOO"]

# How far back to fetch on each run; adjust as needed
FETCH_DAYS = 700

# Name of the table in Postgres/TimescaleDB
TABLE_NAME = "stock_prices"

# ─── DB Setup ─────────────────────────────────────────────────────────────────

engine = create_engine(DB_URL)

def ensure_hypertable():
    """Create the table + convert to hypertable if needed."""
    with engine.begin() as conn:
        # 1. Create table if not exists
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                ticker     TEXT       NOT NULL,
                timestamp  TIMESTAMPTZ NOT NULL,
                open       DOUBLE PRECISION,
                high       DOUBLE PRECISION,
                low        DOUBLE PRECISION,
                close      DOUBLE PRECISION,
                volume     BIGINT,
                PRIMARY KEY (ticker, timestamp)
            );
        """))
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME}_staging (
                ticker     TEXT       NOT NULL,
                timestamp  TIMESTAMPTZ NOT NULL,
                open       DOUBLE PRECISION,
                high       DOUBLE PRECISION,
                low        DOUBLE PRECISION,
                close      DOUBLE PRECISION,
                volume     BIGINT,
                PRIMARY KEY (ticker, timestamp)
            );
        """))
        # 2. Convert to hypertable (ignores if already hypertable)
        try:
            conn.execute(text(f"""
                SELECT create_hypertable(
                    '{TABLE_NAME}',
                    'timestamp',
                    if_not_exists => TRUE
                );
            """))
        except ProgrammingError as e:
            # In some TimescaleDB versions this might raise; safe to ignore
            print("Warning creating hypertable:", e)

# ─── Data Fetch & Load ────────────────────────────────────────────────────────

def fetch_prices(ticker: str, days: int = FETCH_DAYS) -> pd.DataFrame:
    """
    Fetches the last `days` of historical data for `ticker`.
    Returns a DataFrame indexed by timestamp with columns: Open, High, Low, Close, Volume.
    """
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    df = yf.download(
        ticker,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        interval="1d",
        progress=False
    )
    if df.empty:
        return df

    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.index = pd.to_datetime(df.index)
    df.reset_index(inplace=True)
    df.rename(columns={"Date": "timestamp"}, inplace=True)
    df["ticker"] = ticker
    # reorder columns for SQL
    return df[["ticker", "timestamp", "Open", "High", "Low", "Close", "Volume"]]

def upsert_to_db(df: pd.DataFrame):
    """
    Inserts or updates records in the DB.
    Uses Postgres ON CONFLICT to avoid duplicates.
    """
    if df.empty:
        print("No data to upsert.")
        return

    # Use a temporary staging table for upsert
    staging_table = f"{TABLE_NAME}_staging"

    with engine.begin() as conn:
        # 1. Write staging
        df.to_sql(staging_table, conn, if_exists="replace", index=False)
        # 2. Upsert into main table
        conn.execute(text(f"""
            INSERT INTO {TABLE_NAME} AS main (ticker, timestamp, open, high, low, close, volume)
            SELECT *
            FROM {staging_table} st
            ON CONFLICT (ticker, timestamp)
            DO UPDATE SET
              open = EXCLUDED.open,
              high = EXCLUDED.high,
              low = EXCLUDED.low,
              close = EXCLUDED.close,
              volume = EXCLUDED.volume;
        """))
        # 3. Drop staging
        conn.execute(text(f"DROP TABLE IF EXISTS {staging_table};"))

# ─── Main Runner ──────────────────────────────────────────────────────────────

def main():
    print(f"[{datetime.utcnow()}] Starting data ingestion for {TICKERS}")
    ensure_hypertable()
    init_db()

    for ticker in TICKERS:
        print(f"  → Fetching {ticker} for last {FETCH_DAYS} days…")
        df = fetch_prices(ticker)
        if df.empty:
            print(f"    ⚠️ No data returned for {ticker}")
            continue

        print(f"    Writing {len(df)} rows to DB…")
        upsert_to_db(df)

    print(f"[{datetime.utcnow()}] Data ingestion complete.")

if __name__ == "__main__":
    main()
