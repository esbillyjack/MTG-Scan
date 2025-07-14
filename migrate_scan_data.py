#!/usr/bin/env python3
"""
Focused migration script for scan data from SQLite to PostgreSQL
"""

import os
import sqlite3
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.database import Base, Card, Scan, ScanImage, ScanResult

def migrate_scan_data():
    """Migrate scan data from SQLite to Railway PostgreSQL"""
    
    print("🚀 Starting scan data migration to Railway...")
    print("=" * 50)
    
    # Check local database
    sqlite_path = "magic_cards.db"
    if not os.path.exists(sqlite_path):
        print(f"❌ Local database not found: {sqlite_path}")
        return False
    
    # Connect to databases
    print("📡 Connecting to databases...")
    sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
    
    postgres_url = os.getenv("DATABASE_URL")
    if not postgres_url:
        print("❌ DATABASE_URL environment variable not set")
        return False
    
    print(f"🌐 Target database: {postgres_url.split('@')[0]}@[REDACTED]")
    postgres_engine = create_engine(postgres_url)
    
    # Create sessions
    SqliteSession = sessionmaker(bind=sqlite_engine)
    PostgresSession = sessionmaker(bind=postgres_engine)
    
    sqlite_session = SqliteSession()
    postgres_session = PostgresSession()
    
    try:
        # Check what we have in SQLite
        print("\n📊 Checking local scan data...")
        scan_count = sqlite_session.query(Scan).count()
        image_count = sqlite_session.query(ScanImage).count()
        result_count = sqlite_session.query(ScanResult).count()
        
        print(f"   • Scans: {scan_count}")
        print(f"   • Scan Images: {image_count}")
        print(f"   • Scan Results: {result_count}")
        
        if scan_count == 0:
            print("⚠️ No scan data found in local database")
            return True
        
        # Check current PostgreSQL state
        print("\n📊 Checking current PostgreSQL state...")
        pg_scan_count = postgres_session.query(Scan).count()
        pg_image_count = postgres_session.query(ScanImage).count()
        pg_result_count = postgres_session.query(ScanResult).count()
        
        print(f"   • Scans: {pg_scan_count}")
        print(f"   • Scan Images: {pg_image_count}")
        print(f"   • Scan Results: {pg_result_count}")
        
        # Clear existing scan data if any
        if pg_scan_count > 0 or pg_image_count > 0 or pg_result_count > 0:
            print("\n🗑️ Clearing existing scan data...")
            postgres_session.query(ScanResult).delete()
            postgres_session.query(ScanImage).delete()
            postgres_session.query(Scan).delete()
            postgres_session.commit()
            print("✅ Cleared existing scan data")
        
        # Migrate Scans
        print("\n🔍 Migrating scans...")
        scans = sqlite_session.query(Scan).all()
        migrated_scans = 0
        for scan in scans:
            try:
                # Create new scan with same ID
                new_scan = Scan(
                    id=scan.id,
                    created_at=scan.created_at,
                    updated_at=scan.updated_at,
                    status=scan.status,
                    total_images=scan.total_images,
                    processed_images=scan.processed_images,
                    total_cards_found=scan.total_cards_found,
                    unknown_cards_count=scan.unknown_cards_count,
                    notes=scan.notes
                )
                postgres_session.merge(new_scan)
                migrated_scans += 1
                
                if migrated_scans % 10 == 0:
                    print(f"   • Migrated {migrated_scans}/{len(scans)} scans...")
                    
            except Exception as e:
                print(f"   ❌ Error migrating scan {scan.id}: {e}")
                continue
        
        postgres_session.commit()
        print(f"✅ Migrated {migrated_scans} scans")
        
        # Migrate ScanImages
        print("\n🖼️ Migrating scan images...")
        scan_images = sqlite_session.query(ScanImage).all()
        migrated_images = 0
        for image in scan_images:
            try:
                new_image = ScanImage(
                    id=image.id,
                    scan_id=image.scan_id,
                    filename=image.filename,
                    original_filename=image.original_filename,
                    file_path=image.file_path,
                    processed_at=image.processed_at,
                    cards_found=image.cards_found,
                    processing_error=image.processing_error
                )
                postgres_session.merge(new_image)
                migrated_images += 1
                
                if migrated_images % 10 == 0:
                    print(f"   • Migrated {migrated_images}/{len(scan_images)} images...")
                    
            except Exception as e:
                print(f"   ❌ Error migrating image {image.id}: {e}")
                continue
        
        postgres_session.commit()
        print(f"✅ Migrated {migrated_images} scan images")
        
        # Migrate ScanResults
        print("\n📊 Migrating scan results...")
        scan_results = sqlite_session.query(ScanResult).all()
        migrated_results = 0
        for result in scan_results:
            try:
                new_result = ScanResult(
                    id=result.id,
                    scan_id=result.scan_id,
                    scan_image_id=result.scan_image_id,
                    card_name=result.card_name,
                    set_code=result.set_code,
                    set_name=result.set_name,
                    collector_number=result.collector_number,
                    confidence_score=result.confidence_score,
                    status=result.status,
                    user_notes=result.user_notes,
                    card_data=result.card_data,
                    ai_raw_response=result.ai_raw_response,
                    created_at=result.created_at,
                    decided_at=result.decided_at
                )
                postgres_session.merge(new_result)
                migrated_results += 1
                
                if migrated_results % 50 == 0:
                    print(f"   • Migrated {migrated_results}/{len(scan_results)} results...")
                    
            except Exception as e:
                print(f"   ❌ Error migrating result {result.id}: {e}")
                continue
        
        postgres_session.commit()
        print(f"✅ Migrated {migrated_results} scan results")
        
        # Verify final state
        print("\n✅ Verifying migration...")
        final_scan_count = postgres_session.query(Scan).count()
        final_image_count = postgres_session.query(ScanImage).count()
        final_result_count = postgres_session.query(ScanResult).count()
        
        print(f"   • Final scans: {final_scan_count}")
        print(f"   • Final images: {final_image_count}")
        print(f"   • Final results: {final_result_count}")
        
        print("\n🎉 Scan data migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        postgres_session.rollback()
        return False
    finally:
        sqlite_session.close()
        postgres_session.close()

if __name__ == "__main__":
    # Set up DATABASE_URL if not already set
    if not os.getenv("DATABASE_URL"):
        print("DATABASE_URL environment variable not set")
        sys.exit(1)
    
    success = migrate_scan_data()
    if success:
        print("\n🚀 Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Migration failed!")
        sys.exit(1) 