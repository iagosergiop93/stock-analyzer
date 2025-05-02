import os
from dotenv import load_dotenv

load_dotenv()

# Database URL for SQLAlchemy / psycopg2
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
