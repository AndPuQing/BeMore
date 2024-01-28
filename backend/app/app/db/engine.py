from app.core.config import settings
from sqlmodel import create_engine

engine = create_engine(
    f"postgresql+psycopg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@bemore-db/{settings.POSTGRES_DB}",
)
