"""
Google API Authentication Module
Handles OAuth2 authentication for Google Drive and Sheets APIs
"""

import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets'
]


def get_credentials():
    """
    Get Google API credentials using OAuth2

    Returns:
        Credentials object
    """
    creds = None
    token_path = 'token.pickle'
    credentials_path = 'credentials.json'

    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    f"'{credentials_path}' not found. Please download it from Google Cloud Console."
                )
            # Use console-based flow for WSL/headless environments
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            flow.redirect_uri = 'http://localhost'

            auth_url, _ = flow.authorization_url(prompt='consent')

            print("\n" + "="*60)
            print("GOOGLE AUTHORIZATION REQUIRED")
            print("="*60)
            print("\n1. Open this URL in your browser:\n")
            print(f"   {auth_url}\n")
            print("2. Log in and click 'Allow'")
            print("3. The page will try to redirect to localhost (this is normal!)")
            print("4. Copy the ENTIRE URL from your browser's address bar")
            print("   (It will look like: http://localhost:xxxxx/?code=...)")
            print("5. Paste it below\n")

            redirect_response = input("Paste the full redirect URL here: ").strip()

            # Extract the code from the URL
            import urllib.parse
            parsed = urllib.parse.urlparse(redirect_response)
            params = urllib.parse.parse_qs(parsed.query)
            code = params.get('code', [None])[0]

            if not code:
                raise ValueError("Could not extract authorization code from URL")

            flow.fetch_token(code=code)
            creds = flow.credentials

        # Save the credentials for the next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return creds


def get_drive_service():
    """Get Google Drive API service"""
    creds = get_credentials()
    return build('drive', 'v3', credentials=creds)


def get_sheets_service():
    """Get Google Sheets API service"""
    creds = get_credentials()
    return build('sheets', 'v4', credentials=creds)
