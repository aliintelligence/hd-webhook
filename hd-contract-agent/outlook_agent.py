#!/usr/bin/env python3
"""
HD Contract Outlook Agent

Monitors Outlook inbox for HD contract emails, extracts PDF attachments,
parses contract data, and writes to Google Sheets.

Usage:
    python outlook_agent.py                    # Run once
    python outlook_agent.py --loop             # Run continuously
    python outlook_agent.py --setup-headers    # Setup sheet headers
"""

import os
import sys
import time
import base64
import argparse
import requests
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

# Import our modules
from graph_auth import get_graph_token_from_env
from pdf_parser import parse_hd_contract
from sheets_writer import SheetsWriter
from sales_rep_router import SalesRepRouter


class OutlookContractAgent:
    """Agent that processes HD contracts from Outlook"""

    def __init__(
        self,
        search_query: str = 'subject:"HD contract"',
        dest_range: str = "Sheet1!A:Z",
        mark_as_read: bool = False
    ):
        """
        Initialize the agent

        Args:
            search_query: Microsoft Graph search query for emails
            dest_range: Target range in Google Sheet
            mark_as_read: Whether to mark processed emails as read
        """
        self.search_query = search_query
        self.dest_range = dest_range
        self.mark_as_read = mark_as_read

        print("=" * 80)
        print("HD CONTRACT OUTLOOK AGENT")
        print("=" * 80)
        print(f"Search query: {search_query}")
        print(f"Destination: {dest_range}")
        print(f"Mark as read: {mark_as_read}")
        print("=" * 80 + "\n")

        # Get authentication tokens
        print("Authenticating with Microsoft Graph...")
        self.graph_token = get_graph_token_from_env(use_interactive=False)
        print()

        # Initialize sales rep router
        print("Loading sales rep routing configuration...")
        self.sales_rep_router = SalesRepRouter()
        print(f"✓ Loaded {len(self.sales_rep_router.get_all_sales_reps())} sales rep mappings")
        print()

        # Get Google credentials (will create sheets writers on demand)
        self.google_creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if not self.google_creds_json:
            raise Exception("GOOGLE_CREDENTIALS_JSON environment variable is required")
        print("✓ Google credentials loaded")
        print()

    def search_emails(self) -> List[Dict[str, Any]]:
        """
        Search for emails matching the query

        Returns:
            List of email message objects
        """
        url = "https://graph.microsoft.com/v1.0/me/messages"
        headers = {
            "Authorization": f"Bearer {self.graph_token}",
            "Content-Type": "application/json"
        }

        # Use $search for subject/content search
        params = {
            "$search": f'"{self.search_query}"',
            "$select": "id,subject,from,receivedDateTime,hasAttachments",
            "$orderby": "receivedDateTime DESC",
            "$top": 50
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            messages = data.get("value", [])

            print(f"✓ Found {len(messages)} matching email(s)")
            return messages

        except requests.exceptions.RequestException as e:
            print(f"✗ Error searching emails: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return []

    def get_attachments(self, message_id: str) -> List[Dict[str, Any]]:
        """
        Get attachments for a message

        Args:
            message_id: Message ID

        Returns:
            List of attachment objects
        """
        url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments"
        headers = {
            "Authorization": f"Bearer {self.graph_token}"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            attachments = data.get("value", [])

            return attachments

        except requests.exceptions.RequestException as e:
            print(f"✗ Error getting attachments: {e}")
            return []

    def download_attachment_bytes(self, message_id: str, attachment_id: str) -> bytes:
        """
        Download attachment content

        Args:
            message_id: Message ID
            attachment_id: Attachment ID

        Returns:
            Attachment content as bytes
        """
        # For file attachments, content is in contentBytes (base64)
        url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments/{attachment_id}"
        headers = {
            "Authorization": f"Bearer {self.graph_token}"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            attachment = response.json()

            # Decode base64 content
            content_bytes = base64.b64decode(attachment.get("contentBytes", ""))
            return content_bytes

        except Exception as e:
            print(f"✗ Error downloading attachment: {e}")
            return b""

    def mark_email_as_read(self, message_id: str):
        """
        Mark email as read

        Args:
            message_id: Message ID
        """
        url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}"
        headers = {
            "Authorization": f"Bearer {self.graph_token}",
            "Content-Type": "application/json"
        }
        body = {
            "isRead": True
        }

        try:
            response = requests.patch(url, headers=headers, json=body)
            response.raise_for_status()
            print("  ✓ Marked email as read")

        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error marking email as read: {e}")

    def process_email(self, message: Dict[str, Any]) -> int:
        """
        Process a single email and its attachments

        Args:
            message: Email message object

        Returns:
            Number of contracts processed
        """
        message_id = message.get("id")
        subject = message.get("subject", "No Subject")
        from_email = message.get("from", {}).get("emailAddress", {}).get("address", "Unknown")
        received = message.get("receivedDateTime", "")

        print(f"\n📧 Processing email:")
        print(f"   Subject: {subject}")
        print(f"   From: {from_email}")
        print(f"   Received: {received}")

        if not message.get("hasAttachments"):
            print("   ⚠ No attachments found")
            return 0

        # Get attachments
        attachments = self.get_attachments(message_id)
        pdf_count = 0

        for attachment in attachments:
            attachment_id = attachment.get("id")
            attachment_name = attachment.get("name", "")

            # Only process PDF files
            if not attachment_name.lower().endswith('.pdf'):
                print(f"   ⊘ Skipping non-PDF: {attachment_name}")
                continue

            print(f"   📄 Processing PDF: {attachment_name}")

            # Download PDF content
            pdf_bytes = self.download_attachment_bytes(message_id, attachment_id)

            if not pdf_bytes:
                print("   ✗ Failed to download attachment")
                continue

            # Parse PDF
            parsed_data = parse_hd_contract(pdf_bytes)

            if not parsed_data.get("success"):
                print(f"   ✗ Failed to parse PDF: {parsed_data.get('error')}")
                continue

            # Get sales rep and route to correct spreadsheet
            sales_rep = parsed_data.get("sales_rep")
            spreadsheet_id = self.sales_rep_router.get_spreadsheet_id(sales_rep)

            if not spreadsheet_id:
                print(f"   ✗ No spreadsheet found for sales rep: {sales_rep}")
                continue

            # Format for Sheets
            row_data = [
                datetime.now().isoformat(),
                parsed_data.get("contract_number", ""),
                parsed_data.get("sales_rep", ""),
                parsed_data.get("customer_name", ""),
                parsed_data.get("phone", ""),
                parsed_data.get("email", ""),
                parsed_data.get("address", ""),
                parsed_data.get("total_amount", ""),
                parsed_data.get("date", ""),
                attachment_name,
                subject,
                from_email,
            ]

            # Write to Sheets
            try:
                # Create sheets writer for this specific spreadsheet
                sheets_writer = SheetsWriter(
                    spreadsheet_id=spreadsheet_id,
                    credentials_json=self.google_creds_json
                )
                sheets_writer.append_row(row_data, self.dest_range)
                print(f"   ✓ Wrote contract to sheet: {parsed_data.get('contract_number')} (Sales Rep: {sales_rep})")
                pdf_count += 1

            except Exception as e:
                print(f"   ✗ Failed to write to sheet: {e}")

        # Mark email as read if configured
        if self.mark_as_read and pdf_count > 0:
            self.mark_email_as_read(message_id)

        return pdf_count

    def run_once(self) -> Dict[str, int]:
        """
        Run the agent once

        Returns:
            Statistics dictionary
        """
        print("\n🔍 Searching for HD contract emails...\n")

        messages = self.search_emails()

        stats = {
            "emails_found": len(messages),
            "emails_processed": 0,
            "contracts_extracted": 0
        }

        for message in messages:
            contracts = self.process_email(message)
            if contracts > 0:
                stats["emails_processed"] += 1
                stats["contracts_extracted"] += contracts

        return stats

    def run_loop(self, interval_seconds: int = 300):
        """
        Run the agent continuously in a loop

        Args:
            interval_seconds: Time to wait between runs (default: 300 = 5 minutes)
        """
        print(f"\n🔄 Running in loop mode (checking every {interval_seconds} seconds)")
        print("Press Ctrl+C to stop\n")

        iteration = 0

        try:
            while True:
                iteration += 1
                print(f"\n{'=' * 80}")
                print(f"ITERATION {iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'=' * 80}")

                stats = self.run_once()

                print(f"\n📊 Statistics:")
                print(f"   Emails found: {stats['emails_found']}")
                print(f"   Emails processed: {stats['emails_processed']}")
                print(f"   Contracts extracted: {stats['contracts_extracted']}")

                print(f"\n⏳ Waiting {interval_seconds} seconds until next check...")
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("\n\n🛑 Agent stopped by user")

    def setup_headers(self):
        """Setup header row in all sales rep spreadsheets"""
        headers = [
            "Processed At",
            "Contract Number",
            "Sales Rep",
            "Customer Name",
            "Phone",
            "Email",
            "Address",
            "Total Amount",
            "Contract Date",
            "Attachment Name",
            "Email Subject",
            "Email From"
        ]

        print(f"Setting up headers for {len(self.sales_rep_router.get_all_sales_reps())} sales rep spreadsheets...")

        # Setup headers for each sales rep's spreadsheet
        for sales_rep in self.sales_rep_router.get_all_sales_reps():
            spreadsheet_id = self.sales_rep_router.get_spreadsheet_id(sales_rep)
            if spreadsheet_id:
                try:
                    sheets_writer = SheetsWriter(
                        spreadsheet_id=spreadsheet_id,
                        credentials_json=self.google_creds_json
                    )
                    sheets_writer.setup_header_row(headers, "Sheet1!A1:L1")
                    print(f"✓ {sales_rep}: Headers configured")
                except Exception as e:
                    print(f"✗ {sales_rep}: Failed to setup headers - {e}")

        print("\n✓ Headers configured for all spreadsheets!")


def main():
    """Main entry point"""
    # Load environment variables
    load_dotenv()

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='HD Contract Outlook Agent')
    parser.add_argument('--loop', action='store_true', help='Run continuously')
    parser.add_argument('--interval', type=int, default=300, help='Loop interval in seconds (default: 300)')
    parser.add_argument('--setup-headers', action='store_true', help='Setup spreadsheet headers')
    parser.add_argument('--search', type=str, help='Custom search query')
    parser.add_argument('--range', type=str, default='Sheet1!A:Z', help='Target sheet range')
    parser.add_argument('--mark-read', action='store_true', help='Mark processed emails as read')

    args = parser.parse_args()

    # Get configuration from environment or arguments
    search_query = args.search or os.getenv("SEARCH_QUERY", 'subject:"HD contract"')
    mark_as_read = args.mark_read or os.getenv("MARK_AS_READ", "false").lower() == "true"

    try:
        # Initialize agent
        agent = OutlookContractAgent(
            search_query=search_query,
            dest_range=args.range,
            mark_as_read=mark_as_read
        )

        # Setup headers if requested
        if args.setup_headers:
            agent.setup_headers()
            return

        # Run agent
        if args.loop:
            agent.run_loop(interval_seconds=args.interval)
        else:
            stats = agent.run_once()

            print(f"\n{'=' * 80}")
            print("FINAL STATISTICS")
            print(f"{'=' * 80}")
            print(f"Emails found: {stats['emails_found']}")
            print(f"Emails processed: {stats['emails_processed']}")
            print(f"Contracts extracted: {stats['contracts_extracted']}")
            print(f"{'=' * 80}\n")

    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
