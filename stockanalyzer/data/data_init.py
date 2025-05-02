from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from .stockprice import Base
from config import DB_URL
# ─── Initialization & Hypertable Setup ────────────────────────────────────────

def init_db(echo: bool = False):
    """
    Create tables and convert the stock_prices table into a TimescaleDB hypertable.
    Returns a SQLAlchemy engine and session factory.
    """
    engine = create_engine(DB_URL, echo=echo)
    # Create the table if it doesn't exist
    Base.metadata.create_all(engine)

    # Enable TimescaleDB extension and hypertable
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb;"))
        conn.execute(text(
            "SELECT create_hypertable('stock_prices', 'timestamp', if_not_exists => TRUE);"
        ))

    SessionLocal = sessionmaker(bind=engine)
    return engine, SessionLocal

