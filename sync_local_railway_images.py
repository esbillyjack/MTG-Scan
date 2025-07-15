#!/usr/bin/env python3
import os
import sys
import requests
import logging
from pathlib import Path
from dotenv import load_dotenv
import aiofiles
import asyncio
import aiohttp
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_railway_url():
    """Get Railway app URL for file operations"""
    url = os.getenv("RAILWAY_APP_URL", "").rstrip('/')
    if url:
        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
    return url

async def download_railway_image(session, railway_url, filename, local_path):
    """Download a single image from Railway"""
    try:
        url = f"{railway_url}/uploads/{filename}"
        async with session.get(url) as response:
            if response.status == 200:
                async with aiofiles.open(local_path, 'wb') as f:
                    await f.write(await response.read())
                return True
            else:
                logger.error(f"Failed to download {filename}: {response.status}")
                return False
    except Exception as e:
        logger.error(f"Error downloading {filename}: {str(e)}")
        return False

async def upload_to_railway(session, railway_url, local_path, filename):
    """Upload a single image to Railway"""
    try:
        url = f"{railway_url}/api/upload"
        data = aiohttp.FormData()
        data.add_field('file',
                      open(local_path, 'rb'),
                      filename=filename,
                      content_type='image/jpeg')
        
        async with session.post(url, data=data) as response:
            if response.status == 200:
                return True
            else:
                logger.error(f"Failed to upload {filename}: {response.status}")
                return False
    except Exception as e:
        logger.error(f"Error uploading {filename}: {str(e)}")
        return False

async def sync_images():
    """Sync images between local and Railway environments"""
    railway_url = get_railway_url()
    if not railway_url:
        logger.error("Railway URL not configured")
        return

    # Ensure local uploads directory exists
    local_uploads = Path("uploads")
    local_uploads.mkdir(exist_ok=True)

    # Get list of local files
    local_files = set()
    for file in local_uploads.glob("*.*"):
        if file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
            local_files.add(file.name)

    # Get list of Railway files
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{railway_url}/api/files") as response:
                if response.status == 200:
                    railway_files = set((await response.json())['files'])
                else:
                    logger.error("Failed to get Railway files list")
                    return
    except Exception as e:
        logger.error(f"Error getting Railway files: {str(e)}")
        return

    # Files to download (in Railway but not local)
    to_download = railway_files - local_files
    # Files to upload (in local but not Railway)
    to_upload = local_files - railway_files

    logger.info(f"Found {len(to_download)} files to download and {len(to_upload)} files to upload")

    # Download missing files from Railway
    if to_download:
        logger.info("Downloading files from Railway...")
        async with aiohttp.ClientSession() as session:
            tasks = []
            for filename in to_download:
                local_path = local_uploads / filename
                task = download_railway_image(session, railway_url, filename, local_path)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            success = sum(1 for r in results if r)
            logger.info(f"Downloaded {success} of {len(to_download)} files")

    # Upload missing files to Railway
    if to_upload:
        logger.info("Uploading files to Railway...")
        async with aiohttp.ClientSession() as session:
            tasks = []
            for filename in to_upload:
                local_path = local_uploads / filename
                task = upload_to_railway(session, railway_url, local_path, filename)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            success = sum(1 for r in results if r)
            logger.info(f"Uploaded {success} of {len(to_upload)} files")

    logger.info("Sync complete!")

def main():
    """Main entry point"""
    try:
        asyncio.run(sync_images())
    except KeyboardInterrupt:
        logger.info("\nSync cancelled by user")
    except Exception as e:
        logger.error(f"Sync failed: {str(e)}")

if __name__ == "__main__":
    main() 