#!/usr/bin/env python3
"""
Migration script to add new fields to the database
"""

import sqlite3
import os
from backend.database import SessionLocal, Card

def migrate_database():
    """Add new columns to the existing database"""
    conn = sqlite3.connect('magic_cards.db')
    cursor = conn.cursor()
    
    print("Migrating database...")
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(cards)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add new columns if they don't exist
    new_columns = [
        ('notes', 'TEXT DEFAULT ""'),
        ('condition', 'TEXT DEFAULT "NM"'),
        ('is_example', 'BOOLEAN DEFAULT 0'),
        ('duplicate_group', 'TEXT')
    ]
    
    for column_name, column_def in new_columns:
        if column_name not in columns:
            print(f"Adding column: {column_name}")
            cursor.execute(f"ALTER TABLE cards ADD COLUMN {column_name} {column_def}")
    
    # Mark all existing cards as examples (since they're test data)
    print("Marking existing cards as examples...")
    cursor.execute("UPDATE cards SET is_example = 1")
    
    # Create duplicate groups for identical cards
    print("Creating duplicate groups...")
    cursor.execute("""
        UPDATE cards 
        SET duplicate_group = name || '|' || COALESCE(set_code, '') || '|' || COALESCE(collector_number, '')
        WHERE duplicate_group IS NULL
    """)
    
    conn.commit()
    conn.close()
    
    print("Migration completed successfully!")

def cleanup_database():
    db = SessionLocal()
    try:
        # Remove cards with no image_url or empty image_url
        cards_no_image = db.query(Card).filter((Card.image_url == None) | (Card.image_url == '')).all()
        for card in cards_no_image:
            db.delete(card)
        db.commit()
        print(f"Removed {len(cards_no_image)} cards with no image_url.")

        # Remove cards with fake/test image URLs (containing '123456')
        cards_fake_image = db.query(Card).filter(Card.image_url.like('%123456%')).all()
        for card in cards_fake_image:
            db.delete(card)
        db.commit()
        print(f"Removed {len(cards_fake_image)} cards with fake image URLs.")

        # Remove cards with empty set_code
        cards_no_set = db.query(Card).filter((Card.set_code == None) | (Card.set_code == '')).all()
        for card in cards_no_set:
            db.delete(card)
        db.commit()
        print(f"Removed {len(cards_no_set)} cards with no set_code.")

        # Fix stack_count and count for remaining cards
        all_cards = db.query(Card).all()
        for card in all_cards:
            # In individual view, each card should have count=1
            card.count = 1
            # stack_count should match count for individual cards
            card.stack_count = 1
        db.commit()
        print(f"Fixed count and stack_count for {len(all_cards)} cards.")

        # Mark all remaining cards as is_example=True
        remaining = db.query(Card).all()
        for card in remaining:
            card.is_example = True
        db.commit()
        print(f"Marked {len(remaining)} cards as example cards.")
        
    finally:
        db.close()

if __name__ == "__main__":
    migrate_database()
    cleanup_database()