#!/usr/bin/env python3
"""
Graceful sequence handling utilities
"""

import logging
import time
from functools import wraps
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
import psycopg2.errors

logger = logging.getLogger(__name__)

def with_sequence_retry(max_retries=3, delay=0.1):
    """
    Decorator that automatically fixes sequences on UniqueViolation errors
    
    Usage:
        @with_sequence_retry()
        def create_scan(db, **kwargs):
            scan = Scan(**kwargs)
            db.add(scan)
            db.commit()
            return scan
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            db = args[0] if args else None  # Assume first arg is database session
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                    
                except IntegrityError as e:
                    if attempt == max_retries - 1:
                        raise  # Re-raise on final attempt
                    
                    # Check if it's a sequence-related constraint violation
                    if isinstance(e.orig, psycopg2.errors.UniqueViolation):
                        error_msg = str(e.orig)
                        
                        # Extract table name from error message
                        table_name = None
                        if "scans_pkey" in error_msg:
                            table_name = "scans"
                        elif "cards_pkey" in error_msg:
                            table_name = "cards"
                        elif "scan_images_pkey" in error_msg:
                            table_name = "scan_images"
                        elif "scan_results_pkey" in error_msg:
                            table_name = "scan_results"
                        
                        if table_name and db:
                            logger.warning(f"🔄 Sequence violation detected for {table_name}, attempting fix...")
                            
                            try:
                                # Fix the sequence
                                fix_table_sequence(db, table_name)
                                
                                # Rollback the failed transaction
                                db.rollback()
                                
                                # Wait a bit before retry
                                time.sleep(delay)
                                
                                logger.info(f"✅ Sequence fixed for {table_name}, retrying...")
                                continue
                                
                            except Exception as fix_error:
                                logger.error(f"❌ Failed to fix sequence for {table_name}: {fix_error}")
                    
                    # If we can't fix it, re-raise
                    raise
                    
                except Exception as e:
                    # For non-sequence errors, just re-raise
                    raise
            
            # Should never reach here
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def fix_table_sequence(db, table_name):
    """Fix sequence for a specific table"""
    sequence_name = f"{table_name}_id_seq"
    
    # Get max ID from table
    result = db.execute(text(f"SELECT MAX(id) FROM {table_name};"))
    max_id = result.scalar() or 0
    
    # Set sequence to max_id + 1
    next_id = max_id + 1
    db.execute(text(f"SELECT setval('{sequence_name}', {next_id}, false);"))
    db.commit()
    
    logger.info(f"🔧 Fixed {sequence_name}: set to {next_id}")

def create_scan_with_retry(db, **scan_data):
    """Example: Create scan with automatic sequence fixing"""
    from backend.database import Scan
    
    @with_sequence_retry(max_retries=2)
    def _create_scan(db_session):
        scan = Scan(**scan_data)
        db_session.add(scan)
        db_session.commit()
        db_session.refresh(scan)
        return scan
    
    return _create_scan(db)

def create_scan_image_with_retry(db, **image_data):
    """Example: Create scan image with automatic sequence fixing"""
    from backend.database import ScanImage
    
    @with_sequence_retry(max_retries=2)
    def _create_scan_image(db_session):
        scan_image = ScanImage(**image_data)
        db_session.add(scan_image)
        db_session.commit()
        db_session.refresh(scan_image)
        return scan_image
    
    return _create_scan_image(db) 