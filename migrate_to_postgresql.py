#!/usr/bin/env python3
"""
Database Migration Script for Magic Card Scanner
Handles migration from SQLite to PostgreSQL for Railway deployment
"""

import os
import sqlite3
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.database import Base, Card, Scan, ScanImage, ScanResult

def get_database_engines():
    """Get both SQLite and PostgreSQL database engines"""
    
    # SQLite (source)
    sqlite_path = "magic_cards.db"
    if not os.path.exists(sqlite_path):
        print(f"❌ SQLite database not found: {sqlite_path}")
        return None, None
    
    sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
    
    # PostgreSQL (destination)
    postgres_url = os.getenv("DATABASE_URL")
    if not postgres_url:
        print("❌ DATABASE_URL environment variable not set")
        return sqlite_engine, None
    
    postgres_engine = create_engine(postgres_url)
    
    return sqlite_engine, postgres_engine

def create_tables(postgres_engine):
    """Create all tables in PostgreSQL database"""
    print("🏗️ Creating tables in PostgreSQL...")
    
    try:
        Base.metadata.create_all(bind=postgres_engine)
        print("✅ Tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def migrate_data(sqlite_engine, postgres_engine):
    """Migrate data from SQLite to PostgreSQL"""
    print("🔄 Starting data migration...")
    
    # Create sessions
    SqliteSession = sessionmaker(bind=sqlite_engine)
    PostgresSession = sessionmaker(bind=postgres_engine)
    
    sqlite_session = SqliteSession()
    postgres_session = PostgresSession()
    
    try:
        # Migrate in correct order to avoid foreign key constraint violations
        
        # 1. Migrate Scans first (no dependencies)
        print("🔍 Migrating scans...")
        scans = sqlite_session.query(Scan).all()
        for scan in scans:
            postgres_session.merge(scan)
        postgres_session.commit()
        print(f"✅ Migrated {len(scans)} scans")
        
        # 2. Migrate ScanImages (depends on Scans)
        print("🖼️ Migrating scan images...")
        scan_images = sqlite_session.query(ScanImage).all()
        for scan_image in scan_images:
            postgres_session.merge(scan_image)
        postgres_session.commit()
        print(f"✅ Migrated {len(scan_images)} scan images")
        
        # 3. Migrate ScanResults (depends on Scans and ScanImages)
        print("📊 Migrating scan results...")
        scan_results = sqlite_session.query(ScanResult).all()
        for scan_result in scan_results:
            postgres_session.merge(scan_result)
        postgres_session.commit()
        print(f"✅ Migrated {len(scan_results)} scan results")
        
        # 4. Migrate Cards last (depends on Scans and ScanResults)
        print("📦 Migrating cards...")
        cards = sqlite_session.query(Card).all()
        for card in cards:
            postgres_session.merge(card)
        postgres_session.commit()
        print(f"✅ Migrated {len(cards)} cards")
        
        print("✅ Data migration completed successfully")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        postgres_session.rollback()
        return False
    finally:
        sqlite_session.close()
        postgres_session.close()
    
    return True

def verify_migration(postgres_engine):
    """Verify that migration was successful"""
    print("🔍 Verifying migration...")
    
    PostgresSession = sessionmaker(bind=postgres_engine)
    session = PostgresSession()
    
    try:
        # Check counts
        card_count = session.query(Card).count()
        scan_count = session.query(Scan).count()
        scan_image_count = session.query(ScanImage).count()
        scan_result_count = session.query(ScanResult).count()
        
        print(f"📊 Migration verification:")
        print(f"   Cards: {card_count}")
        print(f"   Scans: {scan_count}")
        print(f"   Scan Images: {scan_image_count}")
        print(f"   Scan Results: {scan_result_count}")
        
        if card_count > 0:
            print("✅ Migration verification passed")
            return True
        else:
            print("⚠️ No cards found - migration may have failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False
    finally:
        session.close()

def main():
    """Main migration function"""
    print("🚀 Magic Card Scanner Database Migration")
    print("=" * 50)
    
    # Get database engines
    sqlite_engine, postgres_engine = get_database_engines()
    
    if not sqlite_engine:
        print("❌ Cannot proceed without SQLite database")
        return False
    
    if not postgres_engine:
        print("❌ Cannot proceed without PostgreSQL connection")
        return False
    
    # Create tables
    if not create_tables(postgres_engine):
        return False
    
    # Migrate data
    if not migrate_data(sqlite_engine, postgres_engine):
        return False
    
    # Verify migration
    if not verify_migration(postgres_engine):
        return False
    
    print("\n🎉 Migration completed successfully!")
    print("Your data is now ready for Railway deployment.")
    return True

if __name__ == "__main__":
    main() 