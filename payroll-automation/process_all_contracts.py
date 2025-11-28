"""
Process all contracts in Google Drive folder (one-time batch processing)
"""
import os
from dotenv import load_dotenv
from drive_monitor import DriveMonitor
from hybrid_parser import parse_contract_hybrid
from name_matcher import match_rep_name
from sheets_updater import SheetsUpdater
from config import MAIN_SHEET_HEADERS, BACKUP_SHEET_HEADERS
import tempfile

load_dotenv()

def main():
    drive_folder_id = os.getenv('DRIVE_FOLDER_ID', '115Pg2idzGItjkxamjwV5jP4UFExrmcHL')
    main_sheet_id = os.getenv('MAIN_SPREADSHEET_ID')
    backup_sheet_id = os.getenv('BACKUP_SPREADSHEET_ID')
    
    print("="*60)
    print("BATCH PROCESSING ALL CONTRACTS")
    print("="*60)
    print(f"Drive Folder: {drive_folder_id}")
    print(f"Main Sheet: {main_sheet_id}")
    print(f"Backup Sheet: {backup_sheet_id}")
    print("="*60)
    
    drive_monitor = DriveMonitor(drive_folder_id)
    sheets_updater = SheetsUpdater()
    
    # Get all PDF files in the folder
    print("\nFetching all contracts from Google Drive...")
    all_files = drive_monitor.service.files().list(
        q=f"'{drive_folder_id}' in parents and mimeType='application/pdf' and trashed=false",
        fields="files(id, name, webViewLink, modifiedTime)",
        orderBy="modifiedTime desc"
    ).execute().get('files', [])
    
    print(f"Found {len(all_files)} PDF files in Drive folder\n")
    
    processed_count = 0
    skipped_count = 0
    error_count = 0
    
    for file_info in all_files:
        file_id = file_info['id']
        file_name = file_info['name']
        
        print(f"\n{'='*60}")
        print(f"Processing: {file_name}")
        print(f"{'='*60}")
        
        # Download the PDF to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Download from Drive
            if not drive_monitor.download_file(file_id, tmp_path):
                print(f"✗ Failed to download {file_name}")
                error_count += 1
                continue
            
            # Parse the contract with AI + Regex hybrid
            contract_data = parse_contract_hybrid(tmp_path)
            
            print("\nExtracted data:")
            for key, value in contract_data.items():
                print(f"  {key:20s}: {value}")
            
            # Get contract link
            contract_link = drive_monitor.get_file_link(file_id)
            
            # Match sales rep
            sales_rep_name = contract_data.get('sales_rep', '')
            matched_name, rep_sheet_id, confidence = match_rep_name(sales_rep_name)
            
            # Track if any updates were made
            updated = False
            
            # Update spreadsheets
            if matched_name and rep_sheet_id:
                print(f"\nMatched to rep: {matched_name} (confidence: {confidence}%)")
                
                # Update rep sheet
                print(f"Updating rep spreadsheet...")
                if sheets_updater.update_rep_sheet(rep_sheet_id, contract_data, contract_link):
                    updated = True
                
                # Update main sheet
                if main_sheet_id:
                    print(f"Updating main spreadsheet...")
                    if sheets_updater.update_main_sheet(
                        main_sheet_id, contract_data, matched_name, contract_link
                    ):
                        updated = True
            
            else:
                print(f"\n⚠ No matching rep found for '{sales_rep_name}'")
                print(f"Adding to backup sheet...")
                
                # Update backup sheet
                if backup_sheet_id:
                    if sheets_updater.update_backup_sheet(
                        backup_sheet_id, contract_data, contract_link, sales_rep_name
                    ):
                        updated = True
                
                # Still update main sheet with unmatched rep
                if main_sheet_id:
                    print(f"Updating main spreadsheet...")
                    if sheets_updater.update_main_sheet(
                        main_sheet_id, contract_data, sales_rep_name or "UNKNOWN", contract_link
                    ):
                        updated = True
            
            if updated:
                processed_count += 1
                print(f"\n✓ Contract processed successfully!")
            else:
                skipped_count += 1
                print(f"\n⊘ Contract skipped (duplicate)")
        
        except Exception as e:
            print(f"\n✗ Error processing contract: {e}")
            import traceback
            traceback.print_exc()
            error_count += 1
        
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    # Summary
    print("\n" + "="*60)
    print("BATCH PROCESSING COMPLETE")
    print("="*60)
    print(f"Total files found:     {len(all_files)}")
    print(f"Successfully processed: {processed_count}")
    print(f"Skipped (duplicates):  {skipped_count}")
    print(f"Errors:                {error_count}")
    print("="*60)
    print(f"\nView main spreadsheet: https://docs.google.com/spreadsheets/d/{main_sheet_id}")
    print(f"View backup spreadsheet: https://docs.google.com/spreadsheets/d/{backup_sheet_id}")

if __name__ == "__main__":
    main()
