#!/usr/bin/env python3
"""
Fix Railway production database sequences
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_railway_sequences():
    """Fix Railway production database sequences"""
    
    # Get production database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found - Railway production database not configured")
        return False
    
    print("🚂 Fixing Railway production database sequences...")
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Fix scans table sequence
            result = conn.execute(text("SELECT MAX(id) FROM scans;"))
            max_scans_id = result.scalar()
            print(f"📊 Max scans ID: {max_scans_id}")
            
            if max_scans_id:
                next_scans_seq = max_scans_id + 1
                print(f"🔧 Setting scans sequence to: {next_scans_seq}")
                conn.execute(text(f"SELECT setval('scans_id_seq', {next_scans_seq}, false);"))
            
            # Fix cards table sequence  
            result = conn.execute(text("SELECT MAX(id) FROM cards;"))
            max_cards_id = result.scalar()
            print(f"📊 Max cards ID: {max_cards_id}")
            
            if max_cards_id:
                next_cards_seq = max_cards_id + 1
                print(f"🔧 Setting cards sequence to: {next_cards_seq}")
                conn.execute(text(f"SELECT setval('cards_id_seq', {next_cards_seq}, false);"))
            
            # Fix scan_images table sequence
            result = conn.execute(text("SELECT MAX(id) FROM scan_images;"))
            max_scan_images_id = result.scalar()
            print(f"📊 Max scan_images ID: {max_scan_images_id}")
            
            if max_scan_images_id:
                next_scan_images_seq = max_scan_images_id + 1
                print(f"🔧 Setting scan_images sequence to: {next_scan_images_seq}")
                conn.execute(text(f"SELECT setval('scan_images_id_seq', {next_scan_images_seq}, false);"))
            
            # Fix scan_results table sequence
            result = conn.execute(text("SELECT MAX(id) FROM scan_results;"))
            max_scan_results_id = result.scalar()
            print(f"📊 Max scan_results ID: {max_scan_results_id}")
            
            if max_scan_results_id:
                next_scan_results_seq = max_scan_results_id + 1
                print(f"🔧 Setting scan_results sequence to: {next_scan_results_seq}")
                conn.execute(text(f"SELECT setval('scan_results_id_seq', {next_scan_results_seq}, false);"))
            
            conn.commit()
            print("✅ Railway production database sequences fixed!")
            return True
            
    except Exception as e:
        print(f"❌ Error fixing Railway sequences: {e}")
        return False

if __name__ == "__main__":
    success = fix_railway_sequences()
    sys.exit(0 if success else 1) 