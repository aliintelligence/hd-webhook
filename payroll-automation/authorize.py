"""
Simple script to authorize Google API access
Run this first before using the main automation
"""

from google_auth import get_credentials

print("="*60)
print("GOOGLE API AUTHORIZATION")
print("="*60)
print("\nThis will authorize the app to access your Google Drive and Sheets.")
print("Follow the instructions that appear...\n")

try:
    creds = get_credentials()
    print("\n" + "="*60)
    print("✓ AUTHORIZATION SUCCESSFUL!")
    print("="*60)
    print("\nYou can now run the main automation:")
    print("  python3 main.py")
    print("\nOr test with a single contract:")
    print("  python3 main.py /path/to/contract.pdf")
    print()
except Exception as e:
    print(f"\n✗ Authorization failed: {e}")
    print("\nPlease check:")
    print("1. credentials.json file exists")
    print("2. Google Drive and Sheets APIs are enabled")
    print("3. You completed the authorization in the browser")
