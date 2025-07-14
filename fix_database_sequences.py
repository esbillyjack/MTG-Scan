#!/usr/bin/env python3
"""
Fix database sequence issues causing primary key constraint violations
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_database_sequences():
    """Fix PostgreSQL sequence issues"""
    
    # Get database URL
    database_url = os.getenv("DATABASE_URL_DEV") or os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ No database URL found")
        return False
    
    print("🔧 Fixing database sequences...")
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Fix scans table sequence
            print("🔧 Fixing scans table sequence...")
            conn.execute(text("SELECT setval('scans_id_seq', COALESCE((SELECT MAX(id) FROM scans), 1), false);"))
            
            # Fix cards table sequence
            print("🔧 Fixing cards table sequence...")
            conn.execute(text("SELECT setval('cards_id_seq', COALESCE((SELECT MAX(id) FROM cards), 1), false);"))
            
            # Fix other sequences that might exist
            result = conn.execute(text("SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public';"))
            sequences = result.fetchall()
            
            for seq in sequences:
                seq_name = seq[0]
                table_name = seq_name.replace('_id_seq', '')
                
                if table_name in ['scans', 'cards']:
                    continue  # Already fixed above
                
                print(f"🔧 Fixing {seq_name} sequence...")
                try:
                    conn.execute(text(f"SELECT setval('{seq_name}', COALESCE((SELECT MAX(id) FROM {table_name}), 1), false);"))
                except Exception as e:
                    print(f"⚠️  Could not fix {seq_name}: {e}")
            
            conn.commit()
            print("✅ Database sequences fixed!")
            return True
            
    except Exception as e:
        print(f"❌ Error fixing database sequences: {e}")
        return False

if __name__ == "__main__":
    success = fix_database_sequences()
    sys.exit(0 if success else 1) 