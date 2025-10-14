"""
Sales Rep Router

Handles routing contracts to the correct spreadsheet based on sales rep name.
"""

import json
import os
from typing import Optional, Dict
from difflib import get_close_matches


class SalesRepRouter:
    """Route contracts to correct spreadsheet based on sales rep"""

    def __init__(self, mapping_file: str = "sales_rep_mapping.json"):
        """
        Initialize router with sales rep to spreadsheet mapping

        Args:
            mapping_file: Path to JSON file with sales rep mappings
        """
        self.mapping_file = mapping_file
        self.mapping = self._load_mapping()

    def _load_mapping(self) -> Dict:
        """Load sales rep mapping from JSON file"""
        if not os.path.exists(self.mapping_file):
            print(f"⚠ Warning: Mapping file not found: {self.mapping_file}")
            return {"sales_reps": {}, "fallback_spreadsheet_id": None}

        try:
            with open(self.mapping_file, 'r') as f:
                mapping = json.load(f)
                print(f"✓ Loaded {len(mapping.get('sales_reps', {}))} sales rep mappings")
                return mapping
        except Exception as e:
            print(f"✗ Error loading mapping file: {e}")
            return {"sales_reps": {}, "fallback_spreadsheet_id": None}

    def get_spreadsheet_id(self, sales_rep_name: Optional[str]) -> Optional[str]:
        """
        Get spreadsheet ID for a sales rep

        Args:
            sales_rep_name: Name of the sales rep from PDF

        Returns:
            Spreadsheet ID or None if not found
        """
        if not sales_rep_name:
            print("⚠ No sales rep name provided, using fallback")
            return self.mapping.get("fallback_spreadsheet_id")

        # Clean the name
        sales_rep_name = sales_rep_name.strip()

        # Try exact match first
        sales_reps = self.mapping.get("sales_reps", {})
        if sales_rep_name in sales_reps:
            spreadsheet_id = sales_reps[sales_rep_name]
            print(f"✓ Found exact match: {sales_rep_name} → {spreadsheet_id[:20]}...")
            return spreadsheet_id

        # Try case-insensitive match
        for rep_name, sheet_id in sales_reps.items():
            if rep_name.lower() == sales_rep_name.lower():
                print(f"✓ Found case-insensitive match: {sales_rep_name} → {rep_name}")
                return sheet_id

        # Try fuzzy matching
        rep_names = list(sales_reps.keys())
        close_matches = get_close_matches(sales_rep_name, rep_names, n=1, cutoff=0.8)

        if close_matches:
            matched_name = close_matches[0]
            spreadsheet_id = sales_reps[matched_name]
            print(f"✓ Found fuzzy match: '{sales_rep_name}' → '{matched_name}'")
            return spreadsheet_id

        # No match found, use fallback
        fallback_id = self.mapping.get("fallback_spreadsheet_id")
        print(f"⚠ No match found for '{sales_rep_name}', using fallback")
        return fallback_id

    def get_all_sales_reps(self) -> list:
        """Get list of all configured sales reps"""
        return list(self.mapping.get("sales_reps", {}).keys())

    def add_sales_rep(self, name: str, spreadsheet_id: str):
        """
        Add a new sales rep to the mapping

        Args:
            name: Sales rep name
            spreadsheet_id: Google Sheets spreadsheet ID
        """
        if "sales_reps" not in self.mapping:
            self.mapping["sales_reps"] = {}

        self.mapping["sales_reps"][name] = spreadsheet_id

        # Save to file
        try:
            with open(self.mapping_file, 'w') as f:
                json.dump(self.mapping, f, indent=2)
            print(f"✓ Added {name} to mapping")
        except Exception as e:
            print(f"✗ Error saving mapping: {e}")


def get_router() -> SalesRepRouter:
    """Get default sales rep router instance"""
    return SalesRepRouter()


if __name__ == "__main__":
    """Test sales rep router"""
    router = SalesRepRouter()

    print("\nConfigured Sales Reps:")
    print("=" * 60)
    for rep in router.get_all_sales_reps():
        print(f"  - {rep}")
    print("=" * 60)

    # Test some lookups
    test_names = [
        "Angel Ruiz",
        "angel ruiz",  # lowercase
        "Angel  Ruiz",  # extra space
        "Angle Ruiz",  # typo
        "Unknown Person",  # not in list
    ]

    print("\nTesting Lookups:")
    print("=" * 60)
    for name in test_names:
        result = router.get_spreadsheet_id(name)
        print(f"'{name}' → {result[:20] if result else 'None'}...")
    print("=" * 60)
