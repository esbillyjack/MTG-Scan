from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database setup
DATABASE_URL = "sqlite:///./magic_cards.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Card(Base):
    __tablename__ = "cards"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    set_code = Column(String)
    set_name = Column(String)
    collector_number = Column(String)
    rarity = Column(String)
    mana_cost = Column(String)
    type_line = Column(String)
    oracle_text = Column(Text)
    flavor_text = Column(Text)
    power = Column(String)
    toughness = Column(String)
    colors = Column(String)
    image_url = Column(String)
    price_usd = Column(Float)
    price_eur = Column(Float)
    price_tix = Column(Float)
    count = Column(Integer, default=1)  # Individual card count (how many times scanned)
    stack_count = Column(Integer, default=1)  # Total count in the stack (sum of all duplicates)
    notes = Column(Text, default="")  # User notes about the card
    condition = Column(String, default="NM")  # Card condition (NM, LP, MP, HP, DMG)
    is_example = Column(Boolean, default=False)  # Mark as example/not owned
    duplicate_group = Column(String, index=True)  # Group identical cards together
    stack_id = Column(String, index=True)  # Unique identifier for the stack
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

def init_db():
    """Initialize the database and create tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 