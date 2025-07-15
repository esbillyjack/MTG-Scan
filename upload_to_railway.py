#!/usr/bin/env python3
"""
Upload scan images to Railway volume
Run this script ON Railway using: railway run python upload_to_railway.py
"""

import os
import shutil
import sys
from pathlib import Path

# Files to upload (generated from local scan)
FILES_TO_UPLOAD = [
    ("scan_138_99e414eb-e1da-41a5-bc10-1c2bb4079762.jpg", "uploads_backup/scan_138_99e414eb-e1da-41a5-bc10-1c2bb4079762.jpg"),
    ("scan_139_b20a4fa6-7dbb-4126-bc58-8ae687ebb46a.jpg", "uploads_backup/scan_139_b20a4fa6-7dbb-4126-bc58-8ae687ebb46a.jpg"),
    ("scan_140_0fba90c2-ad17-42c8-b1f4-e3c53a6b5bac.jpg", "uploads_backup/scan_140_0fba90c2-ad17-42c8-b1f4-e3c53a6b5bac.jpg"),
    ("scan_141_9c8a989b-f3f3-4f88-b8e2-e04db0737255.jpg", "uploads_backup/scan_141_9c8a989b-f3f3-4f88-b8e2-e04db0737255.jpg"),
    ("scan_145_f56d87d2-9e11-4a48-8475-26e338990c1f.jpg", "uploads_backup/scan_145_f56d87d2-9e11-4a48-8475-26e338990c1f.jpg"),
    ("scan_150_85c1ee7f-59b8-4217-b640-2a725c61fc9b.jpg", "uploads_backup/scan_150_85c1ee7f-59b8-4217-b640-2a725c61fc9b.jpg"),
    ("scan_154_a7441cf3-d167-41b0-899d-859491672782.jpg", "uploads_backup/scan_154_a7441cf3-d167-41b0-899d-859491672782.jpg"),
    ("scan_155_0732d342-cd02-40ca-88cf-f1af75b4144f.jpg", "uploads_backup/scan_155_0732d342-cd02-40ca-88cf-f1af75b4144f.jpg"),
    ("scan_157_7026b7d9-fba4-4e96-942f-d2a15938c3f3.jpg", "uploads_backup/scan_157_7026b7d9-fba4-4e96-942f-d2a15938c3f3.jpg"),
    ("scan_159_04079bea-fd7c-4c3c-8c75-cf176181f985.jpg", "uploads_backup/scan_159_04079bea-fd7c-4c3c-8c75-cf176181f985.jpg"),
    ("scan_160_2d8bced7-d5bd-441e-a7fc-9191add64264.jpg", "uploads_backup/scan_160_2d8bced7-d5bd-441e-a7fc-9191add64264.jpg"),
    ("scan_161_295d90b0-d421-42af-a451-de8fdacaa9cf.jpg", "uploads_backup/scan_161_295d90b0-d421-42af-a451-de8fdacaa9cf.jpg"),
    ("scan_162_97b6db5e-dde3-47ea-9c85-38bd525b3415.jpg", "uploads_backup/scan_162_97b6db5e-dde3-47ea-9c85-38bd525b3415.jpg"),
    ("scan_162_9c4e88a6-35e6-41ba-98b6-c12ce543df6c.jpg", "uploads_backup/scan_162_9c4e88a6-35e6-41ba-98b6-c12ce543df6c.jpg"),
    ("scan_162_ef094fa9-662b-4902-adc1-6736eb84a208.jpg", "uploads_backup/scan_162_ef094fa9-662b-4902-adc1-6736eb84a208.jpg"),
    ("scan_162_b65dafab-5502-46ba-97c1-ce70fef77e20.jpg", "uploads_backup/scan_162_b65dafab-5502-46ba-97c1-ce70fef77e20.jpg"),
    ("scan_163_10be4661-c93a-4c41-87d9-b0e0a8630c7a.jpg", "uploads_backup/scan_163_10be4661-c93a-4c41-87d9-b0e0a8630c7a.jpg"),
    ("scan_163_61b79cc0-5515-4a68-a97e-af5567e44b00.jpg", "uploads_backup/scan_163_61b79cc0-5515-4a68-a97e-af5567e44b00.jpg"),
    ("scan_163_33c52b27-da8f-41ec-b9f4-1439b511adfc.jpg", "uploads_backup/scan_163_33c52b27-da8f-41ec-b9f4-1439b511adfc.jpg"),
    ("scan_163_60505061-e377-4c7e-b0e9-f50a893b4919.jpg", "uploads_backup/scan_163_60505061-e377-4c7e-b0e9-f50a893b4919.jpg"),
    ("scan_163_ec51ff84-8550-40ee-b244-a72dfe4dd670.jpg", "uploads_backup/scan_163_ec51ff84-8550-40ee-b244-a72dfe4dd670.jpg"),
    ("scan_163_d8100d2a-4ddf-4f8a-bd31-d1da2785d1de.jpg", "uploads_backup/scan_163_d8100d2a-4ddf-4f8a-bd31-d1da2785d1de.jpg"),
    ("scan_170_36e80f8c-2c99-4327-b267-c6bb56c66af1.png", "uploads_backup/scan_170_36e80f8c-2c99-4327-b267-c6bb56c66af1.png"),
    ("scan_171_d32a0d16-f82f-41a9-911c-351c2126cc96.png", "uploads_backup/scan_171_d32a0d16-f82f-41a9-911c-351c2126cc96.png"),
    ("scan_180_c2c39ac2-2b28-45aa-a606-72e89c61ab71.webp", "uploads_backup/scan_180_c2c39ac2-2b28-45aa-a606-72e89c61ab71.webp"),
    ("scan_181_8461db5e-f45b-4cd8-a836-94f9998651fb.webp", "uploads_backup/scan_181_8461db5e-f45b-4cd8-a836-94f9998651fb.webp"),
    ("scan_182_5030e9fa-6bb2-499b-997c-5db696028bfa.webp", "uploads_backup/scan_182_5030e9fa-6bb2-499b-997c-5db696028bfa.webp"),
    ("scan_183_2534249e-281c-4e04-a4da-5e11dc8cbd8d.webp", "uploads_backup/scan_183_2534249e-281c-4e04-a4da-5e11dc8cbd8d.webp"),
    ("scan_185_4cf3a607-daa3-4c9f-95d2-82071b5c9187.png", "uploads_backup/scan_185_4cf3a607-daa3-4c9f-95d2-82071b5c9187.png"),
    ("scan_186_588bf897-e1f5-408e-a08c-18a5eeaeb206.webp", "uploads_backup/scan_186_588bf897-e1f5-408e-a08c-18a5eeaeb206.webp"),
    ("scan_195_18851e64-e4fb-43f3-bf7f-d13364f47acd.jpg", "uploads_backup/scan_195_18851e64-e4fb-43f3-bf7f-d13364f47acd.jpg"),
    ("scan_197_9b666393-649c-418d-8e9e-a566914abdaa.jpg", "uploads_backup/scan_197_9b666393-649c-418d-8e9e-a566914abdaa.jpg"),
    ("scan_198_90ab3b08-ce09-4838-a33a-cd114f8a6183.jpg", "uploads_backup/scan_198_90ab3b08-ce09-4838-a33a-cd114f8a6183.jpg"),
    ("scan_199_80cf30a1-2504-47dd-99a6-24b89067f7b5.webp", "uploads_backup/scan_199_80cf30a1-2504-47dd-99a6-24b89067f7b5.webp"),
    ("scan_202_93f78d75-92bb-440f-9b54-26e44ea77766.jpg", "uploads_backup/scan_202_93f78d75-92bb-440f-9b54-26e44ea77766.jpg"),
    ("scan_203_806671af-93bc-4753-877e-828b93b273a6.jpg", "uploads_backup/scan_203_806671af-93bc-4753-877e-828b93b273a6.jpg"),
    ("scan_204_3a06e621-3326-4c92-87f9-d284802f6098.jpg", "uploads_backup/scan_204_3a06e621-3326-4c92-87f9-d284802f6098.jpg"),
    ("scan_205_1467361d-9548-48d7-898c-f3791c9aad16.jpg", "uploads_backup/scan_205_1467361d-9548-48d7-898c-f3791c9aad16.jpg"),
    ("scan_206_9594a3c8-5af9-4a8d-bc36-1d731cd7c99e.jpg", "uploads_backup/scan_206_9594a3c8-5af9-4a8d-bc36-1d731cd7c99e.jpg"),
    ("scan_207_4bce8878-ff62-463e-becd-60481935c7a1.jpg", "uploads_backup/scan_207_4bce8878-ff62-463e-becd-60481935c7a1.jpg"),
    ("scan_208_c58276f3-0fa6-4bf1-8478-8d9299018a3b.jpg", "uploads_backup/scan_208_c58276f3-0fa6-4bf1-8478-8d9299018a3b.jpg"),
]

