#!/usr/bin/env python3
"""
Check what files are actually in the Railway angelic_volume
Run this ON Railway using: railway run python check_railway_volume_contents.py
"""

import os
import sys
from pathlib import Path

def check_railway_environment():
    """Check if we're running on Railway"""
    print("🔍 RAILWAY ENVIRONMENT CHECK")
    print("=" * 40)
    
    # Check Railway indicators
    railway_indicators = [
        ("RAILWAY_ENVIRONMENT", os.getenv("RAILWAY_ENVIRONMENT")),
        ("RAILWAY_PROJECT_NAME", os.getenv("RAILWAY_PROJECT_NAME")), 
        ("RAILWAY_SERVICE_NAME", os.getenv("RAILWAY_SERVICE_NAME")),
        ("RAILWAY_VOLUME_NAME", os.getenv("RAILWAY_VOLUME_NAME")),
        ("RAILWAY_VOLUME_MOUNT_PATH", os.getenv("RAILWAY_VOLUME_MOUNT_PATH")),
        ("RAILWAY_STATIC_URL", os.getenv("RAILWAY_STATIC_URL")),
        ("RAILWAY_PUBLIC_DOMAIN", os.getenv("RAILWAY_PUBLIC_DOMAIN")),
    ]
    
    for var_name, var_value in railway_indicators:
        status = "✅" if var_value else "❌"
        print(f"{status} {var_name}: {var_value or 'Not set'}")
    
    if not os.path.exists("/app"):
        print("\n❌ NOT RUNNING ON RAILWAY")
        print("This script must be run ON Railway using:")
        print("railway run python check_railway_volume_contents.py")
        return False
    
    print("\n✅ RUNNING ON RAILWAY")
    return True

def check_all_possible_paths():
    """Check all possible volume mount paths"""
    print("\n📂 CHECKING ALL POSSIBLE VOLUME PATHS")
    print("=" * 40)
    
    # All possible paths where the volume might be mounted
    possible_paths = [
        "/app/uploads",
        "/data", 
        "/mnt/angelic_volume",
        "/app/angelic_volume",
        "/angelic_volume",
        "/data/angelic_volume",
        "/volume",
        "/app/volume",
        os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
    ]
    
    accessible_paths = []
    
    for path in possible_paths:
        if path:
            print(f"\n🔍 Checking: {path}")
            if os.path.exists(path):
                try:
                    files = os.listdir(path)
                    total_size = 0
                    image_files = []
                    
                    for file in files:
                        file_path = os.path.join(path, file)
                        if os.path.isfile(file_path):
                            try:
                                size = os.path.getsize(file_path)
                                total_size += size
                                
                                # Check if it's an image file
                                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                                    image_files.append((file, size))
                            except:
                                pass
                    
                    print(f"   ✅ EXISTS: {len(files)} total files, {len(image_files)} images")
                    print(f"   📊 Total size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
                    
                    if image_files:
                        print(f"   🖼️  Image files found:")
                        for filename, size in image_files[:5]:  # Show first 5
                            print(f"      - {filename} ({size:,} bytes)")
                        if len(image_files) > 5:
                            print(f"      ... and {len(image_files) - 5} more")
                    
                    accessible_paths.append((path, len(files), len(image_files), total_size))
                    
                except PermissionError:
                    print(f"   ❌ Permission denied")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
            else:
                print(f"   ❌ Does not exist")
    
    return accessible_paths

def check_scan_image_files():
    """Look for scan image files specifically"""
    print("\n🖼️  LOOKING FOR SCAN IMAGE FILES")
    print("=" * 40)
    
    # Look for scan image patterns
    scan_patterns = [
        "scan_*.jpg",
        "scan_*.jpeg", 
        "scan_*.png",
        "scan_*.webp"
    ]
    
    # Search in common locations
    search_paths = ["/app", "/data", "/mnt", "/volume"]
    
    found_scans = []
    
    for search_path in search_paths:
        if os.path.exists(search_path):
            try:
                for root, dirs, files in os.walk(search_path):
                    for file in files:
                        if file.startswith("scan_") and file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                            file_path = os.path.join(root, file)
                            try:
                                size = os.path.getsize(file_path)
                                found_scans.append((file_path, size))
                            except:
                                pass
            except:
                pass
    
    if found_scans:
        print(f"✅ Found {len(found_scans)} scan image files:")
        for file_path, size in found_scans:
            print(f"   - {file_path} ({size:,} bytes)")
    else:
        print("❌ No scan image files found anywhere")
    
    return found_scans

def check_directory_permissions():
    """Check what directories we can create and write to"""
    print("\n✏️  CHECKING WRITE PERMISSIONS")
    print("=" * 40)
    
    test_paths = [
        "/app/uploads",
        "/data",
        "/app"
    ]
    
    writable_paths = []
    
    for path in test_paths:
        try:
            # Try to create directory if it doesn't exist
            os.makedirs(path, exist_ok=True)
            
            # Try to write a test file
            test_file = os.path.join(path, "test_write.txt")
            with open(test_file, 'w') as f:
                f.write("test")
            
            # Clean up
            os.remove(test_file)
            
            print(f"✅ {path} - Can create and write")
            writable_paths.append(path)
            
        except Exception as e:
            print(f"❌ {path} - Cannot write: {e}")
    
    return writable_paths

def main():
    """Main function"""
    print("🚀 RAILWAY VOLUME CONTENTS CHECK")
    print("=" * 50)
    
    # Check if we're on Railway
    if not check_railway_environment():
        return
    
    # Check all possible volume paths
    accessible_paths = check_all_possible_paths()
    
    # Look for scan image files
    found_scans = check_scan_image_files()
    
    # Check write permissions
    writable_paths = check_directory_permissions()
    
    # Summary
    print("\n📊 SUMMARY")
    print("=" * 50)
    
    if accessible_paths:
        print("✅ ACCESSIBLE VOLUME PATHS:")
        for path, total_files, image_files, total_size in accessible_paths:
            print(f"   {path}: {total_files} files, {image_files} images, {total_size:,} bytes")
    else:
        print("❌ NO ACCESSIBLE VOLUME PATHS FOUND")
    
    if found_scans:
        print(f"\n✅ SCAN IMAGES: Found {len(found_scans)} scan image files")
    else:
        print("\n❌ SCAN IMAGES: No scan image files found")
    
    if writable_paths:
        print(f"\n✅ WRITABLE PATHS: {writable_paths}")
    else:
        print("\n❌ WRITABLE PATHS: None found")
    
    # Recommendations
    print("\n🔧 RECOMMENDATIONS:")
    if not accessible_paths:
        print("1. angelic_volume is not mounted or not accessible")
        print("2. Check Railway dashboard volume configuration")
        print("3. Verify mount path is set correctly")
    elif accessible_paths and not found_scans:
        print("1. Volume is mounted but empty")
        print("2. Upload scan images to the volume")
        print("3. Files should go to:", accessible_paths[0][0])
    elif found_scans:
        print("1. Volume has scan images - check why scan history isn't working")
        print("2. Verify app is looking in the right location")
        print("3. Check file permissions and paths")

if __name__ == "__main__":
    main() 