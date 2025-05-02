from sqlalchemy import Column, Text, DateTime, Float, BigInteger, PrimaryKeyConstraint
from sqlalchemy.ext.declarative import declarative_base


# ─── SQLAlchemy Base ──────────────────────────────────────────────────────────
Base = declarative_base()

class StockPrice(Base):
    __tablename__ = 'stock_prices'

    ticker = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    open = Column('open', Float)
    high = Column('high', Float)
    low = Column('low', Float)
    close = Column('close', Float)
    volume = Column(BigInteger)

    __table_args__ = (
        PrimaryKeyConstraint('ticker', 'timestamp'),
    )