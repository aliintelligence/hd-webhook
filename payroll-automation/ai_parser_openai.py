"""
AI-Powered PDF Contract Parser using OpenAI GPT-4 Vision
Easy to set up - just need an OpenAI API key
"""

import os
import base64
import json
import io
from typing import Dict
from openai import OpenAI
from dotenv import load_dotenv
import fitz  # PyMuPDF

# Load environment variables
load_dotenv()


class AIContractParser:
    """Parse contracts using OpenAI GPT-4 Vision"""

    def __init__(self, api_key: str = None):
        """
        Initialize OpenAI client

        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY environment variable)
        """
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))

    def parse_contract(self, pdf_path: str) -> Dict[str, str]:
        """
        Parse contract PDF using AI

        Args:
            pdf_path: Path to the PDF contract file

        Returns:
            Dictionary with extracted contract data
        """
        # Convert PDF pages to images using PyMuPDF
        pdf_document = fitz.open(pdf_path)
        image_contents = []

        # Process first 3 pages
        for page_num in range(min(3, len(pdf_document))):
            page = pdf_document[page_num]
            # Render page to image at 200 DPI
            pix = page.get_pixmap(matrix=fitz.Matrix(200/72, 200/72))
            # Convert to PNG bytes
            img_bytes = pix.pil_tobytes(format="PNG")
            # Convert to base64
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            image_contents.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_base64}"
                }
            })

        pdf_document.close()

        # Create the prompt
        prompt = self._create_extraction_prompt()

        try:
            # Call GPT-4 Vision
            response = self.client.chat.completions.create(
                model="gpt-4o",  # GPT-4 Omni
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            *image_contents
                        ]
                    }
                ],
                temperature=0.1,
                max_tokens=2048
            )

            # Parse JSON response
            result_text = response.choices[0].message.content.strip()

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

**EQUIPMENT MAPPING GUIDE (English & Spanish):**
Map any equipment text to these standardized codes:
- EC5, ECS, E.C.5, ES5 → EC5
- TC, TCM, T.C., Acondicionador, Acondicionamiento → TC
- BCM → BCM
- HYD, Hydro, Hidro → HYD
- QRS, Q.R.S, Quad → QRS
- AM, Airmaster, Aire → AM
- CS, Clean Start, Inicio Limpio → CS
- UV, UV Light, Ultraviolet, Luz UV, Ultravioleta → UV
- ALK, Alkaline, Alk, Alcalino → ALK
- OXY, Oxygen, Oxígeno → OXY
- RO, R.O., Reverse Osmosis, Ósmosis Inversa → RO
- PFAS → PFAS
- Cage, Reja, Jaula → CAGE
- Base, Stand, Soporte → BASE
- Cooler, Enfriador → COOLER
- Sistema de agua, Water system → (extract equipment codes from description)

**EXTRACT THESE FIELDS:**

1. **sales_rep**: The salesperson's name (first and last name)
   - Look near "Salesperson Name", "Nombre del vendedor", or "Sales Rep"
   - If you find "Salesperson Name" as placeholder text, look for an actual name nearby
   - Common names: Shayne Luque, Carlo Dalelio, Fernando Falco, etc.
   - If no actual name found, return empty string ""

2. **customer_name**: Customer's full name (First Last format)
   - Format as: FirstName LastName

3. **phone_number**: Customer's phone number (10 digits, no dashes)
   - Return as 10 digits only (e.g., "3052909033")
   - Exclude company phone: 3053636966

4. **customer_address**: Full address with city, state, zip
   - Format: Street, City, State ZIP

5. **equipment**: All equipment codes separated by spaces (BILINGUAL - English & Spanish)
   - Look for "Model #" or "Modelo #" section
   - Look for equipment descriptions like "Water Conditioning System" or "Sistema de acondicionamiento de agua"
   - Extract ALL equipment codes mentioned (QRS, RO, ALK, AM, CS, PFAS, UV, CAGE, BASE, HYD, etc.)
   - Use standardized codes from mapping above (works for both English and Spanish terms)
   - Return as space-separated codes (e.g., "TC QRS RO ALK AM PFAS UV CAGE")
   - IMPORTANT: Look carefully throughout the ENTIRE contract for equipment mentions in BOTH languages
   - Check near price, descriptions, installation notes, anywhere equipment might be mentioned
   - Spanish contracts may use terms like "Acondicionador" (TC), "Ósmosis Inversa" (RO), "Alcalino" (ALK), etc.
   - If you see partial codes or abbreviations (like just "T" for TC or "R" for RO), use context to determine the full code
   - Make your best intelligent guess if equipment codes are unclear - equipment is ALWAYS present in these contracts
   - **CRITICAL RULE: EC5 and TC are both water softeners - ONLY ONE can be present:**
     * If you see both EC5 and TC mentioned, choose ONLY the one that appears in the Model # section
     * EC5 is the newer/premium softener, TC is the standard softener
     * A contract will have EITHER "EC5" OR "TC", never both
   - Common basic system: "TC" (water conditioning / acondicionador de agua)
   - Never leave equipment blank - make an educated guess based on contract type and price
   - If unsure and no clear equipment found, default to "TC" for basic water conditioning

6. **sold_price**: Contract sale price with $ sign (e.g., "$18995")

7. **date**: Contract date in MM/DD/YYYY format

8. **lead_po**: Lead or PO number (usually starts with F or ORD)

9. **fin_by**: Financing company
   - Look for "Payment Method", "Finance By", "Meta de Pago", or "Financing"
   - Common values: ISPC, Goodleap, Ygrene, Home, Foundation, Cash
   - Extract the company name exactly as written

**OUTPUT FORMAT:**
Return ONLY valid JSON:
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
"""

    def _normalize_equipment(self, equipment_str: str) -> str:
        """Normalize equipment codes"""
        if not equipment_str:
            return ""

        codes = equipment_str.upper().split()
        normalized = []

        for code in codes:
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
            elif code == 'REJA':
                code = 'CAGE'
            elif code == 'STAND':
                code = 'BASE'

            if code not in normalized:
                normalized.append(code)

        return ' '.join(normalized)


def parse_contract_with_ai(pdf_path: str) -> Dict[str, str]:
    """Parse contract using OpenAI"""
    parser = AIContractParser()
    return parser.parse_contract(pdf_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"Parsing contract with AI: {pdf_path}\n")

        data = parse_contract_with_ai(pdf_path)

        print("Extracted Contract Data:")
        print("-" * 60)
        for key, value in data.items():
            print(f"{key:20s}: {value}")
