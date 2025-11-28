"""
Name Matching Module
Fuzzy matching for sales rep names to handle variations, nicknames, and partial matches
"""

from fuzzywuzzy import fuzz, process
from typing import Optional, Tuple
from config import REP_SPREADSHEETS


class NameMatcher:
    """Match sales rep names using fuzzy logic"""

    def __init__(self, rep_mapping: dict = None):
        self.rep_mapping = rep_mapping or REP_SPREADSHEETS
        self.rep_names = list(self.rep_mapping.keys())

    def find_best_match(self, name: str, threshold: int = 70) -> Tuple[Optional[str], int]:
        """
        Find the best matching rep name using fuzzy matching

        Args:
            name: Name extracted from contract
            threshold: Minimum similarity score (0-100)

        Returns:
            Tuple of (matched_name, confidence_score) or (None, 0) if no match
        """
        if not name or not name.strip():
            return None, 0

        name = name.strip()

        # First try exact match (case insensitive)
        for rep_name in self.rep_names:
            if name.lower() == rep_name.lower():
                return rep_name, 100

        # Try fuzzy matching
        best_match, score = process.extractOne(name, self.rep_names, scorer=fuzz.token_sort_ratio)

        if score >= threshold:
            return best_match, score

        # Try partial matching (for nicknames or first names)
        # Check if the input name matches the first name of any rep
        name_parts = name.lower().split()
        for rep_name in self.rep_names:
            rep_parts = rep_name.lower().split()
            # Check first name match
            if name_parts[0] == rep_parts[0]:
                return rep_name, 85

            # Check last name match
            if len(name_parts) > 1 and name_parts[-1] == rep_parts[-1]:
                return rep_name, 80

        return None, 0

    def get_spreadsheet_id(self, name: str) -> Optional[str]:
        """
        Get spreadsheet ID for a sales rep name

        Args:
            name: Sales rep name

        Returns:
            Spreadsheet ID or None if not found
        """
        matched_name, score = self.find_best_match(name)

        if matched_name:
            print(f"Matched '{name}' to '{matched_name}' (confidence: {score}%)")
            return self.rep_mapping.get(matched_name)

        print(f"No match found for '{name}'")
        return None


def match_rep_name(name: str) -> Tuple[Optional[str], Optional[str], int]:
    """
    Convenience function to match a rep name and get their spreadsheet ID

    Args:
        name: Sales rep name from contract

    Returns:
        Tuple of (matched_name, spreadsheet_id, confidence_score)
    """
    matcher = NameMatcher()
    matched_name, score = matcher.find_best_match(name)

    if matched_name:
        spreadsheet_id = matcher.rep_mapping[matched_name]
        return matched_name, spreadsheet_id, score

    return None, None, 0


if __name__ == "__main__":
    # Test name matching
    test_names = [
        "Carlo Dalelio",
        "Carlo",
        "Dalelio",
        "Bryan",
        "Bryan Gonzalez",
        "David",
        "Shayne",
        "Unknown Person"
    ]

    matcher = NameMatcher()

    print("Testing Name Matching:")
    print("-" * 60)

    for name in test_names:
        matched_name, sheet_id, score = match_rep_name(name)
        if matched_name:
            print(f"'{name}' → '{matched_name}' (score: {score}%)")
            print(f"  Sheet ID: {sheet_id[:20]}...")
        else:
            print(f"'{name}' → NO MATCH")
        print()
