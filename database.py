from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Use .env or fallback
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dispatch_user:dispatch_pass@localhost/silodispatch")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declare base
Base = declarative_base()

# Import models AFTER declaring Base
from models import Driver, Batch, Order, Breadcrumb
 # ⚠️ Make sure this import is present

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency for DB sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
