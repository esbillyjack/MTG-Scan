#!/usr/bin/env python3
"""
Railway Sequence Reset Script
Run this as a one-time deployment on Railway to reset PostgreSQL sequences
"""

import os
import sys
from sqlalchemy import create_engine, text

def reset_sequences():
    """Reset PostgreSQL sequences to prevent duplicate key violations"""
    postgres_url = os.getenv("DATABASE_URL")
    if not postgres_url:
        print("❌ DATABASE_URL not set")
        sys.exit(1)
    
    print("🔄 Connecting to PostgreSQL database...")
    try:
        engine = create_engine(postgres_url)
        with engine.connect() as conn:
            tables = ['cards', 'scans', 'scan_images', 'scan_results']
            
            print("🔍 Resetting sequences for all tables...")
            for table in tables:
                try:
                    seq_name = f'{table}_id_seq'
                    
                    # Get current max ID
                    max_id_query = text(f"SELECT COALESCE(MAX(id), 0) FROM {table}")
                    result = conn.execute(max_id_query)
                    max_id = result.scalar() or 0
                    
                    # Reset sequence to max_id + 1
                    next_id = max_id + 1
                    reset_query = text(f"SELECT setval('{seq_name}', {next_id}, false)")
                    conn.execute(reset_query)
                    
                    print(f"✅ Reset sequence for {table} (max_id: {max_id}, next_id: {next_id})")
                    
                except Exception as e:
                    print(f"⚠️ Error resetting {table}: {e}")
                    
            conn.commit()
            print("🎉 All sequences reset successfully!")
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Railway PostgreSQL Sequence Reset")
    print("=" * 40)
    reset_sequences() 