from database import engine
from models import Base

# This will create all tables defined with Base metadata
Base.metadata.create_all(bind=engine)
