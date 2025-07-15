#!/usr/bin/env python3
"""
Check Railway environment variables and deployment configuration
"""

import requests
import json
import os
import sys
from urllib.parse import urljoin

def check_railway_environment(base_url):
    """Check Railway environment variables and status"""
    try:
        print(f"🔍 Checking Railway environment at: {base_url}")
        
        # Check environment endpoint
        env_response = requests.get(f"{base_url}/api/environment", timeout=10)
        if env_response.status_code == 200:
            env_data = env_response.json()
            print(f"✅ Environment API accessible")
            print(f"   Environment: {env_data.get('environment', 'unknown')}")
            print(f"   Port: {env_data.get('port', 'unknown')}")
            print(f"   Is Development: {env_data.get('is_development', 'unknown')}")
            print(f"   Uses Railway Files: {env_data.get('uses_railway_files', 'unknown')}")
            print(f"   Railway URL: {env_data.get('railway_url', 'None')}")
        else:
            print(f"❌ Environment API not accessible: {env_response.status_code}")
            return False
        
        # Check database status
        db_response = requests.get(f"{base_url}/api/database/status", timeout=10)
        if db_response.status_code == 200:
            db_data = db_response.json()
            print(f"✅ Database API accessible")
            print(f"   Database Type: {db_data.get('database', {}).get('type', 'unknown')}")
            print(f"   Database Location: {db_data.get('database', {}).get('location', 'unknown')}")
            print(f"   Total Cards: {db_data.get('statistics', {}).get('total_cards', 'unknown')}")
            print(f"   Total Scans: {db_data.get('statistics', {}).get('total_scans', 'unknown')}")
            print(f"   Storage Type: {db_data.get('storage', {}).get('type', 'unknown')}")
            print(f"   Storage Path: {db_data.get('storage', {}).get('path', 'unknown')}")
        else:
            print(f"❌ Database status API not accessible: {db_response.status_code}")
            return False
        
        # Check scan history endpoint
        scan_response = requests.get(f"{base_url}/scan/history", timeout=10)
        if scan_response.status_code == 200:
            scan_data = scan_response.json()
            print(f"✅ Scan history API accessible")
            print(f"   Success: {scan_data.get('success', 'unknown')}")
            print(f"   Total Scans: {scan_data.get('total_scans', 'unknown')}")
            print(f"   Scans Returned: {len(scan_data.get('scans', []))}")
            
            # Check if scans have images
            scans = scan_data.get('scans', [])
            if scans:
                first_scan = scans[0]
                print(f"   First Scan ID: {first_scan.get('id', 'unknown')}")
                print(f"   First Scan Status: {first_scan.get('status', 'unknown')}")
                print(f"   First Scan Images: {len(first_scan.get('images', []))}")
                print(f"   First Scan Cards: {len(first_scan.get('cards', []))}")
            else:
                print(f"   No scans returned")
        else:
            print(f"❌ Scan history API not accessible: {scan_response.status_code}")
            if scan_response.status_code == 500:
                try:
                    error_data = scan_response.json()
                    print(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"   Error: {scan_response.text}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking Railway environment: {e}")
        return False

def main():
    """Main function to check both environments"""
    print("🚀 Railway Environment Check")
    print("=" * 50)
    
    # Check if we can access production Railway
    print("\n🌐 PRODUCTION RAILWAY CHECK")
    print("-" * 30)
    
    # You'll need to replace this with your actual Railway production URL
    production_url = input("Enter your production Railway URL (e.g., https://your-app.railway.app): ").strip()
    
    if not production_url:
        print("❌ No production URL provided")
        return
    
    production_ok = check_railway_environment(production_url)
    
    # Check local development if running
    print("\n🔧 LOCAL DEVELOPMENT CHECK")
    print("-" * 30)
    
    development_url = "http://localhost:8001"  # Development port
    development_ok = check_railway_environment(development_url)
    
    if not development_ok:
        print("   Development server not running or not accessible")
        print("   Try starting it with: ./start_server_dev.sh")
    
    # Summary
    print("\n📊 SUMMARY")
    print("-" * 30)
    print(f"Production Railway: {'✅ Working' if production_ok else '❌ Issues detected'}")
    print(f"Development Local: {'✅ Working' if development_ok else '❌ Not accessible'}")
    
    if production_ok and development_ok:
        print("\n💡 Both environments are accessible. The issue may be:")
        print("   - Environment variables (ENV_MODE, USE_RAILWAY_FILES, etc.)")
        print("   - File storage configuration")
        print("   - Code version differences")
        print("   - Railway deployment configuration")
    elif production_ok and not development_ok:
        print("\n💡 Production is accessible but development is not running")
        print("   Start development server to compare environments")
    elif not production_ok:
        print("\n💡 Production Railway has issues:")
        print("   - Check Railway logs for errors")
        print("   - Verify environment variables are set correctly")
        print("   - Ensure latest code is deployed")

if __name__ == "__main__":
    main() 