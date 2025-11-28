"""
Google Sheets Updater Module
Updates individual rep spreadsheets, main spreadsheet, and backup sheet
"""

from typing import Dict, List, Optional
from google_auth import get_sheets_service
from config import REP_SHEET_HEADERS, MAIN_SHEET_HEADERS, BACKUP_SHEET_HEADERS
from equipment_cost_calculator import calculate_profit, format_currency


class SheetsUpdater:
    """Update Google Sheets with contract data"""

    def __init__(self):
        self.service = get_sheets_service()

    def get_all_values(self, spreadsheet_id: str, range_name: str) -> List[List]:
        """
        Get all values from a spreadsheet range

        Args:
            spreadsheet_id: Google Sheets ID
            range_name: Sheet name and range (e.g., 'Sheet1!A:Z')

        Returns:
            List of rows, each row is a list of values
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()

            return result.get('values', [])

        except Exception as e:
            print(f"Error reading from {spreadsheet_id}: {e}")
            return []

    def check_duplicate_by_lead_po(self, spreadsheet_id: str, lead_po: str, lead_po_column_index: int) -> bool:
        """
        Check if a deal with this Lead/PO number already exists

        Args:
            spreadsheet_id: Google Sheets ID
            lead_po: Lead/PO number to check
            lead_po_column_index: Column index where Lead/PO is stored (0-based)

        Returns:
            True if duplicate exists, False otherwise
        """
        if not lead_po or lead_po.strip() == '':
            return False

        try:
            # Use simple range that works with any sheet
            values = self.get_all_values(spreadsheet_id, 'A:Z')

            # Skip header row, check all data rows
            for row in values[1:]:  # Skip first row (headers)
                if len(row) > lead_po_column_index:
                    existing_lead_po = row[lead_po_column_index].strip()
                    if existing_lead_po == lead_po.strip():
                        print(f"Duplicate found: {lead_po} already exists in spreadsheet")
                        return True

        except Exception as e:
            print(f"Error checking for duplicates: {e}")

        return False

    def append_row(self, spreadsheet_id: str, range_name: str, values: List) -> bool:
        """
        Append a row to a spreadsheet

        Args:
            spreadsheet_id: Google Sheets ID
            range_name: Sheet name and range (e.g., 'Sheet1!A:Z')
            values: List of values to append

        Returns:
            True if successful, False otherwise
        """
        try:
            body = {'values': [values]}

            result = self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()

            print(f"Appended row to {spreadsheet_id}: {result.get('updates', {}).get('updatedRows', 0)} rows added")
            return True

        except Exception as e:
            print(f"Error appending row to {spreadsheet_id}: {e}")
            return False

    def update_rep_sheet(self, spreadsheet_id: str, contract_data: Dict, contract_link: str) -> bool:
        """
        Update individual rep spreadsheet with contract data

        Args:
            spreadsheet_id: Rep's spreadsheet ID
            contract_data: Extracted contract data
            contract_link: Link to the contract PDF in Drive

        Returns:
            True if successful
        """
        # Check for duplicate by phone number (column index 2)
        phone_number = contract_data.get('phone_number', '')
        if self.check_duplicate_by_lead_po(spreadsheet_id, phone_number, 2):
            print(f"Skipping duplicate: Phone {phone_number} already exists in rep sheet")
            return True  # Return True because it's not an error, just a duplicate

        # Prepare row data according to REP_SHEET_HEADERS format
        row = [
            contract_data.get('date', ''),
            contract_data.get('customer_name', ''),
            contract_data.get('phone_number', ''),
            contract_data.get('customer_address', ''),
            contract_data.get('equipment', ''),
            contract_data.get('sold_price', ''),
            '',  # Installed (empty)
            contract_data.get('fin_by', ''),
            'pending',  # Fin Status (default to pending)
            '',  # Comments (empty)
            '',  # Commission (empty)
            '',  # Date (commission date, empty)
            contract_link  # Contract PDF link
        ]

        # Append to the first sheet using simple range
        return self.append_row(spreadsheet_id, 'A:Z', row)

    def update_main_sheet(self, spreadsheet_id: str, contract_data: Dict, sales_rep: str, contract_link: str) -> bool:
        """
        Update main spreadsheet with contract data

        Args:
            spreadsheet_id: Main spreadsheet ID
            contract_data: Extracted contract data
            sales_rep: Sales rep name
            contract_link: Link to the contract PDF

        Returns:
            True if successful
        """
        # Check for duplicate by Lead/PO# (column index 8 - moved due to new cost columns)
        lead_po = contract_data.get('lead_po', '')
        if self.check_duplicate_by_lead_po(spreadsheet_id, lead_po, 8):
            print(f"Skipping duplicate: Lead/PO {lead_po} already exists in main sheet")
            return True  # Return True because it's not an error, just a duplicate

        # Calculate equipment cost and profit
        equipment_cost, marketing_fee, profit = calculate_profit(
            contract_data.get('sold_price', ''),
            contract_data.get('equipment', '')
        )

        # Prepare row data according to MAIN_SHEET_HEADERS format
        # Headers: Date, Sales Rep, Customer Name, Equipment, Sale Price, Equipment Cost, Marketing Fee (10%), Profit, Lead/PO#, Contract Link
        row = [
            contract_data.get('date', ''),
            sales_rep,
            contract_data.get('customer_name', ''),
            contract_data.get('equipment', ''),
            contract_data.get('sold_price', ''),
            format_currency(equipment_cost),
            format_currency(marketing_fee),
            format_currency(profit),
            contract_data.get('lead_po', ''),
            contract_link
        ]

        # Append to the first sheet using simple range
        return self.append_row(spreadsheet_id, 'A:Z', row)

    def update_backup_sheet(self, spreadsheet_id: str, contract_data: Dict, contract_link: str, sales_rep_name: str = "") -> bool:
        """
        Update backup spreadsheet with contract data (when rep cannot be matched)

        Args:
            spreadsheet_id: Backup spreadsheet ID
            contract_data: Extracted contract data
            contract_link: Link to the contract PDF
            sales_rep_name: Sales rep name from contract (unmatched)

        Returns:
            True if successful
        """
        # Check for duplicate by phone number (column index 2)
        phone_number = contract_data.get('phone_number', '')
        if self.check_duplicate_by_lead_po(spreadsheet_id, phone_number, 2):
            print(f"Skipping duplicate: Phone {phone_number} already exists in backup sheet")
            return True  # Return True because it's not an error, just a duplicate

        # Same as rep sheet but with an extra column for the unmatched rep name
        row = [
            contract_data.get('date', ''),
            contract_data.get('customer_name', ''),
            contract_data.get('phone_number', ''),
            contract_data.get('customer_address', ''),
            contract_data.get('equipment', ''),
            contract_data.get('sold_price', ''),
            '',  # Installed
            contract_data.get('fin_by', ''),
            'pending',  # Fin Status
            '',  # Comments
            '',  # Commission
            '',  # Date
            contract_link,  # Contract
            sales_rep_name  # Sales Rep Name (unmatched)
        ]

        # Append to the first sheet using simple range
        return self.append_row(spreadsheet_id, 'A:Z', row)

    def create_spreadsheet(self, title: str, headers: List[str]) -> Optional[str]:
        """
        Create a new spreadsheet with headers

        Args:
            title: Spreadsheet title
            headers: List of column headers

        Returns:
            Spreadsheet ID if successful, None otherwise
        """
        try:
            spreadsheet = {
                'properties': {'title': title},
                'sheets': [{
                    'properties': {'title': 'Sheet1'},
                    'data': [{
                        'startRow': 0,
                        'startColumn': 0,
                        'rowData': [{
                            'values': [{'userEnteredValue': {'stringValue': h}} for h in headers]
                        }]
                    }]
                }]
            }

            result = self.service.spreadsheets().create(body=spreadsheet).execute()
            spreadsheet_id = result['spreadsheetId']

            print(f"Created spreadsheet '{title}' with ID: {spreadsheet_id}")
            return spreadsheet_id

        except Exception as e:
            print(f"Error creating spreadsheet: {e}")
            return None

    def ensure_headers(self, spreadsheet_id: str, headers: List[str]) -> bool:
        """
        Ensure a spreadsheet has the correct headers

        Args:
            spreadsheet_id: Spreadsheet ID
            headers: Expected headers

        Returns:
            True if headers exist or were added successfully
        """
        try:
            # Check if headers exist
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!A1:Z1'
            ).execute()

            existing_headers = result.get('values', [[]])[0] if result.get('values') else []

            # If no headers or different headers, update them
            if not existing_headers or existing_headers != headers:
                body = {'values': [headers]}
                self.service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range='Sheet1!A1',
                    valueInputOption='USER_ENTERED',
                    body=body
                ).execute()
                print(f"Updated headers in {spreadsheet_id}")

            return True

        except Exception as e:
            print(f"Error ensuring headers in {spreadsheet_id}: {e}")
            return False


if __name__ == "__main__":
    # Test creating a spreadsheet
    updater = SheetsUpdater()

    # Example: Create main spreadsheet
    main_id = updater.create_spreadsheet("Payroll Main Sheet", MAIN_SHEET_HEADERS)
    if main_id:
        print(f"Main spreadsheet created: https://docs.google.com/spreadsheets/d/{main_id}")

    # Example: Create backup spreadsheet
    backup_id = updater.create_spreadsheet("Payroll Backup Sheet", BACKUP_SHEET_HEADERS)
    if backup_id:
        print(f"Backup spreadsheet created: https://docs.google.com/spreadsheets/d/{backup_id}")
