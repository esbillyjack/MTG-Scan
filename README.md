# Magic Card Scanner

An AI-powered web application that identifies Magic: The Gathering cards from photos and tracks their prices.

## Features

- **AI Card Recognition**: Upload photos and automatically identify MTG cards
- **Database Tracking**: Store identified cards with counts and timestamps
- **Price Integration**: Real-time price lookup from multiple sources
- **Modern Web UI**: Drag-and-drop photo upload with responsive design
- **Card Gallery**: Browse all identified cards with statistics

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML/CSS/JavaScript with modern UI
- **Database**: SQLite with SQLAlchemy ORM
- **AI**: OpenAI Vision API for card recognition
- **Price API**: Scryfall API for card data and prices
- **Image Processing**: Pillow for image optimization

## Project Structure

```
magic-card-scanner/
├── backend/
│   ├── app.py              # FastAPI application
│   ├── models.py           # Database models
│   ├── ai_processor.py     # AI card recognition
│   ├── price_api.py        # Price lookup integration
│   └── database.py         # Database setup
├── frontend/
│   ├── index.html          # Main web interface
│   ├── styles.css          # Styling
│   └── script.js           # Frontend logic
├── uploads/                # Temporary image storage
├── requirements.txt         # Python dependencies
└── README.md              # This file
```

## Setup Instructions

1. **Install Dependencies**:
   ```bash
   cd experiments/projects/magic-card-scanner
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Create `.env` file with:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ```

3. **Run the Application**:
   ```bash
   python backend/app.py
   ```

4. **Access the Web Interface**:
   Open http://localhost:8000 in your browser

## Usage

1. **Upload Photos**: Drag and drop or click to upload photos containing Magic cards
2. **AI Processing**: The system will identify all cards in the image
3. **View Results**: See identified cards with current prices and database counts
4. **Browse Database**: View all previously identified cards with statistics

## API Endpoints

- `POST /upload` - Upload and process images
- `GET /cards` - Get all cards in database
- `GET /cards/{card_id}` - Get specific card details
- `POST /cards/{card_id}/increment` - Increment card count

## Future Enhancements

- Bulk upload support
- Card condition assessment
- Collection value tracking
- Export functionality
- Mobile app version 