"""
Update main spreadsheet headers to include cost columns
"""
from sheets_updater import SheetsUpdater
from config import MAIN_SHEET_HEADERS
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    updater = SheetsUpdater()
    main_sheet_id = os.getenv('MAIN_SPREADSHEET_ID')
    
    if not main_sheet_id:
        print("No main spreadsheet ID found")
        return
    
    print(f"Updating headers in main spreadsheet: {main_sheet_id}")
    print(f"New headers: {MAIN_SHEET_HEADERS}")
    
    if updater.ensure_headers(main_sheet_id, MAIN_SHEET_HEADERS):
        print("✓ Headers updated successfully!")
        print(f"View spreadsheet: https://docs.google.com/spreadsheets/d/{main_sheet_id}")
    else:
        print("✗ Failed to update headers")

if __name__ == "__main__":
    main()
