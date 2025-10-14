"""
Google Sheets Integration

Handles authentication and writing data to Google Sheets.
"""

import os
import json
from typing import List, Any, Optional
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class SheetsWriter:
    """Write data to Google Sheets"""

    def __init__(
        self,
        spreadsheet_id: str,
        credentials_json: Optional[str] = None,
        credentials_file: Optional[str] = None
    ):
        """
        Initialize Sheets writer

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            credentials_json: Service account JSON as string (from env var)
            credentials_file: Path to credentials JSON file
        """
        self.spreadsheet_id = spreadsheet_id
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets']

        # Authenticate
        self.service = self._authenticate(credentials_json, credentials_file)

    def _authenticate(self, credentials_json: Optional[str], credentials_file: Optional[str]):
        """Authenticate with Google Sheets API"""

        creds = None

        # Try service account from JSON string (environment variable)
        if credentials_json:
            try:
                creds_data = json.loads(credentials_json)
                creds = service_account.Credentials.from_service_account_info(
                    creds_data,
                    scopes=self.scopes
                )
                print("✓ Authenticated with Google Sheets (service account from env)")
            except Exception as e:
                print(f"Warning: Could not parse credentials JSON: {e}")

        # Try service account from file
        elif credentials_file and os.path.exists(credentials_file):
            try:
                creds = service_account.Credentials.from_service_account_file(
                    credentials_file,
                    scopes=self.scopes
                )
                print("✓ Authenticated with Google Sheets (service account from file)")
            except Exception as e:
                print(f"Warning: Could not load credentials file: {e}")

        # Try OAuth token (for local development)
        elif os.path.exists('token.json'):
            try:
                creds = Credentials.from_authorized_user_file('token.json', self.scopes)
                print("✓ Authenticated with Google Sheets (OAuth token)")
            except Exception as e:
                print(f"Warning: Could not load OAuth token: {e}")

        if not creds:
            raise Exception(
                "No valid Google credentials found. Please provide:\n"
                "  - GOOGLE_CREDENTIALS_JSON environment variable (service account JSON), or\n"
                "  - credentials.json file (service account), or\n"
                "  - token.json file (OAuth)"
            )

        return build('sheets', 'v4', credentials=creds)

    def append_row(
        self,
        values: List[Any],
        range_name: str = "Sheet1!A:Z",
        value_input_option: str = "USER_ENTERED"
    ) -> dict:
        """
        Append a row to the spreadsheet

        Args:
            values: List of values to append as a row
            range_name: Sheet range (default: "Sheet1!A:Z")
            value_input_option: How to interpret values ("USER_ENTERED" or "RAW")

        Returns:
            API response dictionary
        """
        try:
            body = {
                'values': [values]
            }

            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body
            ).execute()

            print(f"✓ Appended row to {range_name}")
            return result

        except HttpError as error:
            print(f"✗ Error appending to sheet: {error}")
            raise

    def append_rows(
        self,
        rows: List[List[Any]],
        range_name: str = "Sheet1!A:Z",
        value_input_option: str = "USER_ENTERED"
    ) -> dict:
        """
        Append multiple rows to the spreadsheet

        Args:
            rows: List of rows (each row is a list of values)
            range_name: Sheet range (default: "Sheet1!A:Z")
            value_input_option: How to interpret values

        Returns:
            API response dictionary
        """
        try:
            body = {
                'values': rows
            }

            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body
            ).execute()

            print(f"✓ Appended {len(rows)} rows to {range_name}")
            return result

        except HttpError as error:
            print(f"✗ Error appending to sheet: {error}")
            raise

    def read_range(self, range_name: str = "Sheet1!A:Z") -> List[List[Any]]:
        """
        Read values from a range

        Args:
            range_name: Sheet range to read

        Returns:
            List of rows
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()

            values = result.get('values', [])
            print(f"✓ Read {len(values)} rows from {range_name}")
            return values

        except HttpError as error:
            print(f"✗ Error reading from sheet: {error}")
            raise

    def create_sheet(self, sheet_name: str) -> dict:
        """
        Create a new sheet (tab) in the spreadsheet

        Args:
            sheet_name: Name for the new sheet

        Returns:
            API response dictionary
        """
        try:
            body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }]
            }

            result = self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()

            print(f"✓ Created sheet: {sheet_name}")
            return result

        except HttpError as error:
            print(f"✗ Error creating sheet: {error}")
            raise

    def setup_header_row(
        self,
        headers: List[str],
        range_name: str = "Sheet1!A1:Z1"
    ):
        """
        Set up header row (will overwrite if exists)

        Args:
            headers: List of header names
            range_name: Range for headers
        """
        try:
            body = {
                'values': [headers]
            }

            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption="RAW",
                body=body
            ).execute()

            print(f"✓ Set up header row: {headers}")

        except HttpError as error:
            print(f"✗ Error setting up headers: {error}")
            raise


def get_sheets_writer_from_env() -> SheetsWriter:
    """
    Create SheetsWriter from environment variables

    Environment variables:
        SPREADSHEET_ID: Required
        GOOGLE_CREDENTIALS_JSON: Optional (service account JSON as string)

    Returns:
        SheetsWriter instance
    """
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")

    if not spreadsheet_id:
        raise Exception("SPREADSHEET_ID environment variable is required")

    return SheetsWriter(
        spreadsheet_id=spreadsheet_id,
        credentials_json=credentials_json,
        credentials_file="credentials.json"
    )


if __name__ == "__main__":
    """Test Sheets integration"""
    from dotenv import load_dotenv
    from datetime import datetime

    load_dotenv()

    print("Testing Google Sheets integration...\n")

    try:
        writer = get_sheets_writer_from_env()

        # Test writing a row
        test_row = [
            datetime.now().isoformat(),
            "TEST-CONTRACT-123",
            "Test Customer",
            "555-1234",
            "test@example.com",
            "123 Test St",
            "1000.00",
            "12/01/2024",
            "SUCCESS"
        ]

        print(f"Writing test row: {test_row}\n")
        result = writer.append_row(test_row)

        print(f"\n✓ Test successful!")
        print(f"Updates: {result.get('updates')}")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