def upload_files():
    """Upload files to Railway volume"""
    
    # Check if running on Railway
    if not os.path.exists("/app"):
        print("❌ This script must be run on Railway")
        print("Use: railway run python upload_to_railway.py")
        return
    
    uploads_path = "/app/uploads"
    
    # Ensure uploads directory exists
    os.makedirs(uploads_path, exist_ok=True)
    
    print(f"📤 Uploading {len(FILES_TO_UPLOAD)} files to Railway volume...")
    
    uploaded_count = 0
    
    for filename, local_path in FILES_TO_UPLOAD:
        # Create file with dummy content (since we can't transfer actual files)
        railway_path = os.path.join(uploads_path, filename)
        
        try:
            # Create placeholder file
            with open(railway_path, 'w') as f:
                f.write(f"# Placeholder for {filename}\n")
                f.write(f"# Original path: {local_path}\n")
                f.write(f"# You need to manually upload this file\n")
            
            print(f"✅ Created placeholder: {filename}")
            uploaded_count += 1
            
        except Exception as e:
            print(f"❌ Failed to create {filename}: {e}")
    
    print(f"\n📊 Created {uploaded_count} placeholder files")
    print(f"📁 Files are in: {uploads_path}")
    
    # List final contents
    if os.path.exists(uploads_path):
        files = os.listdir(uploads_path)
        print(f"\n📋 Railway volume now contains {len(files)} files")

if __name__ == "__main__":
    upload_files()
