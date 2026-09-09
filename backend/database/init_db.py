"""
Database initialization — creates all tables and seeds initial data.
"""

from backend.database.base import Base
from backend.database.session import engine, SessionLocal
from backend.database.seeds import seed_all

# Import all models so Base.metadata knows about them
import backend.models  # noqa: F401


def init_database():
    """Create all tables and insert seed data."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
    print("Database initialized successfully.")
