#!/usr/bin/env python3
"""
Migration script to add stack_count and stack_id fields
and update existing cards with proper stack information.
"""

import sqlite3
import uuid
from datetime import datetime

def migrate_database():
    """Migrate the database to add stack fields and update existing data"""
    conn = sqlite3.connect('magic_cards.db')
    cursor = conn.cursor()
    
    print("Starting database migration...")
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(cards)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add stack_count column if it doesn't exist
    if 'stack_count' not in columns:
        print("Adding stack_count column...")
        cursor.execute("ALTER TABLE cards ADD COLUMN stack_count INTEGER DEFAULT 1")
    
    # Add stack_id column if it doesn't exist
    if 'stack_id' not in columns:
        print("Adding stack_id column...")
        cursor.execute("ALTER TABLE cards ADD COLUMN stack_id TEXT")
    
    # Update existing cards with stack information
    print("Updating existing cards with stack information...")
    
    # Get all cards grouped by duplicate_group
    cursor.execute("""
        SELECT duplicate_group, COUNT(*) as count, SUM(count) as total_count
        FROM cards 
        WHERE duplicate_group IS NOT NULL 
        GROUP BY duplicate_group
    """)
    
    groups = cursor.fetchall()
    
    for duplicate_group, card_count, total_count in groups:
        # Generate a unique stack_id for this group
        stack_id = str(uuid.uuid4())
        
        # Update all cards in this group with the stack_id and stack_count
        cursor.execute("""
            UPDATE cards 
            SET stack_id = ?, stack_count = ?
            WHERE duplicate_group = ?
        """, (stack_id, total_count, duplicate_group))
        
        print(f"Updated group '{duplicate_group}': {card_count} cards, total count: {total_count}")
    
    # For cards without duplicate_group, create individual stack_ids
    cursor.execute("""
        UPDATE cards 
        SET stack_id = ?
        WHERE duplicate_group IS NULL OR duplicate_group = ''
    """, (str(uuid.uuid4()),))
    
    # Set stack_count to count for individual cards
    cursor.execute("""
        UPDATE cards 
        SET stack_count = count
        WHERE duplicate_group IS NULL OR duplicate_group = ''
    """)
    
    conn.commit()
    conn.close()
    
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate_database() 