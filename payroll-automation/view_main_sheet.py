"""View data from main spreadsheet"""
from sheets_updater import SheetsUpdater
import os
from dotenv import load_dotenv

load_dotenv()

updater = SheetsUpdater()
main_sheet_id = os.getenv('MAIN_SPREADSHEET_ID')

print("Main Spreadsheet Data")
print("="*100)

values = updater.get_all_values(main_sheet_id, 'A:J')

# Print headers
if values:
    headers = values[0]
    print("  ".join(f"{h:15s}" for h in headers))
    print("-"*100)
    
    # Print data rows
    for row in values[1:]:
        # Pad row to match header length
        while len(row) < len(headers):
            row.append('')
        print("  ".join(f"{str(cell):15s}" for cell in row))

print("="*100)
print(f"\nView online: https://docs.google.com/spreadsheets/d/{main_sheet_id}")
