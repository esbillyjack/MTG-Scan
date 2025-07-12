from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import os
import shutil
from datetime import datetime
import aiofiles

from database import get_db, init_db, Card
from ai_processor import CardRecognitionAI
from price_api import ScryfallAPI

# Initialize FastAPI app
app = FastAPI(title="Magic Card Scanner", version="1.0.0")

# Create uploads directory
os.makedirs("uploads", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Initialize database
init_db()

# Initialize AI processor
try:
    ai_processor = CardRecognitionAI()
except ValueError as e:
    print(f"Warning: AI processor not available: {e}")
    ai_processor = None

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    async with aiofiles.open("frontend/index.html", mode="r") as f:
        content = await f.read()
    return HTMLResponse(content=content)

@app.post("/upload")
async def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and process an image to identify Magic cards"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save uploaded file
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Process image with AI
        if ai_processor is None:
            raise HTTPException(status_code=500, detail="AI processor not available")
        
        identified_cards = ai_processor.process_image(file_path)
        
        # Process each identified card
        results = []
        for card_info in identified_cards:
            card_name = card_info['name']
            
            # Get card data from Scryfall
            card_data = ScryfallAPI.get_card_data(card_name)
            
            if card_data:
                # Check if card exists in database
                existing_card = db.query(Card).filter(Card.name == card_name).first()
                
                if existing_card:
                    # Update existing card
                    existing_card.count += 1
                    existing_card.last_seen = datetime.utcnow()
                    existing_card.price_usd = card_data['price_usd']
                    existing_card.price_eur = card_data['price_eur']
                    existing_card.price_tix = card_data['price_tix']
                    db.commit()
                    
                    results.append({
                        "name": existing_card.name,
                        "set_name": existing_card.set_name,
                        "price_usd": existing_card.price_usd,
                        "price_eur": existing_card.price_eur,
                        "count": existing_card.count,
                        "status": "updated"
                    })
                else:
                    # Create new card
                    new_card = Card(
                        name=card_data['name'],
                        set_code=card_data['set_code'],
                        set_name=card_data['set_name'],
                        collector_number=card_data['collector_number'],
                        rarity=card_data['rarity'],
                        mana_cost=card_data['mana_cost'],
                        type_line=card_data['type_line'],
                        oracle_text=card_data['oracle_text'],
                        flavor_text=card_data['flavor_text'],
                        power=card_data['power'],
                        toughness=card_data['toughness'],
                        colors=card_data['colors'],
                        image_url=card_data['image_url'],
                        price_usd=card_data['price_usd'],
                        price_eur=card_data['price_eur'],
                        price_tix=card_data['price_tix'],
                        count=1
                    )
                    db.add(new_card)
                    db.commit()
                    
                    results.append({
                        "name": new_card.name,
                        "set_name": new_card.set_name,
                        "price_usd": new_card.price_usd,
                        "price_eur": new_card.price_eur,
                        "count": new_card.count,
                        "status": "new"
                    })
            else:
                # Card not found in Scryfall
                results.append({
                    "name": card_name,
                    "set_name": "",
                    "price_usd": 0.0,
                    "price_eur": 0.0,
                    "count": 0,
                    "status": "not_found",
                    "error": "Card not found in database"
                })
        
        # Clean up uploaded file
        os.remove(file_path)
        
        return {
            "success": True,
            "cards_found": len(identified_cards),
            "cards_processed": len(results),
            "results": results
        }
        
    except Exception as e:
        # Clean up uploaded file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/cards")
async def get_cards(db: Session = Depends(get_db)):
    """Get all cards in the database"""
    cards = db.query(Card).order_by(Card.name).all()
    
    return {
        "total_cards": len(cards),
        "cards": [
            {
                "id": card.id,
                "name": card.name,
                "set_name": card.set_name,
                "rarity": card.rarity,
                "price_usd": card.price_usd,
                "price_eur": card.price_eur,
                "price_tix": card.price_tix,
                "count": card.count,
                "first_seen": card.first_seen.isoformat() if card.first_seen else None,
                "last_seen": card.last_seen.isoformat() if card.last_seen else None,
                "image_url": card.image_url
            }
            for card in cards
        ]
    }

@app.get("/cards/{card_id}")
async def get_card(card_id: int, db: Session = Depends(get_db)):
    """Get specific card details"""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    return {
        "id": card.id,
        "name": card.name,
        "set_code": card.set_code,
        "set_name": card.set_name,
        "collector_number": card.collector_number,
        "rarity": card.rarity,
        "mana_cost": card.mana_cost,
        "type_line": card.type_line,
        "oracle_text": card.oracle_text,
        "flavor_text": card.flavor_text,
        "power": card.power,
        "toughness": card.toughness,
        "colors": card.colors,
        "image_url": card.image_url,
        "price_usd": card.price_usd,
        "price_eur": card.price_eur,
        "price_tix": card.price_tix,
        "count": card.count,
        "first_seen": card.first_seen.isoformat() if card.first_seen else None,
        "last_seen": card.last_seen.isoformat() if card.last_seen else None
    }

@app.post("/cards/{card_id}/increment")
async def increment_card(card_id: int, db: Session = Depends(get_db)):
    """Increment the count for a specific card"""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    card.count += 1
    card.last_seen = datetime.utcnow()
    db.commit()
    
    return {"success": True, "new_count": card.count}

@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get database statistics"""
    total_cards = db.query(Card).count()
    total_count = db.query(Card).with_entities(db.func.sum(Card.count)).scalar() or 0
    total_value_usd = db.query(Card).with_entities(db.func.sum(Card.price_usd * Card.count)).scalar() or 0
    total_value_eur = db.query(Card).with_entities(db.func.sum(Card.price_eur * Card.count)).scalar() or 0
    
    return {
        "total_unique_cards": total_cards,
        "total_card_count": total_count,
        "total_value_usd": round(total_value_usd, 2),
        "total_value_eur": round(total_value_eur, 2)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 