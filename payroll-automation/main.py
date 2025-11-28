"""
Main Payroll Automation Script
Orchestrates the entire contract processing workflow
"""

import os
import time
import tempfile
from dotenv import load_dotenv
from pathlib import Path

from drive_monitor import DriveMonitor
from hybrid_parser import parse_contract_hybrid
from name_matcher import match_rep_name
from sheets_updater import SheetsUpdater
from config import MAIN_SHEET_HEADERS, BACKUP_SHEET_HEADERS

# Load environment variables
load_dotenv()


class PayrollAutomation:
    """Main automation orchestrator"""

    def __init__(self):
        self.drive_folder_id = os.getenv('DRIVE_FOLDER_ID', '115Pg2idzGItjkxamjwV5jP4UFExrmcHL')
        self.main_sheet_id = os.getenv('MAIN_SPREADSHEET_ID')
        self.backup_sheet_id = os.getenv('BACKUP_SPREADSHEET_ID')
        self.check_interval = int(os.getenv('CHECK_INTERVAL', 300))

        self.drive_monitor = DriveMonitor(self.drive_folder_id)
        self.sheets_updater = SheetsUpdater()

        # Initialize spreadsheets if needed
        self._initialize_spreadsheets()

    def _initialize_spreadsheets(self):
        """Create main and backup spreadsheets if they don't exist"""
        # Create main spreadsheet
        if not self.main_sheet_id:
            print("Creating main spreadsheet...")
            self.main_sheet_id = self.sheets_updater.create_spreadsheet(
                "Payroll Automation - Main Sheet",
                MAIN_SHEET_HEADERS
            )
            if self.main_sheet_id:
                print(f"Main spreadsheet created: https://docs.google.com/spreadsheets/d/{self.main_sheet_id}")
                self._update_env_file('MAIN_SPREADSHEET_ID', self.main_sheet_id)

        # Create backup spreadsheet
        if not self.backup_sheet_id:
            print("Creating backup spreadsheet...")
            self.backup_sheet_id = self.sheets_updater.create_spreadsheet(
                "Payroll Automation - Backup Sheet",
                BACKUP_SHEET_HEADERS
            )
            if self.backup_sheet_id:
                print(f"Backup spreadsheet created: https://docs.google.com/spreadsheets/d/{self.backup_sheet_id}")
                self._update_env_file('BACKUP_SPREADSHEET_ID', self.backup_sheet_id)

    def _update_env_file(self, key: str, value: str):
        """Update .env file with new key-value pair"""
        env_path = Path('.env')

        # Read existing content
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()
        else:
            lines = []

        # Update or add the key
        updated = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                updated = True
                break

        if not updated:
            lines.append(f"{key}={value}\n")

        # Write back
        with open(env_path, 'w') as f:
            f.writelines(lines)

    def process_contract(self, file_info: dict):
        """
        Process a single contract file

        Args:
            file_info: File metadata from Google Drive
        """
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
            print("Downloading contract from Google Drive...")
            if not self.drive_monitor.download_file(file_id, tmp_path):
                print(f"Failed to download {file_name}")
                return

            # Parse the contract with AI + Regex hybrid
            print("Parsing contract with AI...")
            contract_data = parse_contract_hybrid(tmp_path)

            print("\nExtracted data:")
            for key, value in contract_data.items():
                print(f"  {key:20s}: {value}")

            # Get contract link
            contract_link = self.drive_monitor.get_file_link(file_id)

            # Match sales rep
            sales_rep_name = contract_data.get('sales_rep', '')
            matched_name, rep_sheet_id, confidence = match_rep_name(sales_rep_name)

            # Update spreadsheets
            if matched_name and rep_sheet_id:
                print(f"\nMatched to rep: {matched_name} (confidence: {confidence}%)")

                # Update rep sheet
                print(f"Updating rep spreadsheet...")
                if self.sheets_updater.update_rep_sheet(rep_sheet_id, contract_data, contract_link):
                    print(f"✓ Rep sheet updated successfully")
                else:
                    print(f"✗ Failed to update rep sheet")

                # Update main sheet
                if self.main_sheet_id:
                    print(f"Updating main spreadsheet...")
                    if self.sheets_updater.update_main_sheet(
                        self.main_sheet_id, contract_data, matched_name, contract_link
                    ):
                        print(f"✓ Main sheet updated successfully")
                    else:
                        print(f"✗ Failed to update main sheet")

            else:
                print(f"\n⚠ No matching rep found for '{sales_rep_name}'")
                print(f"Adding to backup sheet...")

                # Update backup sheet
                if self.backup_sheet_id:
                    if self.sheets_updater.update_backup_sheet(
                        self.backup_sheet_id, contract_data, contract_link, sales_rep_name
                    ):
                        print(f"✓ Backup sheet updated successfully")
                    else:
                        print(f"✗ Failed to update backup sheet")

                # Still update main sheet with unmatched rep
                if self.main_sheet_id:
                    self.sheets_updater.update_main_sheet(
                        self.main_sheet_id, contract_data, sales_rep_name or "UNKNOWN", contract_link
                    )

            # Mark file as processed
            self.drive_monitor.mark_as_processed(file_id)
            print(f"\n✓ Contract processed successfully: {file_name}")

        except Exception as e:
            print(f"\n✗ Error processing contract: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def run(self):
        """Run the automation in continuous monitoring mode"""
        print("="*60)
        print("PAYROLL AUTOMATION STARTED")
        print("="*60)
        print(f"Drive Folder ID: {self.drive_folder_id}")
        print(f"Main Sheet: {self.main_sheet_id}")
        print(f"Backup Sheet: {self.backup_sheet_id}")
        print(f"Check Interval: {self.check_interval} seconds")
        print("="*60)

        while True:
            try:
                print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Checking for new contracts...")

                new_files = self.drive_monitor.get_new_contracts()

                if new_files:
                    print(f"Found {len(new_files)} new contract(s)")
                    for file in new_files:
                        self.process_contract(file)
                else:
                    print("No new contracts found")

                print(f"\nNext check in {self.check_interval} seconds...")
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                print("\n\nStopping automation...")
                break
            except Exception as e:
                print(f"\nError in main loop: {e}")
                import traceback
                traceback.print_exc()
                print(f"Retrying in {self.check_interval} seconds...")
                time.sleep(self.check_interval)

    def process_single_file(self, file_path: str):
        """
        Process a single contract file (for testing)

        Args:
            file_path: Path to the PDF contract file
        """
        print(f"Processing single file: {file_path}")

        try:
            # Parse the contract with AI + Regex hybrid
            contract_data = parse_contract_hybrid(file_path)

            print("\nExtracted data:")
            for key, value in contract_data.items():
                print(f"  {key:20s}: {value}")

            # Use file path as contract link for testing
            contract_link = f"file://{file_path}"

            # Match sales rep
            sales_rep_name = contract_data.get('sales_rep', '')
            matched_name, rep_sheet_id, confidence = match_rep_name(sales_rep_name)

            # Update spreadsheets
            if matched_name and rep_sheet_id:
                print(f"\nMatched to rep: {matched_name} (confidence: {confidence}%)")

                # Update rep sheet
                print(f"Updating rep spreadsheet...")
                if self.sheets_updater.update_rep_sheet(rep_sheet_id, contract_data, contract_link):
                    print(f"✓ Rep sheet updated successfully")
                else:
                    print(f"✗ Failed to update rep sheet")

                # Update main sheet
                if self.main_sheet_id:
                    print(f"Updating main spreadsheet...")
                    if self.sheets_updater.update_main_sheet(
                        self.main_sheet_id, contract_data, matched_name, contract_link
                    ):
                        print(f"✓ Main sheet updated successfully")
                    else:
                        print(f"✗ Failed to update main sheet")

            else:
                print(f"\n⚠ No matching rep found for '{sales_rep_name}'")
                print(f"Adding to backup sheet...")

                # Update backup sheet
                if self.backup_sheet_id:
                    if self.sheets_updater.update_backup_sheet(
                        self.backup_sheet_id, contract_data, contract_link, sales_rep_name
                    ):
                        print(f"✓ Backup sheet updated successfully")
                    else:
                        print(f"✗ Failed to update backup sheet")

                # Still update main sheet with unmatched rep
                if self.main_sheet_id:
                    print(f"Updating main spreadsheet...")
                    if self.sheets_updater.update_main_sheet(
                        self.main_sheet_id, contract_data, sales_rep_name or "UNKNOWN", contract_link
                    ):
                        print(f"✓ Main sheet updated successfully")
                    else:
                        print(f"✗ Failed to update main sheet")

            print(f"\n✓ Contract processed successfully!")

        except Exception as e:
            print(f"\n✗ Error processing contract: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point"""
    import sys

    if len(sys.argv) > 1:
        # Test mode: process a single file
        file_path = sys.argv[1]
        automation = PayrollAutomation()
        automation.process_single_file(file_path)
    else:
        # Normal mode: continuous monitoring
        automation = PayrollAutomation()
        automation.run()


if __name__ == "__main__":
    main()
