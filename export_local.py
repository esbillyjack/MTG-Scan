#!/usr/bin/env python3
"""
Local Export Script for Magic Card Scanner
Exports card data to local CSV or Excel files with file selection support.
"""

import sys
import json
import pandas as pd
import sqlite3
import os
from pathlib import Path
from datetime import datetime
import subprocess
import platform

def get_database_connection():
    """Get database connection - works with both SQLite (local) and PostgreSQL (Railway)."""
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # Railway/Cloud environment with PostgreSQL
        import psycopg2
        from sqlalchemy import create_engine
        
        # Use SQLAlchemy for PostgreSQL connection
        engine = create_engine(database_url)
        return engine
    else:
        # Local environment with SQLite
        env_mode = os.getenv("ENV_MODE", "production")
        if env_mode == "development":
            db_path = Path(__file__).parent / "magic_cards_dev.db"
        else:
            db_path = Path(__file__).parent / "magic_cards.db"
        return sqlite3.connect(str(db_path))

def export_cards_to_file(file_path, file_format="csv", overwrite=False):
    """Export cards to specified file path."""
    try:
        # Check if file exists and handle overwrite
        if Path(file_path).exists() and not overwrite:
            return {
                "success": False,
                "error": "File already exists. Use overwrite=True to replace it.",
                "file_exists": True
            }
        
        # Get card data from database
        conn = get_database_connection()
        
        # SQL query that works for both SQLite and PostgreSQL
        query = """
        SELECT 
            name,
            set_code,
            set_name,
            collector_number,
            rarity,
            condition,
            price_usd,
            mana_cost,
            type_line,
            oracle_text,
            count,
            notes,
            first_seen,
            last_seen,
            added_method
        FROM cards 
        WHERE deleted = false OR deleted IS NULL
        ORDER BY name, set_code
        """
        
        df = pd.read_sql_query(query, conn)
        
        # Close connection properly
        try:
            # Try SQLAlchemy engine dispose method
            conn.dispose()
        except AttributeError:
            try:
                # Try SQLite connection close method
                conn.close()
            except AttributeError:
                pass  # Connection doesn't need explicit closing
        
        if df.empty:
            return {
                "success": False,
                "error": "No cards found in database"
            }
        
        # Format the data
        df['price_usd'] = df['price_usd'].apply(lambda x: f"${x:.2f}" if pd.notna(x) and x > 0 else "")
        df['oracle_text'] = df['oracle_text'].fillna("")
        df['notes'] = df['notes'].fillna("")
        df['mana_cost'] = df['mana_cost'].fillna("")
        df['type_line'] = df['type_line'].fillna("")
        df['set_name'] = df['set_name'].fillna("")
        df['collector_number'] = df['collector_number'].fillna("")
        df['added_method'] = df['added_method'].fillna("LEGACY")
        
        # Rename columns for better readability
        df.columns = [
            'Card Name',
            'Set Code',
            'Set Name',
            'Collector Number',
            'Rarity',
            'Condition',
            'Price (USD)',
            'Mana Cost',
            'Type Line',
            'Oracle Text',
            'Count',
            'Notes',
            'First Seen',
            'Last Seen',
            'Added Method'
        ]
        
        # Create output directory if it doesn't exist
        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Export based on format
        if file_format.lower() == "excel":
            # Create Excel file with formatting
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Cards', index=False)
                
                # Get the workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Cards']
                
                # Make headers bold
                from openpyxl.styles import Font
                for cell in worksheet[1]:
                    cell.font = Font(bold=True)
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        else:
            # Export as CSV (default)
            df.to_csv(file_path, index=False)
        
        return {
            "success": True,
            "file_path": str(file_path),
            "record_count": len(df),
            "format": file_format
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "error": "File path is required"
        }))
        return
    
    file_path = sys.argv[1]
    file_format = sys.argv[2] if len(sys.argv) > 2 else "csv"
    overwrite = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else False
    
    result = export_cards_to_file(file_path, file_format, overwrite)
    print(json.dumps(result))
    
    # Open the directory containing the exported file on macOS
    if result["success"] and platform.system() == "Darwin":
        try:
            subprocess.run(["open", "-R", file_path], check=True)
        except subprocess.CalledProcessError:
            # Fallback to opening just the directory
            try:
                subprocess.run(["open", str(Path(file_path).parent)], check=True)
            except subprocess.CalledProcessError:
                pass  # Ignore if we can't open the directory

if __name__ == "__main__":
    main() 