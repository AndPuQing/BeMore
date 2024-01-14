from sqlmodel import create_engine

from bemore.core.config import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
