"""
AI-Powered PDF Contract Parser
Uses Google Gemini to extract contract data with high accuracy
"""

import os
import base64
import json
from typing import Dict
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from config import EQUIPMENT_MAPPING

# Google Cloud Project settings
PROJECT_ID = "sales-ai-agent-478815"
LOCATION = "us-central1"


class AIContractParser:
    """Parse contracts using Google Gemini AI"""

    def __init__(self):
        """Initialize Gemini AI model"""
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        self.model = GenerativeModel("gemini-1.5-flash-002")

    def parse_contract(self, pdf_path: str) -> Dict[str, str]:
        """
        Parse contract PDF using AI

        Args:
            pdf_path: Path to the PDF contract file

        Returns:
            Dictionary with extracted contract data
        """
        # Read PDF file as base64
        with open(pdf_path, 'rb') as f:
            pdf_data = base64.b64encode(f.read()).decode('utf-8')

        # Create the prompt
        prompt = self._create_extraction_prompt()

        # Create PDF part
        pdf_part = Part.from_data(
            data=base64.b64decode(pdf_data),
            mime_type="application/pdf"
        )

        try:
            # Generate response
            response = self.model.generate_content(
                [prompt, pdf_part],
                generation_config={
                    "temperature": 0.1,  # Low temperature for consistent extraction
                    "max_output_tokens": 2048,
                }
            )

            # Parse JSON response
            result_text = response.text.strip()

            # Extract JSON from markdown code block if present
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            data = json.loads(result_text)

            # Normalize equipment codes
            if data.get('equipment'):
                data['equipment'] = self._normalize_equipment(data['equipment'])

            return data

        except Exception as e:
            print(f"AI parsing error: {e}")
            # Return empty data on error
            return {
                "sales_rep": "",
                "customer_name": "",
                "phone_number": "",
                "customer_address": "",
                "equipment": "",
                "sold_price": "",
                "date": "",
                "lead_po": "",
                "fin_by": ""
            }

    def _create_extraction_prompt(self) -> str:
        """Create the AI extraction prompt"""
        return """
You are a contract data extraction specialist. Extract the following information from this water treatment contract PDF.

**IMPORTANT INSTRUCTIONS:**
1. Extract data EXACTLY as it appears in the document
2. For sales rep name: Look for actual person names (NOT "Salesperson Name" placeholder)
3. For equipment: Extract ALL equipment codes and components listed
4. Return data as valid JSON only, no markdown formatting

**EQUIPMENT MAPPING GUIDE:**
Map any equipment text to these standardized codes:
- EC5, ECS, E.C.5, ES5 → EC5
- TC, TCM, T.C. → TC
- BCM → BCM
- HYD, Hydro → HYD
- QRS, Q.R.S, Quad → QRS
- AM, Airmaster → AM
- CS, Clean Start → CS
- UV, UV Light, Ultraviolet → UV
- ALK, Alkaline, Alk → ALK
- OXY, Oxygen → OXY
- RO, R.O., Reverse Osmosis → RO
- PFAS → PFAS
- Cage, Reja → CAGE
- Base, Stand → BASE
- Cooler → COOLER
- Portable Air → Portable Air
- Pump → PUMP
- Pressure Tank → Pressure Tank
- RO Pump → RO PUMP

**EXTRACT THESE FIELDS:**

1. **sales_rep**: The salesperson's name (first and last name)
   - Look near "Salesperson Name", "Nombre del vendedor", or "Sales Rep"
   - If you find "Salesperson Name" as placeholder text, look for an actual name nearby
   - Common names: Shayne Luque, Carlo Dalelio, Fernando Falco, etc.
   - If no actual name found, return empty string ""

2. **customer_name**: Customer's full name (First Last format)
   - Spanish contracts: Look for "Apellido del Cliente" / "Nombre del Cliente"
   - English contracts: Look for "Customer Last Name" / "Customer First Name"
   - Format as: FirstName LastName

3. **phone_number**: Customer's phone number (10 digits, no dashes)
   - Look near "Home Phone#", "Cell Phone#", "Work Phone#"
   - Spanish: "Casa #", "Móvil #", "Trabajo #"
   - Return as 10 digits only (e.g., "3052909033")
   - Exclude company phone: 3053636966

4. **customer_address**: Full address with city, state, zip
   - Format: Street, City, State ZIP
   - Example: "16100 SW 102 CT, Miami, FL 33157"

5. **equipment**: All equipment codes separated by spaces
   - Extract ALL equipment/model codes from the contract
   - Use standardized codes from mapping above
   - Return as space-separated codes (e.g., "EC5 QRS RO ALK AM PFAS UV CAGE")
   - Include: BASE, CAGE, COOLER if mentioned

6. **sold_price**: Contract sale price
   - Look for "Contract Price", "Precio del Contrato", "Total"
   - Format with $ sign (e.g., "$18995")
   - If multiple prices, use the final contract price

7. **date**: Contract date in MM/DD/YYYY format
   - Look for date near signature or contract date field
   - Format: MM/DD/YYYY (e.g., "11/26/2025")

8. **lead_po**: Lead or PO number
   - Look for "Lead/PO#", "Lead PO", "Cliente potencial"
   - Usually starts with F or ORD (e.g., "F55825490")

9. **fin_by**: Financing company
   - Look for "Payment Method", "Finance By", "Meta de Pago"
   - Common values: ISPC, Goodleap, Ygrene, Home, Foundation, Cash

**OUTPUT FORMAT:**
Return ONLY valid JSON with these exact keys:
{
  "sales_rep": "",
  "customer_name": "",
  "phone_number": "",
  "customer_address": "",
  "equipment": "",
  "sold_price": "",
  "date": "",
  "lead_po": "",
  "fin_by": ""
}

**CRITICAL RULES:**
- If a field cannot be found, use empty string ""
- Do NOT return placeholder text like "Salesperson Name" for sales_rep
- Phone numbers must be 10 digits only, no formatting
- Equipment must be space-separated standardized codes
- Return ONLY the JSON object, no other text
"""

    def _normalize_equipment(self, equipment_str: str) -> str:
        """Normalize equipment codes to match our cost database"""
        if not equipment_str:
            return ""

        # Split into codes
        codes = equipment_str.upper().split()
        normalized = []

        for code in codes:
            # Normalize common variations
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
            elif code == 'CLEANSTART':
                code = 'CS'
            elif code == 'ULTRAVIOLET':
                code = 'UV'
            elif code == 'REJA':
                code = 'CAGE'
            elif code == 'STAND':
                code = 'BASE'
            elif code == 'HYDRO':
                code = 'HYD'
            elif code == 'OXYGEN':
                code = 'OXY'

            if code not in normalized:
                normalized.append(code)

        return ' '.join(normalized)


def parse_contract_with_ai(pdf_path: str) -> Dict[str, str]:
    """
    Convenience function to parse a contract with AI

    Args:
        pdf_path: Path to the PDF contract file

    Returns:
        Dictionary with extracted contract data
    """
    parser = AIContractParser()
    return parser.parse_contract(pdf_path)


if __name__ == "__main__":
    # Test with a sample contract
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"Parsing contract with AI: {pdf_path}\n")

        data = parse_contract_with_ai(pdf_path)

        print("Extracted Contract Data:")
        print("-" * 60)
        for key, value in data.items():
            print(f"{key:20s}: {value}")
