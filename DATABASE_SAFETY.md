# Database Safety & Backup Strategy

## Overview

The Magic Card Scanner uses SQLite for data storage, which provides excellent reliability but requires careful backup strategies to protect against data loss. This document outlines comprehensive backup and recovery procedures.

## Current Database Structure

### Files to Protect
- **`magic_cards.db`** - Main SQLite database (908KB)
- **`uploads/`** - Directory containing scan images
- **`backups/`** - Backup directory (created automatically)

### Database Tables
- **`cards`** - Individual card entries with condition, count, pricing
- **`scans`** - Scan sessions and metadata
- **`scan_images`** - Image file references
- **`scan_results`** - AI identification results

## Backup Strategy

### 1. Automatic Backups
```bash
# Start automatic backup scheduler (every 6 hours)
python auto_backup.py --daemon

# Force immediate backup
python auto_backup.py --force
```

### 2. Manual Backups
```bash
# Create backup with custom name
python backup_manager.py backup --name "pre_migration_backup"

# List all backups
python backup_manager.py list

# Get database statistics
python backup_manager.py stats
```

### 3. Data Export (for reconstruction)
```bash
# Export database schema and card data
python backup_manager.py export
```

## Recovery Procedures

### 1. Full Restore from Backup
```bash
# Restore from backup file
python backup_manager.py restore --backup-file backups/backup_20250113_143022.zip
```

### 2. Database Reconstruction
```bash
# Reconstruct from JSON export
python backup_manager.py reconstruct --json-file backups/cards_export_20250113_143022.json
```

### 3. Emergency Recovery Steps

#### If Database is Corrupted:
1. **Stop the application** immediately
2. **Locate the most recent backup**:
   ```bash
   python backup_manager.py list
   ```
3. **Restore from backup**:
   ```bash
   python backup_manager.py restore --backup-file backups/backup_YYYYMMDD_HHMMSS.zip
   ```
4. **Verify restoration**:
   ```bash
   python backup_manager.py stats
   ```

#### If No Backup Available:
1. **Export current data** (if database is partially accessible):
   ```bash
   python backup_manager.py export
   ```
2. **Reconstruct from JSON**:
   ```bash
   python backup_manager.py reconstruct --json-file backups/cards_export_YYYYMMDD_HHMMSS.json
   ```

## Backup Retention Policy

- **Keep last 10 backups** automatically
- **Backup every 6 hours** when scheduler is running
- **Manual backups** before major operations (migrations, updates)

## Data Reconstruction Capabilities

### What Can Be Reconstructed:
- ✅ **Card data** (name, set, condition, count, pricing)
- ✅ **Scan history** (scan sessions and results)
- ✅ **Image references** (file paths and metadata)
- ✅ **Timestamps** (first_seen, last_seen)

### What Cannot Be Reconstructed:
- ❌ **Original scan images** (if uploads directory is lost)
- ❌ **User notes** (if not in backup)
- ❌ **AI raw responses** (if not in backup)

## Best Practices

### 1. Regular Backups
- Run automatic backup scheduler: `python auto_backup.py --daemon`
- Create manual backups before major changes
- Test restore procedures periodically

### 2. Multiple Backup Locations
- **Local backups**: `backups/` directory
- **External storage**: Copy backup files to external drive
- **Cloud storage**: Upload backup files to cloud service

### 3. Verification
- **Check backup integrity**: All backups include integrity checks
- **Test restores**: Periodically test restore procedures
- **Monitor backup logs**: Check `backup_scheduler.log`

### 4. Before Major Operations
- **Database migrations**: Always backup before schema changes
- **Application updates**: Backup before updating
- **Bulk operations**: Backup before large data imports

## Monitoring & Alerts

### Backup Health Checks
```bash
# Check backup status
python backup_manager.py stats

# Verify recent backups
python backup_manager.py list
```

### Log Monitoring
- **Backup logs**: `backup_scheduler.log`
- **Application logs**: Check for database errors
- **Disk space**: Monitor available space for backups

## Emergency Contacts

### If Data Loss Occurs:
1. **Stop using the application** immediately
2. **Do not create new data** until recovery is complete
3. **Document the incident** with timestamps
4. **Follow recovery procedures** above
5. **Verify data integrity** after recovery

## Recovery Time Estimates

- **Full backup restore**: 1-5 minutes
- **JSON reconstruction**: 2-10 minutes
- **Manual data entry**: Hours to days (depending on collection size)

## Prevention Strategies

### 1. Hardware Protection
- **UPS**: Uninterruptible power supply
- **RAID**: Redundant storage arrays
- **Regular hardware maintenance**

### 2. Software Protection
- **Automatic backups**: Every 6 hours
- **Integrity checks**: Built into backup system
- **Error handling**: Graceful failure recovery

### 3. Operational Protection
- **User training**: Proper backup procedures
- **Documentation**: Clear recovery instructions
- **Testing**: Regular backup/restore tests

## Advanced Recovery

### Partial Data Recovery
If only some data is corrupted:
```bash
# Export current data
python backup_manager.py export

# Manually edit JSON file to remove corrupted entries
# Reconstruct from edited JSON
python backup_manager.py reconstruct --json-file edited_export.json
```

### Cross-Version Recovery
If database schema has changed:
1. Export data from old version
2. Update to new version
3. Import data using migration scripts

## Backup File Formats

### ZIP Backups (Recommended)
- **Format**: ZIP archive with metadata
- **Contents**: Database + uploads + metadata
- **Size**: Compressed, efficient storage
- **Integrity**: Built-in checksums

### SQL Dumps
- **Format**: SQL text files
- **Contents**: Database schema and data
- **Size**: Larger than ZIP backups
- **Use**: Schema reconstruction

### JSON Exports
- **Format**: JSON text files
- **Contents**: Card data and metadata
- **Size**: Human-readable, portable
- **Use**: Data migration, reconstruction

## Conclusion

The Magic Card Scanner includes comprehensive backup and recovery capabilities. By following these procedures and maintaining regular backups, you can protect your valuable card collection data against most types of data loss scenarios.

**Remember**: The best backup strategy is the one you actually use. Set up automatic backups and test your recovery procedures regularly. 