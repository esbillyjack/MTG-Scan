#!/usr/bin/env python3
"""
Simple test server for Magic Card Scanner
"""

import sys
import os
sys.path.append('backend')

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

# Create a simple FastAPI app
app = FastAPI(title="Magic Card Scanner Test", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    try:
        with open("frontend/index.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except Exception as e:
        return HTMLResponse(f"<h1>Magic Card Scanner</h1><p>Error loading page: {e}</p>")

@app.get("/test")
async def test_endpoint():
    """Test endpoint"""
    return {"message": "Magic Card Scanner is running!", "status": "success"}

@app.post("/cards")
async def add_card(card_data: dict):
    """Add a new card to the database"""
    # For now, just return success - in a real implementation this would save to database
    return {"success": True, "status": "created", "card_id": 1}

if __name__ == "__main__":
    print("Starting Magic Card Scanner test server...")
    print("Server will be available at: http://localhost:8000")
    print("Test endpoint: http://localhost:8000/test")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info") 