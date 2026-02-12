from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings  # make sure settings.DATABASE_URL is correct

# Create SQLAlchemy engine
engine = create_engine(settings.DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Dependency for FastAPI endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
