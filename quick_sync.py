#!/usr/bin/env python3
"""
Quick sync from SQLite dev database to PostgreSQL
"""

import sqlite3
import os
from sqlalchemy import create_engine, text

def sync_cards():
    """Sync cards from SQLite to PostgreSQL"""
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect('magic_cards_dev.db')
    sqlite_cursor = sqlite_conn.cursor()
    
    # Connect to PostgreSQL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not set")
        return
    
    engine = create_engine(database_url)
    
    print("🔄 Starting quick sync...")
    
    # Clear PostgreSQL cards table
    with engine.connect() as pg_conn:
        print("🗑️  Clearing PostgreSQL cards table...")
        pg_conn.execute(text("DELETE FROM cards"))
        pg_conn.commit()
        
        # Get cards from SQLite
        sqlite_cursor.execute("""
            SELECT name, set_code, set_name, collector_number, rarity, mana_cost,
                   type_line, oracle_text, flavor_text, power, toughness, colors,
                   image_url, price_usd, price_eur, price_tix, count, first_seen,
                   last_seen, notes, condition, is_example, duplicate_group,
                   stack_count, stack_id, unique_id, deleted, deleted_at, scan_id,
                   scan_result_id, import_status, added_method
            FROM cards 
            WHERE deleted = 0 OR deleted IS NULL
        """)
        
        cards = sqlite_cursor.fetchall()
        print(f"📦 Found {len(cards)} cards in SQLite")
        
        # Insert into PostgreSQL
        insert_sql = text("""
            INSERT INTO cards (
                name, set_code, set_name, collector_number, rarity, mana_cost,
                type_line, oracle_text, flavor_text, power, toughness, colors,
                image_url, price_usd, price_eur, price_tix, count, first_seen,
                last_seen, notes, condition, is_example, duplicate_group,
                stack_count, stack_id, unique_id, deleted, deleted_at, scan_id,
                scan_result_id, import_status, added_method
            ) VALUES (
                :name, :set_code, :set_name, :collector_number, :rarity, :mana_cost,
                :type_line, :oracle_text, :flavor_text, :power, :toughness, :colors,
                :image_url, :price_usd, :price_eur, :price_tix, :count, :first_seen,
                :last_seen, :notes, :condition, :is_example, :duplicate_group,
                :stack_count, :stack_id, :unique_id, :deleted, :deleted_at, :scan_id,
                :scan_result_id, :import_status, :added_method
            )
        """)
        
        for i, card in enumerate(cards):
            if i % 10 == 0:
                print(f"   Progress: {i}/{len(cards)} cards")
            
            # Convert to dict for SQLAlchemy
            card_dict = {
                'name': card[0], 'set_code': card[1], 'set_name': card[2],
                'collector_number': card[3], 'rarity': card[4], 'mana_cost': card[5],
                'type_line': card[6], 'oracle_text': card[7], 'flavor_text': card[8],
                'power': card[9], 'toughness': card[10], 'colors': card[11],
                'image_url': card[12], 'price_usd': card[13], 'price_eur': card[14],
                'price_tix': card[15], 'count': card[16], 'first_seen': card[17],
                'last_seen': card[18], 'notes': card[19], 'condition': card[20],
                'is_example': bool(card[21]), 'duplicate_group': card[22],
                'stack_count': card[23], 'stack_id': card[24], 'unique_id': card[25],
                'deleted': bool(card[26]), 'deleted_at': card[27], 'scan_id': card[28],
                'scan_result_id': card[29], 'import_status': card[30], 'added_method': card[31]
            }
            
            pg_conn.execute(insert_sql, card_dict)
        
        pg_conn.commit()
        print(f"✅ Successfully synced {len(cards)} cards to PostgreSQL")
    
    sqlite_conn.close()

if __name__ == "__main__":
    sync_cards() 