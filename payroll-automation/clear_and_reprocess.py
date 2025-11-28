"""
Clear main spreadsheet and re-process all contracts with improved parser
"""
import os
from dotenv import load_dotenv
from sheets_updater import SheetsUpdater
from config import MAIN_SHEET_HEADERS

load_dotenv()

def main():
    updater = SheetsUpdater()
    main_sheet_id = os.getenv('MAIN_SPREADSHEET_ID')
    
    print("="*60)
    print("CLEARING MAIN SPREADSHEET")
    print("="*60)
    
    # Clear all data except headers
    try:
        # Delete all rows after row 1 (headers)
        updater.service.spreadsheets().values().clear(
            spreadsheetId=main_sheet_id,
            range='A2:Z10000',
        ).execute()
        
        print("✓ Cleared all data rows from main spreadsheet")
        print(f"\nView spreadsheet: https://docs.google.com/spreadsheets/d/{main_sheet_id}")
        print("\nNow run: python3 process_all_contracts.py")
        
    except Exception as e:
        print(f"✗ Error clearing spreadsheet: {e}")

if __name__ == "__main__":
    main()
