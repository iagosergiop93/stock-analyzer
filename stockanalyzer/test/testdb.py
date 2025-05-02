from sqlalchemy import create_engine, text
from stockanalyzer.config import DB_URL


engine = create_engine(DB_URL)
with engine.connect() as conn:
    result = conn.execute(text("SELECT now();"))
    print("DB time:", result.scalar())
