"""
Google Drive Monitor Module
Monitors a Google Drive folder for new PDF contracts
"""

import os
import time
from typing import List, Dict
from googleapiclient.http import MediaIoBaseDownload
import io

from google_auth import get_drive_service


class DriveMonitor:
    """Monitor Google Drive folder for new contracts"""

    def __init__(self, folder_id: str, processed_file_path: str = 'processed_files.txt'):
        self.folder_id = folder_id
        self.processed_file_path = processed_file_path
        self.service = get_drive_service()
        self.processed_files = self._load_processed_files()

    def _load_processed_files(self) -> set:
        """Load the list of already processed file IDs"""
        if os.path.exists(self.processed_file_path):
            with open(self.processed_file_path, 'r') as f:
                return set(line.strip() for line in f)
        return set()

    def _save_processed_file(self, file_id: str):
        """Mark a file as processed"""
        self.processed_files.add(file_id)
        with open(self.processed_file_path, 'a') as f:
            f.write(f"{file_id}\n")

    def get_new_contracts(self) -> List[Dict]:
        """
        Get list of new PDF files in the monitored folder

        Returns:
            List of file metadata dictionaries
        """
        try:
            # Query for PDF files in the folder
            query = f"'{self.folder_id}' in parents and mimeType='application/pdf' and trashed=false"
            results = self.service.files().list(
                q=query,
                pageSize=100,
                fields="files(id, name, createdTime, webViewLink, webContentLink)"
            ).execute()

            files = results.get('files', [])

            # Filter out already processed files
            new_files = [f for f in files if f['id'] not in self.processed_files]

            return new_files

        except Exception as e:
            print(f"Error fetching files from Drive: {e}")
            return []

    def download_file(self, file_id: str, destination_path: str) -> bool:
        """
        Download a file from Google Drive

        Args:
            file_id: Google Drive file ID
            destination_path: Local path to save the file

        Returns:
            True if successful, False otherwise
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}%")

            # Write to file
            fh.seek(0)
            with open(destination_path, 'wb') as f:
                f.write(fh.read())

            return True

        except Exception as e:
            print(f"Error downloading file {file_id}: {e}")
            return False

    def mark_as_processed(self, file_id: str):
        """Mark a file as processed"""
        self._save_processed_file(file_id)

    def get_file_link(self, file_id: str) -> str:
        """Get the web view link for a file"""
        return f"https://drive.google.com/file/d/{file_id}/view"


def monitor_drive_folder(folder_id: str, check_interval: int = 300):
    """
    Continuously monitor a Drive folder for new contracts

    Args:
        folder_id: Google Drive folder ID to monitor
        check_interval: How often to check for new files (in seconds)
    """
    monitor = DriveMonitor(folder_id)

    print(f"Monitoring Drive folder: {folder_id}")
    print(f"Check interval: {check_interval} seconds")

    while True:
        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Checking for new contracts...")

        new_files = monitor.get_new_contracts()

        if new_files:
            print(f"Found {len(new_files)} new contract(s)")
            for file in new_files:
                print(f"  - {file['name']} (ID: {file['id']})")
        else:
            print("No new contracts found")

        time.sleep(check_interval)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        folder_id = sys.argv[1]
        monitor_drive_folder(folder_id)
    else:
        print("Usage: python drive_monitor.py <folder_id>")
