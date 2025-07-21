# Scan History Integrity Policy

## Overview
The scan history is a critical component of the Magic Card Scanner system that must remain intact and complete. This policy establishes rules for maintaining scan history integrity across all operations.

## Core Principles

### 1. Scan History is Immutable
- **Scans** (scan records) should never be deleted
- **Scan Results** (AI identification results) should never be deleted  
- **Scan Images** (image files) should never be deleted
- **Scan Images Database Records** should never be deleted
- **Exception**: Scans that produced 0 cards may not be stored (as per system design)

### 2. Card Deletion Does Not Affect Scan History
- When a card is deleted from the collection, the scan that found it remains
- The scan result showing what was identified remains
- The image file and database record remain
- Only the card-to-scan relationship is broken

### 3. Complete Audit Trail
- Every scan must have a complete record of:
  - What image was processed
  - What the AI identified
  - What the user decided (accept/reject)
  - When it happened
  - What card (if any) was created
- **Exception**: Scans that produced 0 cards may not be stored (as per system design)

## Database Schema Requirements

### Tables That Must Be Preserved
1. **scans** - Master scan records
2. **scan_images** - Image file metadata and storage paths
3. **scan_results** - AI identification results and user decisions

### Tables That Can Be Modified
1. **cards** - Can be deleted, but scan_id reference should be preserved in scan_results

## Current Issues Identified

### Issue: Missing Scan Image Records
- **Problem**: Image files exist but no corresponding `scan_images` table entry
- **Example**: `scan_285_21bdff30-07d6-429c-84dc-a579e7ead68c.jpg` exists in uploads/ but no database record
- **Impact**: Images not synced to cloud, not tracked in reports
- **Solution**: Add missing scan_images entries for orphaned files
- **Note**: This applies only to scans that actually produced cards (non-zero results)

### Issue: Missing Cards from Scan Results
- **Problem**: Scan results show ACCEPTED cards that no longer exist in database
- **Example**: Scan 285 found Millstone (Result ID 1068), card was deleted
- **Impact**: Scan history shows false positives, inconsistent state
- **Solution**: Either restore missing cards or mark scan results as REJECTED

### Issue: Incomplete Sync
- **Problem**: Local images not uploaded to Railway cloud storage
- **Impact**: Images not accessible from cloud deployment, cache misses
- **Solution**: Ensure all scan_images records are synced to cloud storage

## Implementation Rules

### 1. Scan Processing
- Every uploaded image that produces cards must create a `scan_images` record
- Every scan that produces cards must create a `scan` record
- Every AI identification must create a `scan_result` record
- **Exception**: Scans with 0 cards found may not be stored (as per current system design)

### 2. Card Management
- When deleting cards, preserve all scan history
- When restoring cards, link back to original scan results
- Use soft deletion for cards (deleted flag) rather than hard deletion

### 3. Image Management
- All scan images must be tracked in `scan_images` table
- All images must be stored in Railway cloud storage (centralized)
- Local images serve as a cache for speed
- Smart fallback: check local first, then cloud if not found
- Both local and cloud app versions access the same centralized image storage

### 4. Data Integrity Checks
- Regular validation of scan-card relationships
- Detection of orphaned image files
- Detection of missing scan_images records
- Detection of scan results without corresponding cards

## Maintenance Procedures

### Daily Checks
- Run scan-card relationship report
- Check for orphaned image files
- Verify cloud sync status

### Weekly Maintenance
- Fix missing scan_images records
- Restore or properly mark missing cards
- Clean up any inconsistencies
- Ensure all images are in centralized cloud storage
- Verify cache functionality (local → cloud fallback)

### Monthly Review
- Full scan history audit
- Cloud storage verification
- Performance optimization

## Tools and Scripts

### Required Tools
1. **detailed_scan_card_report.py** - Relationship integrity checking
2. **sync_images_to_railway.py** - Cloud image synchronization
3. **fix_missing_scan_images.py** - Add missing database records
4. **restore_missing_cards.py** - Restore cards from scan results
5. **cache_management.py** - Manage local cache and cloud fallback

### Monitoring
- Database integrity checks
- File system monitoring
- Cloud sync status tracking

## Compliance

### Development
- All new features must preserve scan history
- No operations should delete scan-related data
- All image uploads must create proper database records

### Production
- Regular backup of scan history
- Monitoring of scan history integrity
- Automated alerts for missing data

## Emergency Procedures

### Data Recovery
- Restore from backups if scan history is corrupted
- Rebuild missing scan_images records from file system
- Restore missing cards from scan_results

### System Recovery
- Verify scan history integrity after any system changes
- Test cloud sync functionality
- Validate all scan-card relationships

---

**Policy Version**: 1.0  
**Effective Date**: 2025-07-15  
**Review Schedule**: Monthly  
**Owner**: System Administrator 