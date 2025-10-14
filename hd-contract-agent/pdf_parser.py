"""
HD Contract PDF Parser

Extracts structured data from Home Depot contract PDFs using pdfplumber.
Customize the parsing logic based on your specific contract format.
"""

import io
import re
import pdfplumber
from typing import Dict, Optional, Any
from datetime import datetime


class HDContractParser:
    """Parse Home Depot contract PDFs and extract key information"""

    def __init__(self):
        """Initialize the parser with field patterns"""
        # Common patterns for extracting data from contracts
        self.patterns = {
            'contract_number': [
                r'Contract\s*#?\s*:?\s*([A-Z0-9\-]+)',
                r'Contract\s+Number\s*:?\s*([A-Z0-9\-]+)',
                r'F-?(\d{8,})',  # F-number pattern
            ],
            'sales_rep': [
                r'Sales\s+Rep(?:resentative)?\s*:?\s*([A-Z][a-zA-Z\s]+)',
                r'Rep(?:resentative)?\s*:?\s*([A-Z][a-zA-Z\s]+)',
                r'Agent\s*:?\s*([A-Z][a-zA-Z\s]+)',
                r'Salesperson\s*:?\s*([A-Z][a-zA-Z\s]+)',
                # Match names like "Angel Ruiz", "Luis Martinez Milan", etc.
                r'(?:Angel Ruiz|Alfredo Arguilles|Bryan Gonzalez|David Rodriguez|Daniel Chuecos|Daniel Carrero|Diego Toribio|Edgar Lantigua|Estefania Nieto|Evelyn Vides|Francisco Gonzalez|Geronimo Fernandez|Henry Velasco|Lisandra|Luis Martinez Milan|Marisol Medina|Maximiliano Mele|Michelet|Rachel Miranda|Rocny Rodriguez|Shayne Luque|Ulises Delgado|Yoan Bonet)',
            ],
            'customer_name': [
                r'Customer\s*Name\s*:?\s*([A-Z][a-zA-Z\s]+)',
                r'Name\s*:?\s*([A-Z][a-zA-Z\s]+)',
            ],
            'address': [
                r'Address\s*:?\s*(.+?)(?:\n|$)',
                r'Service\s+Address\s*:?\s*(.+?)(?:\n|$)',
            ],
            'phone': [
                r'Phone\s*:?\s*([\d\-\(\)\s]+)',
                r'Contact\s*:?\s*([\d\-\(\)\s]+)',
            ],
            'email': [
                r'Email\s*:?\s*([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})',
            ],
            'total_amount': [
                r'Total\s*:?\s*\$?\s*([\d,]+\.?\d*)',
                r'Amount\s*:?\s*\$?\s*([\d,]+\.?\d*)',
            ],
            'date': [
                r'Date\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                r'Contract\s+Date\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            ],
        }

    def parse_pdf_bytes(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Parse PDF from bytes

        Args:
            pdf_bytes: PDF file content as bytes

        Returns:
            Dictionary containing extracted contract data
        """
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            return self.parse_pdf(pdf_file)
        except Exception as e:
            print(f"✗ Error parsing PDF bytes: {e}")
            return {"error": str(e), "success": False}

    def parse_pdf(self, pdf_file: io.BytesIO) -> Dict[str, Any]:
        """
        Parse PDF and extract contract information

        Args:
            pdf_file: PDF file-like object

        Returns:
            Dictionary containing extracted data
        """
        extracted_data = {
            "success": True,
            "parsed_at": datetime.now().isoformat(),
            "contract_number": None,
            "sales_rep": None,
            "customer_name": None,
            "address": None,
            "phone": None,
            "email": None,
            "total_amount": None,
            "date": None,
            "raw_text": "",
        }

        try:
            with pdfplumber.open(pdf_file) as pdf:
                # Extract text from all pages
                all_text = ""
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    all_text += page_text + "\n"

                extracted_data["raw_text"] = all_text
                extracted_data["page_count"] = len(pdf.pages)

                # Extract structured fields using patterns
                for field_name, patterns in self.patterns.items():
                    value = self._extract_field(all_text, patterns)
                    if value:
                        extracted_data[field_name] = self._clean_value(field_name, value)

                # Additional extraction: Look for tables
                extracted_data["tables"] = self._extract_tables(pdf)

                print(f"✓ Successfully parsed PDF ({len(pdf.pages)} pages)")

                return extracted_data

        except Exception as e:
            print(f"✗ Error parsing PDF: {e}")
            extracted_data["success"] = False
            extracted_data["error"] = str(e)
            return extracted_data

    def _extract_field(self, text: str, patterns: list) -> Optional[str]:
        """
        Try to extract a field using multiple regex patterns

        Args:
            text: Text to search in
            patterns: List of regex patterns to try

        Returns:
            Extracted value or None
        """
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()
        return None

    def _clean_value(self, field_name: str, value: str) -> str:
        """
        Clean extracted values based on field type

        Args:
            field_name: Name of the field
            value: Raw extracted value

        Returns:
            Cleaned value
        """
        # Remove extra whitespace
        value = " ".join(value.split())

        # Field-specific cleaning
        if field_name == "phone":
            # Keep only digits and basic formatting
            value = re.sub(r'[^\d\-\(\)\s]', '', value)

        elif field_name == "total_amount":
            # Remove commas, keep decimals
            value = value.replace(',', '')

        elif field_name == "customer_name":
            # Title case
            value = value.title()

        elif field_name == "email":
            # Lowercase
            value = value.lower()

        return value

    def _extract_tables(self, pdf: Any) -> list:
        """
        Extract tables from PDF

        Args:
            pdf: pdfplumber PDF object

        Returns:
            List of tables (each table is a list of rows)
        """
        tables = []
        for page in pdf.pages:
            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)
        return tables

    def format_for_sheets(self, parsed_data: Dict[str, Any]) -> list:
        """
        Format parsed data as a row for Google Sheets

        Args:
            parsed_data: Dictionary from parse_pdf()

        Returns:
            List of values for a spreadsheet row
        """
        return [
            parsed_data.get("parsed_at", ""),
            parsed_data.get("contract_number", ""),
            parsed_data.get("sales_rep", ""),
            parsed_data.get("customer_name", ""),
            parsed_data.get("phone", ""),
            parsed_data.get("email", ""),
            parsed_data.get("address", ""),
            parsed_data.get("total_amount", ""),
            parsed_data.get("date", ""),
            parsed_data.get("success", False),
        ]


def parse_hd_contract(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Convenience function to parse HD contract PDF

    Args:
        pdf_bytes: PDF file content as bytes

    Returns:
        Dictionary containing extracted contract data
    """
    parser = HDContractParser()
    return parser.parse_pdf_bytes(pdf_bytes)


if __name__ == "__main__":
    """Test PDF parsing"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pdf_parser.py <pdf_file_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    print(f"Testing PDF parser with: {pdf_path}\n")

    try:
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        result = parse_hd_contract(pdf_bytes)

        print("\nExtracted Data:")
        print("=" * 60)
        for key, value in result.items():
            if key not in ["raw_text", "tables"]:  # Skip long fields
                print(f"{key:20s}: {value}")
        print("=" * 60)

    except Exception as e:
        print(f"✗ Error: {e}")
