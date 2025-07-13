from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
import os
import shutil
from datetime import datetime
import aiofiles
import uuid

from database import get_db, init_db, Card, Scan, ScanImage, ScanResult
from ai_processor import CardRecognitionAI
from price_api import ScryfallAPI

# Initialize FastAPI app
app = FastAPI(title="Magic Card Scanner", version="1.0.0")

# Create uploads directory
os.makedirs("uploads", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")
# Mount uploads directory to serve scan images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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
                # Create duplicate group identifier
                duplicate_group = f"{card_data['name']}|{card_data.get('set_code', '')}|{card_data.get('collector_number', '')}"
                
                # Check if this card already exists in the database
                existing_cards = db.query(Card).filter(Card.duplicate_group == duplicate_group, Card.deleted == False).all()
                
                # Generate stack_id (use existing one if available, otherwise create new)
                if existing_cards:
                    stack_id = existing_cards[0].stack_id
                    # Update stack_count for all cards in this group
                    total_count = sum(card.count for card in existing_cards) + 1
                    for card in existing_cards:
                        card.stack_count = total_count
                else:
                    stack_id = str(uuid.uuid4())
                
                # Create new card entry (always create separate entry for duplicates)
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
                    count=1,
                    stack_count=len(existing_cards) + 1,
                    notes="",
                    condition="LP", # Changed default condition to LP
                    is_example=False,
                    duplicate_group=duplicate_group,
                    stack_id=stack_id
                )
                db.add(new_card)
                db.commit()
                
                results.append({
                    "name": new_card.name,
                    "set_name": new_card.set_name,
                    "price_usd": new_card.price_usd,
                    "price_eur": new_card.price_eur,
                    "count": new_card.count,
                    "status": "new",
                    "duplicate_group": new_card.duplicate_group
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


@app.post("/upload/scan")
async def upload_and_scan(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    """Upload files and create a scan session for the new workflow"""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Validate that at least one file is an image
    valid_files = [f for f in files if f.content_type and f.content_type.startswith("image/")]
    if not valid_files:
        raise HTTPException(status_code=400, detail="No valid image files provided")
    
    try:
        # Step 1: Create a new scan session
        new_scan = Scan(status="PENDING", notes="Scan initiated from upload")
        db.add(new_scan)
        db.commit()
        db.refresh(new_scan)
        
        # Step 2: Upload files to the scan
        uploaded_images = []
        for file in valid_files:
            # Generate unique filename
            file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
            unique_filename = f"scan_{new_scan.id}_{uuid.uuid4()}{file_extension}"
            file_path = f"uploads/{unique_filename}"
            
            # Save the file
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Create scan image record
            scan_image = ScanImage(
                scan_id=new_scan.id,
                filename=unique_filename,
                original_filename=file.filename or "unknown",
                file_path=file_path
            )
            db.add(scan_image)
            uploaded_images.append({
                "filename": unique_filename,
                "original_filename": file.filename,
                "size": len(content)
            })
        
        # Update scan totals
        new_scan.total_images = len(uploaded_images)
        db.commit()
        
        return {
            "success": True,
            "scan_id": new_scan.id,
            "status": new_scan.status,
            "total_images": new_scan.total_images,
            "uploaded_images": uploaded_images,
            "message": "Scan created and ready for processing"
        }
        
    except Exception as e:
        # Clean up any uploaded files on error
        for img in uploaded_images:
            try:
                if os.path.exists(f"uploads/{img['filename']}"):
                    os.remove(f"uploads/{img['filename']}")
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Error creating scan: {str(e)}")


@app.get("/cards")
async def get_cards(db: Session = Depends(get_db), view_mode: str = "individual"):
    """
    Get all cards in the database
    view_mode: "individual" (show all cards) or "stacked" (group duplicates)
    """
    if view_mode == "stacked":
        # Group cards by duplicate_group and return aggregated data
        cards = db.query(Card).filter(Card.deleted == False).order_by(Card.name).all()
        
        # Group by duplicate_group
        grouped_cards = {}
        for card in cards:
            group_key = card.duplicate_group or f"{card.name}|{card.set_code}|{card.collector_number}"
            if group_key not in grouped_cards:
                grouped_cards[group_key] = {
                    "stack_id": card.stack_id,
                    "name": card.name,
                    "set_name": card.set_name,
                    "set_code": card.set_code,
                    "collector_number": card.collector_number,
                    "rarity": card.rarity,
                    "mana_cost": card.mana_cost,
                    "type_line": card.type_line,
                    "oracle_text": card.oracle_text,
                    "flavor_text": card.flavor_text,
                    "power": card.power,
                    "toughness": card.toughness,
                    "colors": card.colors,
                    "price_usd": card.price_usd,
                    "price_eur": card.price_eur,
                    "price_tix": card.price_tix,
                    "count": card.count,  # Add individual card count
                    "stack_count": 0,  # Will sum all counts
                    "total_cards": 0,  # Number of individual card entries
                    "first_seen": card.first_seen.isoformat() if card.first_seen else None,
                    "last_seen": card.last_seen.isoformat() if card.last_seen else None,
                    "image_url": card.image_url,
                    "duplicate_group": card.duplicate_group,
                    "is_example": card.is_example,
                    "duplicates": []
                }
            
            grouped_cards[group_key]["stack_count"] += card.count
            grouped_cards[group_key]["total_cards"] += 1
            grouped_cards[group_key]["duplicates"].append({
                "id": card.id,
                "count": card.count,
                "condition": card.condition,
                "notes": card.notes,
                "is_example": card.is_example,
                "added_method": card.added_method or "LEGACY",
                "first_seen": card.first_seen.isoformat() if card.first_seen else None,
                "last_seen": card.last_seen.isoformat() if card.last_seen else None
            })
        
        return {
            "view_mode": "stacked",
            "total_stacks": len(grouped_cards),
            "cards": list(grouped_cards.values())
        }
    else:
        # Return individual cards
        cards = db.query(Card).filter(Card.deleted == False).order_by(Card.name).all()
        
        return {
            "view_mode": "individual",
            "total_cards": len(cards),
            "cards": [
                {
                    "id": card.id,
                    "name": card.name,
                    "set_name": card.set_name,
                    "set_code": card.set_code,
                    "collector_number": card.collector_number,
                    "rarity": card.rarity,
                    "mana_cost": card.mana_cost,
                    "type_line": card.type_line,
                    "oracle_text": card.oracle_text,
                    "flavor_text": card.flavor_text,
                    "power": card.power,
                    "toughness": card.toughness,
                    "colors": card.colors,
                    "price_usd": card.price_usd,
                    "price_eur": card.price_eur,
                    "price_tix": card.price_tix,
                    "count": card.count,
                    "stack_count": card.stack_count,
                    "stack_id": card.stack_id,
                    "first_seen": card.first_seen.isoformat() if card.first_seen else None,
                    "last_seen": card.last_seen.isoformat() if card.last_seen else None,
                    "image_url": card.image_url,
                    "notes": card.notes,
                    "condition": card.condition,
                    "is_example": card.is_example,
                    "duplicate_group": card.duplicate_group,
                    "added_method": card.added_method or "LEGACY"
                }
                for card in cards
            ]
        }

@app.get("/cards/{card_id}")
async def get_card(card_id: int, db: Session = Depends(get_db)):
    """Get specific card details"""
    card = db.query(Card).filter(Card.id == card_id, Card.deleted == False).first()
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
        "notes": card.notes,
        "condition": card.condition,
        "is_example": card.is_example,
        "duplicate_group": card.duplicate_group,
        "first_seen": card.first_seen.isoformat() if card.first_seen else None,
        "last_seen": card.last_seen.isoformat() if card.last_seen else None
    }

@app.put("/cards/{card_id}")
async def update_card(card_id: int, card_data: dict, db: Session = Depends(get_db)):
    """Update card details"""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # Update allowed fields
    if 'notes' in card_data:
        card.notes = card_data['notes']
    if 'condition' in card_data:
        card.condition = card_data['condition']
    if 'is_example' in card_data:
        card.is_example = card_data['is_example']
    if 'count' in card_data:
        card.count = card_data['count']
    
    db.commit()
    return {"success": True, "card_id": card.id}

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

@app.post("/cards")
async def add_card(card_data: dict, db: Session = Depends(get_db)):
    """Add a new card to the database"""
    try:
        # Create duplicate group identifier
        duplicate_group = f"{card_data['name']}|{card_data.get('set_code', '')}|{card_data.get('collector_number', '')}"
        
        # Create new card (always create separate entry)
        new_card = Card(
            name=card_data['name'],
            set_code=card_data.get('set_code', ''),
            set_name=card_data.get('set_name', ''),
            collector_number=card_data.get('collector_number', ''),
            rarity=card_data.get('rarity', ''),
            mana_cost=card_data.get('mana_cost', ''),
            type_line=card_data.get('type_line', ''),
            oracle_text=card_data.get('oracle_text', ''),
            flavor_text=card_data.get('flavor_text', ''),
            power=card_data.get('power', ''),
            toughness=card_data.get('toughness', ''),
            colors=card_data.get('colors', ''),
            image_url=card_data.get('image_url', ''),
            price_usd=card_data.get('price_usd', 0.0),
            price_eur=card_data.get('price_eur', 0.0),
            price_tix=card_data.get('price_tix', 0.0),
            count=card_data.get('count', 1),
            notes=card_data.get('notes', ''),
            condition=card_data.get('condition', 'LP'),
            is_example=card_data.get('is_example', False),
            duplicate_group=duplicate_group,
            first_seen=datetime.fromisoformat(card_data.get('first_seen', datetime.utcnow().isoformat())),
            last_seen=datetime.fromisoformat(card_data.get('last_seen', datetime.utcnow().isoformat()))
        )
        db.add(new_card)
        db.commit()
        return {"success": True, "status": "created", "card_id": new_card.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding card: {str(e)}")

@app.delete("/cards/{card_id}")
async def delete_card(card_id: int, db: Session = Depends(get_db)):
    """Soft delete a specific card"""
    card = db.query(Card).filter(Card.id == card_id, Card.deleted == False).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # Soft delete - just mark as deleted
    card.deleted = True
    card.deleted_at = datetime.utcnow()
    db.commit()
    return {"success": True, "card_id": card_id}

@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get database statistics"""
    # Filter out deleted cards for total statistics
    total_cards = db.query(Card).filter(Card.deleted == False).count()
    total_count = db.query(Card).filter(Card.deleted == False).with_entities(func.sum(Card.count)).scalar() or 0
    total_value_usd = db.query(Card).filter(Card.deleted == False).with_entities(func.sum(Card.price_usd * Card.count)).scalar() or 0
    total_value_eur = db.query(Card).filter(Card.deleted == False).with_entities(func.sum(Card.price_eur * Card.count)).scalar() or 0
    
    # Filter out example cards AND deleted cards for owned statistics
    owned_cards = db.query(Card).filter(Card.is_example == False, Card.deleted == False).count()
    owned_count = db.query(Card).filter(Card.is_example == False, Card.deleted == False).with_entities(func.sum(Card.count)).scalar() or 0
    owned_value_usd = db.query(Card).filter(Card.is_example == False, Card.deleted == False).with_entities(func.sum(Card.price_usd * Card.count)).scalar() or 0
    owned_value_eur = db.query(Card).filter(Card.is_example == False, Card.deleted == False).with_entities(func.sum(Card.price_eur * Card.count)).scalar() or 0
    
    return {
        "total_unique_cards": total_cards,
        "total_card_count": total_count,
        "total_value_usd": round(total_value_usd, 2),
        "total_value_eur": round(total_value_eur, 2),
        "owned_unique_cards": owned_cards,
        "owned_card_count": owned_count,
        "owned_value_usd": round(owned_value_usd, 2),
        "owned_value_eur": round(owned_value_eur, 2)
    }


# New Scan Management Endpoints

@app.post("/scan/start")
async def start_scan(db: Session = Depends(get_db)):
    """Create a new scan session"""
    new_scan = Scan(status="PENDING", notes="New scan session")
    db.add(new_scan)
    db.commit()
    db.refresh(new_scan)
    
    return {
        "success": True,
        "scan_id": new_scan.id,
        "status": new_scan.status,
        "created_at": new_scan.created_at.isoformat()
    }


@app.post("/scan/{scan_id}/upload")
async def upload_scan_images(scan_id: int, files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    """Upload images to a scan session"""
    # Verify scan exists and is in valid state
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if scan.status not in ["PENDING", "PROCESSING"]:
        raise HTTPException(status_code=400, detail="Scan is not in a state that accepts uploads")
    
    uploaded_images = []
    
    for file in files:
        if not file.content_type.startswith("image/"):
            continue  # Skip non-image files
            
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
        unique_filename = f"scan_{scan_id}_{uuid.uuid4()}{file_extension}"
        file_path = f"uploads/{unique_filename}"
        
        # Save the file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create scan image record
        scan_image = ScanImage(
            scan_id=scan_id,
            filename=unique_filename,
            original_filename=file.filename or "unknown",
            file_path=file_path
        )
        db.add(scan_image)
        uploaded_images.append({
            "filename": unique_filename,
            "original_filename": file.filename,
            "size": len(content)
        })
    
    # Update scan totals
    scan.total_images = db.query(ScanImage).filter(ScanImage.scan_id == scan_id).count()
    db.commit()
    
    return {
        "success": True,
        "scan_id": scan_id,
        "uploaded_images": uploaded_images,
        "total_images": scan.total_images
    }


@app.post("/scan/{scan_id}/process")
async def process_scan(scan_id: int, db: Session = Depends(get_db)):
    """Start AI processing of uploaded images"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
        
    if scan.status != "PENDING":
        raise HTTPException(status_code=400, detail="Scan is not ready for processing")
    
    # Update scan status
    scan.status = "PROCESSING"
    db.commit()
    
    try:
        # Get all images for this scan
        scan_images = db.query(ScanImage).filter(ScanImage.scan_id == scan_id).all()
        
        total_cards_found = 0
        processed_images = 0
        
        for scan_image in scan_images:
            try:
                # Process image with AI
                if ai_processor:
                    card_results = ai_processor.process_image(scan_image.file_path)
                    
                    # Create scan results for each identified card
                    for card_data in card_results:
                        # Use enhanced Scryfall search with AI set information
                        ai_set_info = card_data.get('set', '') or card_data.get('set_symbol_description', '')
                        scryfall_data = ScryfallAPI.get_card_data(card_data['name'], ai_set_info)
                        
                        # Update confidence with Scryfall data
                        if scryfall_data:
                            enhanced_card = ai_processor.update_confidence_with_scryfall(card_data, scryfall_data)
                        else:
                            enhanced_card = card_data
                            enhanced_card['scryfall_matched'] = False
                            enhanced_card['confidence_score'] = ai_processor._parse_confidence(card_data.get('confidence', 'medium'))
                        
                        # Create scan result
                        import json
                        scan_result = ScanResult(
                            scan_id=scan_id,
                            scan_image_id=scan_image.id,
                            card_name=enhanced_card['name'],
                            set_code=scryfall_data.get('set_code', '') if scryfall_data else enhanced_card.get('set', ''),
                            set_name=scryfall_data.get('set_name', '') if scryfall_data else '',
                            collector_number=scryfall_data.get('collector_number', '') if scryfall_data else enhanced_card.get('collector_number', ''),
                            confidence_score=enhanced_card.get('confidence_score', 0.0),
                            status="PENDING",
                            card_data=json.dumps(scryfall_data) if scryfall_data else json.dumps(enhanced_card)
                        )
                        db.add(scan_result)
                        total_cards_found += 1
                    
                    # Update scan image
                    scan_image.cards_found = len(card_results)
                    scan_image.processed_at = datetime.utcnow()
                    
                else:
                    scan_image.processing_error = "AI processor not available"
                
                processed_images += 1
                
            except Exception as e:
                scan_image.processing_error = str(e)
        
        # Update scan with results
        scan.processed_images = processed_images
        scan.total_cards_found = total_cards_found
        
        # Set status to READY_FOR_REVIEW even if no cards found (for user review of scan quality)
        scan.status = "READY_FOR_REVIEW"
        scan.updated_at = datetime.utcnow()
        
        # Store a note about zero cards found
        if total_cards_found == 0:
            scan.notes = f"Scan completed with 0 cards found. Images stored for future review."
        
        db.commit()
        
        return {
            "success": True,
            "scan_id": scan_id,
            "status": scan.status,
            "processed_images": processed_images,
            "total_cards_found": total_cards_found
        }
        
    except Exception as e:
        # Mark scan as failed
        scan.status = "FAILED"
        scan.notes = f"Processing error: {str(e)}"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/scan/{scan_id}/status")
async def get_scan_status(scan_id: int, db: Session = Depends(get_db)):
    """Get current scan status and progress"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return {
        "scan_id": scan.id,
        "status": scan.status,
        "total_images": scan.total_images,
        "processed_images": scan.processed_images,
        "total_cards_found": scan.total_cards_found,
        "unknown_cards_count": scan.unknown_cards_count,
        "created_at": scan.created_at.isoformat(),
        "updated_at": scan.updated_at.isoformat() if scan.updated_at else None
    }


@app.get("/scan/{scan_id}/results")
async def get_scan_results(scan_id: int, db: Session = Depends(get_db)):
    """Get scan results for review"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Get all scan results with image info
    results = db.query(ScanResult, ScanImage).join(
        ScanImage, ScanResult.scan_image_id == ScanImage.id
    ).filter(ScanResult.scan_id == scan_id).all()
    
    scan_results = []
    for scan_result, scan_image in results:
        # Parse card data to make it available for the frontend
        card_data = None
        if scan_result.card_data:
            import json
            import ast
            try:
                # Try JSON parsing first
                card_data = json.loads(scan_result.card_data)
            except json.JSONDecodeError:
                try:
                    # If JSON fails, try to evaluate as Python literal
                    card_data = ast.literal_eval(scan_result.card_data)
                except (ValueError, SyntaxError):
                    # If both fail, use None
                    card_data = None
        
        scan_results.append({
            "id": scan_result.id,
            "card_name": scan_result.card_name,
            "set_code": scan_result.set_code,
            "set_name": scan_result.set_name,
            "confidence_score": scan_result.confidence_score,
            "status": scan_result.status,
            "image_filename": scan_image.filename,
            "requires_review": scan_result.confidence_score < 70,
            "created_at": scan_result.created_at.isoformat(),
            "card_data": card_data
        })
    
    return {
        "scan_id": scan_id,
        "scan_status": scan.status,
        "results": scan_results,
        "total_results": len(scan_results)
    }


@app.get("/scan/pending")
async def get_pending_scans(db: Session = Depends(get_db)):
    """Get all scans that need user review"""
    pending_scans = db.query(Scan).filter(
        Scan.status.in_(["READY_FOR_REVIEW", "PROCESSING"])
    ).order_by(Scan.created_at.desc()).all()
    
    return {
        "pending_scans": [
            {
                "id": scan.id,
                "status": scan.status,
                "total_images": scan.total_images,
                "total_cards_found": scan.total_cards_found,
                "created_at": scan.created_at.isoformat()
            }
            for scan in pending_scans
        ]
    }


@app.post("/scan/{scan_id}/accept")
async def accept_scan_results(scan_id: int, request_data: dict, db: Session = Depends(get_db)):
    """Accept specific scan results or all results"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    accept_all = request_data.get('accept_all', False)
    result_ids = request_data.get('result_ids', [])
    
    if accept_all:
        # Accept all pending results
        results_to_accept = db.query(ScanResult).filter(
            ScanResult.scan_id == scan_id,
            ScanResult.status == "PENDING"
        ).all()
    else:
        # Accept specific results
        if not result_ids:
            raise HTTPException(status_code=400, detail="No result IDs provided")
        results_to_accept = db.query(ScanResult).filter(
            ScanResult.scan_id == scan_id,
            ScanResult.id.in_(result_ids),
            ScanResult.status == "PENDING"
        ).all()
    
    accepted_count = 0
    for result in results_to_accept:
        result.status = "ACCEPTED"
        result.decided_at = datetime.utcnow()
        accepted_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "scan_id": scan_id,
        "accepted_count": accepted_count
    }


@app.post("/scan/{scan_id}/reject")
async def reject_scan_results(scan_id: int, request_data: dict, db: Session = Depends(get_db)):
    """Reject specific scan results"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    result_ids = request_data.get('result_ids', [])
    
    if not result_ids:
        raise HTTPException(status_code=400, detail="No result IDs provided")
    
    results_to_reject = db.query(ScanResult).filter(
        ScanResult.scan_id == scan_id,
        ScanResult.id.in_(result_ids),
        ScanResult.status == "PENDING"
    ).all()
    
    rejected_count = 0
    for result in results_to_reject:
        result.status = "REJECTED"
        result.decided_at = datetime.utcnow()
        rejected_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "scan_id": scan_id,
        "rejected_count": rejected_count
    }


@app.post("/scan/{scan_id}/commit")
async def commit_scan(scan_id: int, db: Session = Depends(get_db)):
    """Finalize scan by creating cards from accepted results"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Get accepted results
    accepted_results = db.query(ScanResult).filter(
        ScanResult.scan_id == scan_id,
        ScanResult.status == "ACCEPTED"
    ).all()
    
    if not accepted_results:
        raise HTTPException(status_code=400, detail="No accepted results to commit")
    
    created_cards = 0
    for result in accepted_results:
        try:
            # Parse card data - handle both JSON string and Python string representation
            import json
            import ast
            
            card_data = {}
            if result.card_data:
                try:
                    # Try JSON parsing first
                    card_data = json.loads(result.card_data)
                except json.JSONDecodeError:
                    try:
                        # If JSON fails, try to evaluate as Python literal
                        card_data = ast.literal_eval(result.card_data)
                    except (ValueError, SyntaxError):
                        # If both fail, use empty dict
                        card_data = {}
            
            # Create duplicate group identifier using set_name instead of set_code to handle API inconsistencies
            duplicate_group = f"{result.card_name}|{result.set_name}|{result.collector_number}"
            
            # Check for existing cards in this group
            existing_cards = db.query(Card).filter(Card.duplicate_group == duplicate_group, Card.deleted == False).all()
            
            # Generate stack_id
            if existing_cards:
                stack_id = existing_cards[0].stack_id
                total_count = sum(card.count for card in existing_cards) + 1
                for card in existing_cards:
                    card.stack_count = total_count
            else:
                stack_id = str(uuid.uuid4())
            
            # Create new card
            new_card = Card(
                name=result.card_name,
                set_code=result.set_code,
                set_name=result.set_name,
                collector_number=result.collector_number,
                rarity=card_data.get('rarity', ''),
                mana_cost=card_data.get('mana_cost', ''),
                type_line=card_data.get('type_line', ''),
                oracle_text=card_data.get('oracle_text', ''),
                flavor_text=card_data.get('flavor_text', ''),
                power=card_data.get('power', ''),
                toughness=card_data.get('toughness', ''),
                colors=card_data.get('colors', ''),
                image_url=card_data.get('image_url', ''),
                price_usd=card_data.get('price_usd', 0.0),
                price_eur=card_data.get('price_eur', 0.0),
                price_tix=card_data.get('price_tix', 0.0),
                count=1,
                stack_count=len(existing_cards) + 1,
                notes=f"Imported from scan {scan_id}",
                condition="LP",
                is_example=False,
                duplicate_group=duplicate_group,
                stack_id=stack_id,
                scan_id=scan_id,
                scan_result_id=result.id,
                import_status="ACCEPTED",
                added_method="SCANNED"
            )
            db.add(new_card)
            created_cards += 1
            
        except Exception as e:
            print(f"Error creating card from result {result.id}: {e}")
            continue
    
    # Update scan status
    scan.status = "COMPLETED"
    scan.updated_at = datetime.utcnow()
    scan.notes = f"Completed: {created_cards} cards imported"
    
    db.commit()
    
    return {
        "success": True,
        "scan_id": scan_id,
        "status": "COMPLETED",
        "cards_created": created_cards
    }


@app.delete("/scan/{scan_id}")
async def cancel_scan(scan_id: int, db: Session = Depends(get_db)):
    """Cancel a scan and clean up files"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Get scan images for cleanup
    scan_images = db.query(ScanImage).filter(ScanImage.scan_id == scan_id).all()
    
    # Delete image files
    deleted_files = 0
    for scan_image in scan_images:
        try:
            if os.path.exists(scan_image.file_path):
                os.remove(scan_image.file_path)
                deleted_files += 1
        except Exception as e:
            print(f"Error deleting file {scan_image.file_path}: {e}")
    
    # Update scan status
    scan.status = "CANCELLED"
    scan.updated_at = datetime.utcnow()
    scan.notes = f"Cancelled by user. {deleted_files} files cleaned up."
    
    db.commit()
    
    return {
        "success": True,
        "scan_id": scan_id,
        "status": "CANCELLED",
        "files_deleted": deleted_files
    }


@app.post("/admin/populate-sets")
async def populate_missing_sets(db: Session = Depends(get_db)):
    """Populate missing set information for existing cards"""
    try:
        # Get cards with missing set information
        cards_to_update = db.query(Card).filter(
            Card.deleted == False,
            (Card.set_name.is_(None) | (Card.set_name == '') |
             Card.collector_number.is_(None) | (Card.collector_number == '') |
             Card.image_url.is_(None) | (Card.image_url == ''))
        ).all()
        
        if not cards_to_update:
            return {
                "success": True,
                "message": "All cards already have complete set information",
                "updated_count": 0
            }
        
        updated_count = 0
        for card in cards_to_update:
            try:
                # Get enhanced set data
                missing_data = ScryfallAPI.populate_missing_set_data(card.name, card.set_code)
                
                if missing_data:
                    # Update missing fields
                    if not card.set_name and missing_data.get('set_name'):
                        card.set_name = missing_data['set_name']
                    
                    if not card.collector_number and missing_data.get('collector_number'):
                        card.collector_number = missing_data['collector_number']
                    
                    if not card.image_url and missing_data.get('image_url'):
                        card.image_url = missing_data['image_url']
                    
                    if missing_data.get('rarity'):
                        card.rarity = missing_data['rarity']
                    
                    updated_count += 1
                
                # Be nice to the API
                if updated_count % 10 == 0:
                    db.commit()
                    
            except Exception as e:
                print(f"Error updating card {card.name}: {e}")
                continue
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Successfully populated set information for {updated_count} cards",
            "updated_count": updated_count,
            "total_processed": len(cards_to_update)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error populating sets: {str(e)}")


@app.get("/scan/{scan_id}/details")
async def get_scan_details(scan_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific scan"""
    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        # Get scan images
        scan_images = db.query(ScanImage).filter(ScanImage.scan_id == scan.id).all()
        images = []
        for img in scan_images:
            images.append({
                "filename": img.filename,
                "url": f"/{img.filename}"
            })
        
        # Get cards from this scan
        cards = db.query(Card).filter(Card.scan_id == scan.id, Card.deleted == False).all()
        card_list = []
        for card in cards:
            card_list.append({
                "name": card.name,
                "set_name": card.set_name,
                "condition": card.condition
            })
        
        return {
            "success": True,
            "scan": {
                "id": scan.id,
                "status": scan.status,
                "total_images": scan.total_images,
                "created_at": scan.created_at.isoformat() if scan.created_at else None,
                "images": images,
                "cards": card_list
            }
        }
        
    except Exception as e:
        print(f"Error getting scan details: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting scan details: {str(e)}")


@app.get("/scan/history")
async def get_scan_history(db: Session = Depends(get_db)):
    """Get all scan history with images and cards found"""
    try:
        # Get all scans ordered by newest first
        scans = db.query(Scan).order_by(Scan.created_at.desc()).all()
        
        scan_history = []
        for scan in scans:
            # Get scan images
            scan_images = db.query(ScanImage).filter(ScanImage.scan_id == scan.id).all()
            
            # Get cards created from this scan
            scan_cards = db.query(Card).filter(Card.scan_id == scan.id, Card.deleted == False).all()
            
            # Format images
            images = []
            for image in scan_images:
                images.append({
                    "filename": image.filename,
                    "original_filename": image.original_filename,
                    "file_path": image.file_path
                })
            
            # Format cards
            cards = []
            for card in scan_cards:
                cards.append({
                    "name": card.name,
                    "set_name": card.set_name,
                    "set_code": card.set_code,
                    "collector_number": card.collector_number,
                    "rarity": card.rarity,
                    "count": card.count
                })
            
            scan_data = {
                "id": scan.id,
                "status": scan.status,
                "total_images": scan.total_images,
                "cards_count": len(cards),
                "created_at": scan.created_at.isoformat() if scan.created_at else None,
                "updated_at": scan.updated_at.isoformat() if hasattr(scan, 'updated_at') and scan.updated_at else None,
                "images": images,
                "cards": cards
            }
            
            scan_history.append(scan_data)
        
        return {
            "success": True,
            "total_scans": len(scan_history),
            "scans": scan_history
        }
        
    except Exception as e:
        print(f"Error getting scan history: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting scan history: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 