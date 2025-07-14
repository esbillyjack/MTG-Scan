from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import uuid
import json
import logging
from sqlalchemy import text

# Configure logging
logger = logging.getLogger(__name__)

# Database setup
# Railway PostgreSQL only - no SQLite fallbacks
env_mode = os.getenv("ENV_MODE", "production")

if env_mode == "development":
    # Development mode - use development PostgreSQL
    dev_database_url = os.getenv("DATABASE_URL_DEV")
    if not dev_database_url:
        raise ValueError("DATABASE_URL_DEV environment variable is required for development mode")
    
    # Development PostgreSQL connection - mask sensitive info
    masked_url = dev_database_url.split('@')[0] + '@[REDACTED]' if '@' in dev_database_url else dev_database_url
    print(f"🗄️ Using development PostgreSQL: {masked_url}")
    engine = create_engine(dev_database_url)
else:
    # Production mode - use production PostgreSQL
    prod_database_url = os.getenv("DATABASE_URL")
    if not prod_database_url:
        raise ValueError("DATABASE_URL environment variable is required for production mode")
    
    # Production PostgreSQL connection - mask sensitive info
    masked_url = prod_database_url.split('@')[0] + '@[REDACTED]' if '@' in prod_database_url else prod_database_url
    print(f"🌐 Using production PostgreSQL: {masked_url}")
    engine = create_engine(prod_database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def validate_and_fix_sequences():
    """Validate and fix PostgreSQL sequences on startup"""
    try:
        with engine.connect() as conn:
            # Define tables and their sequences
            tables_and_sequences = [
                ('cards', 'cards_id_seq'),
                ('scans', 'scans_id_seq'),
                ('scan_images', 'scan_images_id_seq'),
                ('scan_results', 'scan_results_id_seq')
            ]
            
            for table_name, sequence_name in tables_and_sequences:
                try:
                    # Get max ID from table
                    result = conn.execute(text(f"SELECT MAX(id) FROM {table_name};"))
                    max_id = result.scalar() or 0
                    
                    # Set sequence to max_id + 1
                    next_id = max_id + 1
                    conn.execute(text(f"SELECT setval('{sequence_name}', {next_id}, false);"))
                    
                    logger.info(f"✅ Fixed {sequence_name}: set to {next_id}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Could not fix {sequence_name}: {e}")
            
            conn.commit()
            logger.info("🔧 Database sequences validated and fixed")
            
    except Exception as e:
        logger.error(f"❌ Error validating sequences: {e}")


class Card(Base):
    __tablename__ = "cards"
    
    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))  # Unique ID for each card entry
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
    condition = Column(String, default="LP")  # Card condition (LP, NM, MP, HP, DMG)
    is_example = Column(Boolean, default=False)  # Mark as example/not owned
    duplicate_group = Column(String, index=True)  # Group identical cards together
    stack_id = Column(String, index=True)  # Unique identifier for the stack
    deleted = Column(Boolean, default=False, index=True)  # Soft deletion flag
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)  # When the card was soft deleted
    
    # New scan-related fields
    scan_id = Column(Integer, ForeignKey('scans.id'), nullable=True)  # Which scan created this card
    scan_result_id = Column(Integer, ForeignKey('scan_results.id'), nullable=True)  # Which scan result this came from
    import_status = Column(String, default="ACTIVE")  # PENDING, ACCEPTED, ACTIVE
    
    # How the card was added to the database
    added_method = Column(String, default="SCANNED")  # SCANNED, MANUAL, IMPORTED, BULK_IMPORT, etc.


class Scan(Base):
    __tablename__ = "scans"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String, default="PENDING")  # PENDING, PROCESSING, READY_FOR_REVIEW, COMPLETED, CANCELLED
    total_images = Column(Integer, default=0)
    processed_images = Column(Integer, default=0)
    total_cards_found = Column(Integer, default=0)
    unknown_cards_count = Column(Integer, default=0)
    notes = Column(Text, default="")
    
    # Relationships
    scan_images = relationship("ScanImage", back_populates="scan")
    scan_results = relationship("ScanResult", back_populates="scan")
    cards = relationship("Card", backref="scan")


class ScanImage(Base):
    __tablename__ = "scan_images"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey('scans.id'), nullable=False)
    filename = Column(String, nullable=False)  # Generated filename
    original_filename = Column(String, nullable=False)  # User's original filename
    file_path = Column(String, nullable=False)  # Path to stored file
    processed_at = Column(DateTime, nullable=True)
    cards_found = Column(Integer, default=0)
    processing_error = Column(Text, nullable=True)  # Store any processing errors
    
    # Relationships
    scan = relationship("Scan", back_populates="scan_images")
    scan_results = relationship("ScanResult", back_populates="scan_image")


class ScanResult(Base):
    __tablename__ = "scan_results"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey('scans.id'), nullable=False)
    scan_image_id = Column(Integer, ForeignKey('scan_images.id'), nullable=False)
    
    # AI identification results
    card_name = Column(String, nullable=False)
    set_code = Column(String, nullable=True)
    set_name = Column(String, nullable=True)
    collector_number = Column(String, nullable=True)
    confidence_score = Column(Float, default=0.0)  # 0-100 confidence score
    
    # User decision
    status = Column(String, default="PENDING")  # PENDING, ACCEPTED, REJECTED
    user_notes = Column(Text, default="")
    
    # Full card data from Scryfall as JSON
    card_data = Column(Text, nullable=True)  # JSON string of full card data
    
    # Raw AI response for debugging/review
    ai_raw_response = Column(Text, nullable=True)  # Raw text response from AI API
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)  # When user made accept/reject decision
    
    # Relationships
    scan = relationship("Scan", back_populates="scan_results")
    scan_image = relationship("ScanImage", back_populates="scan_results")
    card = relationship("Card", backref="scan_result")


def init_db():
    """Initialize the database and create tables"""
    Base.metadata.create_all(bind=engine)
    
    # Validate and fix sequences on startup
    validate_and_fix_sequences()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 