#!/usr/bin/env python3
"""
Detailed test script with enhanced logging to diagnose AI consistency issues
"""

import requests
import json
import time
import shutil
import os

def check_ai_health():
    """Check AI health status"""
    try:
        response = requests.get("http://localhost:8000/debug/ai-health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"AI Health Status: {health_data['status']}")
            print(f"API Key Present: {health_data.get('api_key_present', 'Unknown')}")
            print(f"Rate Limit Interval: {health_data.get('rate_limit_interval', 'Unknown')}")
            if health_data.get('last_error'):
                print(f"Last Error: {health_data['last_error']}")
            return True
        else:
            print(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error checking health: {e}")
        return False

def test_single_upload():
    """Test single image upload with detailed logging"""
    source_path = "/Users/billjackson/Downloads/working/experiments/TradeBinder3.jpg"
    
    print(f"\n=== Testing single upload ===")
    
    try:
        # Copy image to uploads folder
        target_filename = f"test_detailed_{int(time.time())}.jpg"
        target_path = f"uploads/{target_filename}"
        shutil.copy2(source_path, target_path)
        
        # Upload via scan endpoint
        with open(target_path, 'rb') as f:
            files = {'files': (target_filename, f, 'image/jpeg')}
            upload_response = requests.post("http://localhost:8000/upload/scan", files=files)
            
        if upload_response.status_code != 200:
            print(f"Upload failed: {upload_response.status_code}")
            return None
            
        upload_data = upload_response.json()
        scan_id = upload_data['scan_id']
        print(f"Upload successful, scan ID: {scan_id}")
        
        # Process the scan
        process_response = requests.post(f"http://localhost:8000/scan/{scan_id}/process")
        if process_response.status_code != 200:
            print(f"Process failed: {process_response.status_code}")
            return None
            
        print("Processing completed")
        
        # Get results
        results_response = requests.get(f"http://localhost:8000/scan/{scan_id}/results")
        if results_response.status_code != 200:
            print(f"Results failed: {results_response.status_code}")
            return None
            
        results_data = results_response.json()
        cards_found = len(results_data.get('results', []))
        print(f"Cards found: {cards_found}")
        
        # Check for errors
        error_response = requests.get("http://localhost:8000/debug/ai-errors")
        if error_response.status_code == 200:
            error_data = error_response.json()
            if error_data.get('has_errors'):
                print(f"AI Error detected: {error_data['last_error']}")
        
        return {
            'scan_id': scan_id,
            'cards_found': cards_found,
            'results': results_data.get('results', [])
        }
        
    except Exception as e:
        print(f"Test failed: {e}")
        return None

def main():
    print("=== AI Consistency Test with Enhanced Logging ===")
    
    # Check AI health first
    if not check_ai_health():
        print("AI health check failed, stopping test")
        return
    
    # Run 3 test uploads
    results = []
    for i in range(3):
        print(f"\n--- Test {i+1} ---")
        result = test_single_upload()
        if result:
            results.append(result)
        time.sleep(2)  # Wait between tests
    
    print(f"\n=== Summary ===")
    print(f"Total tests: {len(results)}")
    cards_found_counts = [r['cards_found'] for r in results]
    print(f"Cards found per test: {cards_found_counts}")
    
    # Check consistency
    if len(set(cards_found_counts)) == 1:
        print("✅ Results are consistent!")
    else:
        print("❌ Results are inconsistent!")
        print("Check server logs for detailed AI response content")

if __name__ == "__main__":
    main() 