"""
Equipment Cost Calculator
Parses equipment strings and calculates total cost
"""

import re
from typing import Tuple, List
from config import EQUIPMENT_COSTS, EQUIPMENT_MAPPING, MARKETING_FEE_PERCENT


def parse_equipment_string(equipment_str: str) -> List[str]:
    """
    Parse equipment string and identify components

    Args:
        equipment_str: Equipment description (e.g., "EC5 QRS RO ALK AM PFAS UV CAGE")

    Returns:
        List of standardized equipment keys
    """
    if not equipment_str:
        return []

    # Normalize the string
    equipment_str = equipment_str.upper().strip()

    found_equipment = []

    # Try to match each equipment type
    for standard_key, variations in EQUIPMENT_MAPPING.items():
        for variation in variations:
            # Use word boundaries to avoid partial matches
            # But also handle cases like "EC5" in "EC5QRS"
            pattern = r'\b' + re.escape(variation.upper()) + r'\b'
            if re.search(pattern, equipment_str):
                if standard_key not in found_equipment:
                    found_equipment.append(standard_key)
                break

    return found_equipment


def calculate_equipment_cost(equipment_str: str) -> float:
    """
    Calculate total equipment cost from equipment string

    Args:
        equipment_str: Equipment description

    Returns:
        Total equipment cost
    """
    components = parse_equipment_string(equipment_str)

    total_cost = 0.0
    for component in components:
        if component in EQUIPMENT_COSTS:
            total_cost += EQUIPMENT_COSTS[component]

    return total_cost


def calculate_profit(sold_price_str: str, equipment_str: str) -> Tuple[float, float, float]:
    """
    Calculate profit from sale

    Args:
        sold_price_str: Sale price (e.g., "$10995" or "10995")
        equipment_str: Equipment description

    Returns:
        Tuple of (equipment_cost, marketing_fee, profit)
    """
    # Parse sold price
    try:
        sold_price = float(re.sub(r'[^\d.]', '', sold_price_str))
    except (ValueError, TypeError):
        return (0.0, 0.0, 0.0)

    # Calculate equipment cost
    equipment_cost = calculate_equipment_cost(equipment_str)

    # Calculate marketing fee
    marketing_fee = sold_price * MARKETING_FEE_PERCENT

    # Calculate profit
    profit = sold_price - equipment_cost - marketing_fee

    return (equipment_cost, marketing_fee, profit)


def format_currency(amount: float) -> str:
    """Format amount as currency string"""
    return f"${amount:,.2f}"


if __name__ == "__main__":
    # Test with sample equipment strings
    test_cases = [
        "EC5 QRS RO BASE",
        "EC5 QRS RO ALK AM PFAS UV CAGE",
        "TCM QRS Base",
        "BCM HYD Pump"
    ]

    print("Equipment Cost Calculator Test\n" + "="*60)

    for equipment in test_cases:
        components = parse_equipment_string(equipment)
        cost = calculate_equipment_cost(equipment)

        print(f"\nEquipment: {equipment}")
        print(f"Components: {', '.join(components)}")
        print(f"Total Cost: {format_currency(cost)}")

        # Test with sample sale price
        sold_price = "$10995"
        eq_cost, mkt_fee, profit = calculate_profit(sold_price, equipment)
        print(f"Sold Price: {sold_price}")
        print(f"  Equipment Cost: {format_currency(eq_cost)}")
        print(f"  Marketing Fee: {format_currency(mkt_fee)}")
        print(f"  Profit: {format_currency(profit)}")
