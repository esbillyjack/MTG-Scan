#!/usr/bin/env python3
"""
Database migration script to add new columns for soft deletion and unique IDs
"""

import sqlite3
import uuid
from datetime import datetime

def migrate_database():
    """Add new columns to existing database"""
    conn = sqlite3.connect('magic_cards.db')
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(cards)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add unique_id column if it doesn't exist
        if 'unique_id' not in columns:
            print("Adding unique_id column...")
            cursor.execute("ALTER TABLE cards ADD COLUMN unique_id TEXT")
            
            # Generate unique IDs for existing cards
            cursor.execute("SELECT id FROM cards")
            card_ids = cursor.fetchall()
            
            for card_id in card_ids:
                unique_id = str(uuid.uuid4())
                cursor.execute("UPDATE cards SET unique_id = ? WHERE id = ?", (unique_id, card_id[0]))
            
            # Create index for unique_id
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_unique_id ON cards(unique_id)")
            print(f"Generated unique IDs for {len(card_ids)} existing cards")
        
        # Add deleted column if it doesn't exist
        if 'deleted' not in columns:
            print("Adding deleted column...")
            cursor.execute("ALTER TABLE cards ADD COLUMN deleted BOOLEAN DEFAULT 0")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_deleted ON cards(deleted)")
            print("Added deleted column with default value False")
        
        # Add deleted_at column if it doesn't exist
        if 'deleted_at' not in columns:
            print("Adding deleted_at column...")
            cursor.execute("ALTER TABLE cards ADD COLUMN deleted_at DATETIME")
            print("Added deleted_at column")
        
        conn.commit()
        print("Database migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()