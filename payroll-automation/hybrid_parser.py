"""
Hybrid PDF Parser - Combines AI and Regex for best accuracy
Uses AI for: sales_rep, customer_name, phone, address, price, date, lead_po
Uses Regex for: equipment, fin_by (more reliable for these fields)
"""

from typing import Dict
from ai_parser_openai import AIContractParser
from pdf_parser import ContractParser


def _get_best_equipment(regex_equipment: str, ai_equipment: str) -> str:
    """
    Get best equipment extraction using smart fallback logic:
    1. If regex has valid 2+ char codes, use filtered regex
    2. If regex only has single letters or is empty, trust AI (unfiltered)
    3. Equipment should always be present - trust AI when in doubt
    4. Enforce rule: EC5 and TC are mutually exclusive (both are water softeners)
    """
    if not regex_equipment and not ai_equipment:
        return 'TC'  # Default to basic water conditioning if nothing found

    # Filter regex to get valid codes (2+ chars)
    regex_codes = regex_equipment.strip().split() if regex_equipment else []
    valid_regex_codes = [code for code in regex_codes if len(code) >= 2]

    # If regex has valid codes, use them
    if valid_regex_codes:
        equipment = ' '.join(valid_regex_codes)
    else:
        # Otherwise, trust AI completely (even single letters)
        # AI is smart enough to identify equipment when regex fails
        equipment = ai_equipment if ai_equipment else 'TC'

    # Enforce EC5/TC mutual exclusivity
    codes = equipment.split()
    if 'EC5' in codes and 'TC' in codes:
        # EC5 is premium, so keep EC5 and remove TC
        codes = [c for c in codes if c != 'TC']
        equipment = ' '.join(codes)

    return equipment if equipment else 'TC'


def parse_contract_hybrid(pdf_path: str) -> Dict[str, str]:
    """
    Parse contract using hybrid AI + Regex approach

    Args:
        pdf_path: Path to the PDF contract file

    Returns:
        Dictionary with extracted contract data
    """
    # Use AI parser for most fields
    ai_parser = AIContractParser()
    ai_data = ai_parser.parse_contract(pdf_path)

    # Use regex parser for equipment and financing (more reliable)
    regex_parser = ContractParser(pdf_path)
    regex_parser.extract_text()
    regex_data = regex_parser.parse()

    # Get equipment from both sources
    regex_equipment = regex_data.get('equipment', '')
    ai_equipment = ai_data.get('equipment', '')

    # Use smart fallback logic: prefer regex, trust AI when regex fails
    final_equipment = _get_best_equipment(regex_equipment, ai_equipment)

    # Combine the best of both
    hybrid_data = {
        # From AI (more accurate for these)
        "sales_rep": ai_data.get('sales_rep') or regex_data.get('sales_rep', ''),
        "customer_name": ai_data.get('customer_name') or regex_data.get('customer_name', ''),
        "phone_number": ai_data.get('phone_number') or regex_data.get('phone_number', ''),
        "customer_address": ai_data.get('customer_address') or regex_data.get('customer_address', ''),
        "sold_price": ai_data.get('sold_price') or regex_data.get('sold_price', ''),
        "date": ai_data.get('date') or regex_data.get('date', ''),
        "lead_po": ai_data.get('lead_po') or regex_data.get('lead_po', ''),

        # Equipment: Regex preferred (filtered), AI as fallback
        "equipment": final_equipment,
        "fin_by": regex_data.get('fin_by', '') or ai_data.get('fin_by', ''),
    }

    return hybrid_data


if __name__ == "__main__":
    # Test with a sample contract
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"Parsing contract with HYBRID AI + Regex: {pdf_path}\n")

        data = parse_contract_hybrid(pdf_path)

        print("Extracted Contract Data:")
        print("-" * 60)
        for key, value in data.items():
            print(f"{key:20s}: {value}")
