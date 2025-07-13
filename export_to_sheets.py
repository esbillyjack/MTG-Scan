#!/usr/bin/env python3
"""
Export Magic Card Scanner database to Google Sheets
"""

import os
import sys
from typing import List, Dict
import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
from sqlalchemy.orm import Session
from backend.database import get_db, Card

# If modifying these scopes, delete the token.pickle file
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_google_creds():
    """Get or refresh Google API credentials"""
    creds = None
    
    # Check if credentials.json exists
    if not os.path.exists('credentials.json'):
        print("ERROR: credentials.json not found!")
        print("Please follow these steps to set up Google Sheets API:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select an existing one")
        print("3. Enable the Google Sheets API")
        print("4. Create credentials (OAuth 2.0 Client ID)")
        print("5. Choose 'Desktop application' as the application type")
        print("6. Download the credentials and save them as 'credentials.json' in your project root")
        return None
    
    # The token.pickle file stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("Refreshing expired credentials...")
                creds.refresh(Request())
            except Exception as e:
                print(f"Failed to refresh credentials: {e}")
                creds = None
        
        if not creds:
            print("Starting OAuth flow...")
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                # Use run_local_server with specific parameters for better compatibility
                creds = flow.run_local_server(
                    port=8080,
                    prompt='consent',
                    authorization_prompt_message='Please visit this URL to authorize this application: {url}',
                    success_message='The auth flow is complete; you may close this window.',
                    open_browser=True
                )
                print("Authentication successful!")
            except Exception as e:
                print(f"Authentication failed: {e}")
                return None
            
        # Save the credentials for the next run
        try:
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
            print("Credentials saved successfully!")
        except Exception as e:
            print(f"Warning: Could not save credentials: {e}")
    
    return creds

def get_cards_data(db: Session) -> List[Dict]:
    """Get all active cards from the database"""
    cards = db.query(Card).filter(Card.deleted == False).all()
    
    card_data = []
    for card in cards:
        card_data.append({
            'Name': card.name,
            'Set': card.set_name,
            'Set Code': card.set_code,
            'Collector Number': card.collector_number,
            'Rarity': card.rarity,
            'Count': card.count,
            'Stack Count': card.stack_count,
            'Condition': card.condition,
            'Price USD': card.price_usd,
            'Price EUR': card.price_eur,
            'Price TIX': card.price_tix,
            'Type': card.type_line,
            'Mana Cost': card.mana_cost,
            'Colors': card.colors,
            'Notes': card.notes,
            'First Seen': card.first_seen.strftime('%Y-%m-%d %H:%M:%S') if card.first_seen else '',
            'Last Seen': card.last_seen.strftime('%Y-%m-%d %H:%M:%S') if card.last_seen else ''
        })
    
    return card_data

def create_or_update_sheet(creds, spreadsheet_id: str = None, title: str = None) -> str:
    """Create a new Google Sheet or update existing one"""
    try:
        service = build('sheets', 'v4', credentials=creds)
        
        if not spreadsheet_id:
            # Create a new spreadsheet
            spreadsheet_title = title or f'Magic Card Collection {pd.Timestamp.now().strftime("%Y-%m-%d")}'
            spreadsheet = {
                'properties': {
                    'title': spreadsheet_title
                }
            }
            print(f"Creating new spreadsheet: {spreadsheet_title}")
            spreadsheet = service.spreadsheets().create(body=spreadsheet).execute()
            spreadsheet_id = spreadsheet['spreadsheetId']
            print(f"Created spreadsheet with ID: {spreadsheet_id}")
        else:
            print(f"Updating existing spreadsheet: {spreadsheet_id}")
        
        # Get the card data
        db = next(get_db())
        cards_data = get_cards_data(db)
        
        if not cards_data:
            print("No cards found in database!")
            return spreadsheet_id
        
        print(f"Found {len(cards_data)} cards to export")
        
        # Convert to DataFrame for easier handling
        df = pd.DataFrame(cards_data)
        
        # Prepare the data for sheets
        values = [df.columns.tolist()] + df.values.tolist()
        
        # Update the sheet
        body = {
            'values': values
        }
        
        print("Clearing existing content...")
        # Clear existing content and update
        service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range='Sheet1'
        ).execute()
        
        print("Writing data to spreadsheet...")
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Sheet1',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        print(f"Updated {result.get('updatedCells')} cells")
        
        # Format the sheet
        print("Formatting spreadsheet...")
        requests = [
            {
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': 0,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': len(df.columns)
                    }
                }
            },
            {
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': 0,
                        'gridProperties': {
                            'frozenRowCount': 1
                        }
                    },
                    'fields': 'gridProperties.frozenRowCount'
                }
            }
        ]
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        
        print("Export completed successfully!")
        return spreadsheet_id
        
    except HttpError as error:
        print(f"An HTTP error occurred: {error}")
        return None
    except Exception as error:
        print(f"An error occurred: {error}")
        return None

def main():
    """Main function to handle export"""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Export Magic Card Collection to Google Sheets")
    parser.add_argument("--sheet-id", help="Existing Google Sheet ID to update")
    parser.add_argument("--filename", default="Magic Card Collection", help="Name for the spreadsheet")
    parser.add_argument("--include-timestamp", action="store_true", help="Include timestamp in filename")
    args = parser.parse_args()
    
    print("Starting Google Sheets export...")
    print("Authenticating with Google Sheets API...")
    
    creds = get_google_creds()
    
    if not creds:
        print("Failed to get Google credentials!")
        sys.exit(1)
    
    # Build the final filename
    final_filename = args.filename
    if args.include_timestamp:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        final_filename = f"{args.filename} {timestamp}"
    
    sheet_id = create_or_update_sheet(creds, args.sheet_id, final_filename)
    
    if sheet_id:
        spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        print(f"Spreadsheet URL: {spreadsheet_url}")
        
        # Try to open the spreadsheet in the default browser
        try:
            import webbrowser
            webbrowser.open(spreadsheet_url)
            print("Opened spreadsheet in browser")
        except Exception as e:
            print(f"Could not open browser: {e}")
            
    else:
        print("Failed to create/update spreadsheet!")
        sys.exit(1)

if __name__ == "__main__":
    main() 