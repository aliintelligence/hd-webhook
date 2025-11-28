"""
PDF Parser for Home Depot Water Treatment Contracts
Extracts relevant information from signed contracts
"""

import re
import pdfplumber
from typing import Dict, Optional


class ContractParser:
    """Parse Home Depot water treatment contracts (English and Spanish)"""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.text = ""
        self.language = None  # Will be detected: 'en' or 'es'

    def extract_text(self) -> str:
        """Extract all text from PDF"""
        with pdfplumber.open(self.pdf_path) as pdf:
            self.text = "\n".join([page.extract_text() or "" for page in pdf.pages])
        self._detect_language()
        return self.text

    def _detect_language(self):
        """Detect if contract is in English or Spanish"""
        # Check for Spanish keywords
        spanish_keywords = ['Apellido del Cliente', 'Nombre del vendedor', 'Precio del Contrato']
        english_keywords = ['Customer Last Name', 'Salesperson Name', 'Contract Price']

        spanish_count = sum(1 for keyword in spanish_keywords if keyword in self.text)
        english_count = sum(1 for keyword in english_keywords if keyword in self.text)

        self.language = 'es' if spanish_count > english_count else 'en'

    def parse(self) -> Dict[str, str]:
        """
        Parse contract and extract all relevant fields
        Returns a dictionary with extracted data
        """
        if not self.text:
            self.extract_text()

        data = {
            "sales_rep": self._extract_sales_rep(),
            "customer_name": self._extract_customer_name(),
            "phone_number": self._extract_phone(),
            "customer_address": self._extract_address(),
            "equipment": self._extract_equipment(),
            "sold_price": self._extract_price(),
            "date": self._extract_date(),
            "lead_po": self._extract_lead_po(),
            "fin_by": self._extract_finance_company(),
        }

        return data

    def _extract_sales_rep(self) -> str:
        """Extract sales rep name (works for both English and Spanish)"""
        lines = self.text.split('\n')

        # Search keywords based on language
        if self.language == 'es':
            search_terms = ['Nombre del vendedor', 'vendedor']
        else:
            search_terms = ['Salesperson Name', 'Sales Person', 'Salesperson']

        # Known rep names to look for
        known_reps = [
            'Shayne Luque', 'Carlo Dalelio', 'Adriana Botero', 'Alessandro Crisci',
            'Bryan Gonzalez', 'David Rodriguez', 'Daniel Chuecos', 'Edgar Lantigua',
            'Ennio Zucchino', 'Fernando Falco', 'Facundo Alvarez', 'Estefania Nieto',
            'Henry Velasco', 'Hamelet Louis', 'Lisandra', 'Marisol Medina',
            'Rachel Miranda', 'Rocny Rodriguez', 'Romel Duran', 'Ulises Delgado',
            'Yoan Bonet'
        ]

        # First, try to find known rep names anywhere in the text
        for rep_name in known_reps:
            if rep_name in self.text:
                return rep_name

        # Try to find name near "Salesperson" marker
        for i, line in enumerate(lines[:100]):  # Search more lines
            if any(term in line for term in search_terms):
                # Skip if it's just the placeholder text
                if line.strip() in ['Salesperson Name', 'Sales Person Name', 'Nombre del vendedor']:
                    # Check lines above and below
                    search_range = list(range(max(0, i-3), i)) + list(range(i+1, min(i+6, len(lines))))
                else:
                    # Check same line and nearby lines
                    search_range = [i] + list(range(max(0, i-2), i)) + list(range(i+1, min(i+4, len(lines))))

                for j in search_range:
                    # Look for name pattern (First Last or First Middle Last)
                    name_match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b', lines[j])
                    if name_match:
                        name = name_match.group(1).strip()
                        # Filter out common non-name words
                        if name not in ['Salesperson Name', 'Customer Name', 'Customer Last', 'Customer First',
                                       'Last Name', 'First Name', 'Home Phone', 'Cell Phone', 'Work Phone',
                                       'Miami Water', 'Water Conditioning', 'Contract Price', 'Lead Po']:
                            # Verify it's a valid name (at least 2 words, each starting with capital)
                            words = name.split()
                            if len(words) >= 2 and all(word[0].isupper() for word in words):
                                return name

        return ""

    def _extract_customer_name(self) -> str:
        """Extract customer name (works for both English and Spanish)"""
        lines = self.text.split('\n')

        if self.language == 'es':
            # Spanish: "Apellido del Cliente" / "Nombre del Cliente"
            for i, line in enumerate(lines):
                if 'Apellido del Cliente' in line and 'Nombre del Cliente' in line:
                    # Customer name is on the previous line in format "LastName FirstName"
                    if i > 0:
                        prev_line = lines[i-1].strip()
                        parts = prev_line.split()
                        if len(parts) >= 2:
                            # Format: "Soler Dennis" → "Dennis Soler"
                            return f"{parts[1]} {parts[0]}"
        else:
            # English: "Customer Last Name" / "Customer First Name"
            for i, line in enumerate(lines):
                if 'Customer Last Name' in line and 'Customer First Name' in line:
                    # Name is on the previous line in format "LastName FirstName"
                    if i > 0:
                        prev_line = lines[i-1].strip()
                        parts = prev_line.split()
                        if len(parts) >= 2:
                            # Format: "Suarez Xiomara" → "Xiomara Suarez"
                            return f"{parts[1]} {parts[0]}"

        return ""

    def _extract_phone(self) -> str:
        """Extract customer phone number (works for both English and Spanish)"""
        lines = self.text.split('\n')

        # Look for phone markers based on language
        if self.language == 'es':
            phone_markers = ['Casa #', 'Trabajo #', 'Móvil #']
        else:
            phone_markers = ['Home Phone#', 'Work Phone#', 'Cell Phone#']

        # Find line with phone markers
        for i, line in enumerate(lines):
            if any(marker in line for marker in phone_markers):
                # In English, phone is often on PREVIOUS line, in Spanish it's AFTER
                search_range = range(max(0, i-2), min(i+3, len(lines)))

                for j in search_range:
                    # Match phone with or without dashes: 305-290-9033 or 3052909033
                    phone_match = re.search(r'(\d{3})[-\s]?(\d{3})[-\s]?(\d{4})', lines[j])
                    if phone_match:
                        phone = ''.join(phone_match.groups())
                        if phone != '3053636966':  # Exclude Miami Water and Air
                            return phone

        # Fallback: find any phone near customer email
        phone_match = re.search(r"(\d{3})[-\s]?(\d{3})[-\s]?(\d{4})\s+[a-z0-9.]+@[a-z]+\.com", self.text)
        if phone_match:
            phone = ''.join(phone_match.groups())
            if phone != '3053636966':
                return phone

        return ""

    def _extract_address(self) -> str:
        """Extract customer address (works for both English and Spanish)"""
        # Comprehensive address patterns
        address_patterns = [
            # Pattern: 16100 SW 102 CT Miami FL 33157
            r"(\d+\s+[A-Z]{1,2}\s+\d+\s+[A-Z]{2,3})\s+(\w+)\s+(FL)\s+(\d{5})",
            # Pattern: 117 NE 24th Terr Homestead FL 33033
            r"(\d+\s+[A-Z]{1,2}\s+\d+(?:st|nd|rd|th)\s+\w+)\s+(\w+)\s+(FL)\s+(\d{5})",
        ]

        for pattern in address_patterns:
            match = re.search(pattern, self.text)
            if match:
                street = match.group(1)
                city = match.group(2)
                state = match.group(3)
                zip_code = match.group(4)
                return f"{street}, {city}, {state} {zip_code}"

        # Line-by-line search
        lines = self.text.split('\n')
        for i, line in enumerate(lines):
            # Look for street address
            addr_match = re.search(r'(\d+\s+[A-Z]{1,2}\s+\d+(?:st|nd|rd|th)?\s+[A-Z]{2,3})\s', line)
            if addr_match:
                street = addr_match.group(1)
                # Look for city, state, zip on same or nearby lines
                for j in range(i, min(i+2, len(lines))):
                    city_match = re.search(r'(\w+)\s+(FL)\s+(\d{5})', lines[j])
                    if city_match:
                        return f"{street}, {city_match.group(1)}, {city_match.group(2)} {city_match.group(3)}"

        return ""

    def _extract_equipment(self) -> str:
        """Extract equipment information (works for both English and Spanish)"""

        # FIRST: Try flexible format (handles spaces, commas, dashes, periods, mixed case)
        # Examples: "Tc,QRs,ro,alk", "Ec5 qrs ro alk am cs", "TC - QRS - RO - CS", "EC5,QRs,ro,ALK,cs.am"
        equipment_patterns = [
            r"Modelo #\s+([A-Za-z0-9,\s\.\-]+?)(?:\n|Sistema)",  # Spanish
            r"Model #\s+([A-Za-z0-9,\s\.\-]+?)(?:\n|System)",   # English
        ]

        for pattern in equipment_patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                equipment_str = match.group(1).strip()

                # Split on ANY separator: comma, dash, period, or space
                # Use regex to split on any combination of these characters
                codes = re.split(r'[\s,\.\-]+', equipment_str)

                # Normalize: uppercase and filter
                valid_codes = []
                for code in codes:
                    code = code.strip().upper()
                    # Keep codes with 2+ characters
                    if len(code) >= 2:
                        valid_codes.append(code)

                if valid_codes:
                    return ' '.join(valid_codes)

        # SECOND: Try standard format patterns
        if self.language == 'es':
            # Spanish: "Sistema de acondicionamiento de agua"
            equipment_pattern = r"Sistema de acondicionamiento de agua\s+Ctd\s+\d+\s+Modelo #\s+([A-Z0-9\s]+)"
        else:
            # English: "Water Conditioning System"
            equipment_pattern = r"Water Conditioning System\s+Qty\s+\d+\s+Model #\s+([A-Z0-9\s]+)"

        match = re.search(equipment_pattern, self.text)
        if match:
            return match.group(1).strip()

        # Alternative pattern: Look for "Model #" or "Modelo #" followed by equipment codes
        model_patterns = [
            r"Model #\s+([A-Z0-9][A-Z0-9\s]+?)(?:\n|$|[A-Z][a-z])",
            r"Modelo #\s+([A-Z0-9][A-Z0-9\s]+?)(?:\n|$|[A-Z][a-z])",
        ]

        for pattern in model_patterns:
            match = re.search(pattern, self.text)
            if match:
                equipment = match.group(1).strip()
                # Filter out obvious non-equipment text
                if len(equipment) > 1 and not equipment.startswith('Miami'):
                    return equipment

        # Look for equipment codes in "Description" or "Equipment" section
        # Common patterns: EC5, TC, BCM, QRS, RO, ALK, AM, CS, UV, PFAS, etc.
        equipment_codes = []

        # Look specifically in the equipment/model section of the text
        # Find the section with "Model #" or equipment descriptions
        equipment_section = ""
        lines = self.text.split('\n')

        # Find equipment section (usually near "Model #" or "Water Conditioning")
        for i, line in enumerate(lines):
            if any(keyword in line.upper() for keyword in ['MODEL #', 'MODELO #', 'WATER CONDITIONING', 'ACONDICIONAMIENTO']):
                # Get surrounding lines (5 before and 15 after)
                start = max(0, i - 5)
                end = min(len(lines), i + 15)
                equipment_section = '\n'.join(lines[start:end])
                break

        # If no equipment section found, use whole text
        if not equipment_section:
            equipment_section = self.text

        # Search for equipment keywords with stricter patterns
        equipment_keywords = [
            r'\b(EC5|ECS|E\.C\.5|ES5)\b',
            r'\b(TC|TCM|T\.C\.)\b',  # Word boundaries prevent matching single T
            r'\b(BCM)\b',
            r'\b(QRS|Q\.R\.S)\b',
            r'\b(RO|R\.O\.)\b',  # Word boundaries prevent matching single R
            r'\b(ALK|ALKALINE)\b',
            r'\b(AM|AIRMASTER)\b',
            r'\b(CS|CLEAN START)\b',
            r'\b(UV|ULTRAVIOLET)\b',
            r'\b(PFAS)\b',
            r'\b(CAGE|REJA)\b',
            r'\b(BASE|STAND)\b',
            r'\b(HYD|HYDRO)\b',
            r'\b(OXY|OXYGEN)\b',
            r'\b(COOLER)\b',
        ]

        for keyword_pattern in equipment_keywords:
            matches = re.finditer(keyword_pattern, equipment_section, re.IGNORECASE)
            for match in matches:
                code = match.group(1).upper()
                # Normalize variations
                if code in ['ECS', 'E.C.5', 'ES5']:
                    code = 'EC5'
                elif code in ['T.C.', 'TCM']:
                    code = 'TC'
                elif code in ['Q.R.S']:
                    code = 'QRS'
                elif code in ['R.O.']:
                    code = 'RO'
                elif code == 'ALKALINE':
                    code = 'ALK'
                elif code == 'AIRMASTER':
                    code = 'AM'
                elif code in ['CLEAN START', 'CLEANSTART']:
                    code = 'CS'
                elif code in ['ULTRAVIOLET', 'UV LIGHT']:
                    code = 'UV'
                elif code == 'STAND':
                    code = 'BASE'
                elif code == 'REJA':
                    code = 'CAGE'
                elif code == 'HYDRO':
                    code = 'HYD'
                elif code == 'OXYGEN':
                    code = 'OXY'

                if code not in equipment_codes:
                    equipment_codes.append(code)

        if equipment_codes:
            return ' '.join(equipment_codes)

        return ""

    def _extract_price(self) -> str:
        """Extract sold price (works for both English and Spanish)"""
        if self.language == 'es':
            # Spanish: "Precio del Contrato"
            price_patterns = [
                r"Precio del Contrato:\s*\$\s*(\d+,?\d*)",
            ]
        else:
            # English: "Contract Price"
            price_patterns = [
                r"Contract Price:\s*\$\s*(\d+,?\d*)",
            ]

        for pattern in price_patterns:
            match = re.search(pattern, self.text)
            if match:
                price = match.group(1).replace(',', '')
                return f"${price}"

        return ""

    def _extract_date(self) -> str:
        """Extract contract date"""
        # Look for date in MM/DD/YYYY format
        date_pattern = r"(\d{1,2}/\d{1,2}/\d{4})"
        match = re.search(date_pattern, self.text)
        if match:
            return match.group(1)

        return ""

    def _extract_lead_po(self) -> str:
        """Extract Lead/PO number"""
        # Look for "Cliente potencial/ Orden de compra" or "Lead/PO#"
        po_patterns = [
            r"Lead/PO#\s+([A-Z0-9]+)",
            r"F(\d{8})",
            r"Cliente potencial[^\n]*?\n\s*([A-Z0-9]+)",
        ]

        for pattern in po_patterns:
            match = re.search(pattern, self.text)
            if match:
                return match.group(1) if len(match.groups()) == 1 else f"F{match.group(1)}"

        return ""

    def _extract_finance_company(self) -> str:
        """Extract financing company (works for both English and Spanish)"""
        if self.language == 'es':
            # Spanish: "Meta de Pago"
            fin_pattern = r"Meta de Pago:([A-Za-z]+)"
        else:
            # English: "Payment Method"
            fin_pattern = r"Payment Method:\s*([A-Za-z]+)"

        match = re.search(fin_pattern, self.text)
        if match:
            return match.group(1)

        return ""


def parse_contract(pdf_path: str) -> Dict[str, str]:
    """
    Convenience function to parse a contract PDF

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Dictionary containing extracted contract data
    """
    parser = ContractParser(pdf_path)
    return parser.parse()


if __name__ == "__main__":
    # Test with the sample contract
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        data = parse_contract(pdf_path)
        print("\nExtracted Contract Data:")
        print("-" * 50)
        for key, value in data.items():
            print(f"{key:20s}: {value}")
