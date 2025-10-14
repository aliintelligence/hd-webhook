"""
Microsoft Graph API Authentication Module

Handles OAuth authentication with Microsoft Graph API for accessing Outlook emails.
Supports both interactive and headless (client credentials) authentication flows.
"""

import os
import json
import pickle
from msal import PublicClientApplication, ConfidentialClientApplication
from typing import Optional, Dict


class GraphAuthenticator:
    """Handle Microsoft Graph API authentication"""

    def __init__(
        self,
        client_id: str,
        client_secret: Optional[str] = None,
        tenant_id: str = "common",
        cache_file: str = "ms_token_cache.bin"
    ):
        """
        Initialize Graph authenticator

        Args:
            client_id: Azure AD application (client) ID
            client_secret: Client secret (optional, for headless auth)
            tenant_id: Azure AD tenant ID or "common"
            cache_file: Token cache file path
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.cache_file = cache_file
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"

        # Scopes for delegated permissions
        self.scopes = [
            "Mail.Read",
            "Mail.ReadWrite",
            "offline_access"
        ]

    def _load_cache(self) -> Optional[Dict]:
        """Load token cache from file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Warning: Could not load token cache: {e}")
        return None

    def _save_cache(self, cache: Dict):
        """Save token cache to file"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache, f)
        except Exception as e:
            print(f"Warning: Could not save token cache: {e}")

    def get_access_token(self, use_interactive: bool = True) -> str:
        """
        Get a valid access token for Microsoft Graph API

        Args:
            use_interactive: Whether to use interactive auth (browser popup)
                           Set to False for headless/server environments

        Returns:
            Access token string

        Raises:
            Exception: If authentication fails
        """
        # Try client credentials flow first (for headless environments)
        if self.client_secret:
            return self._get_token_client_credentials()

        # Use delegated permissions with MSAL
        if use_interactive:
            return self._get_token_interactive()
        else:
            raise Exception(
                "Interactive auth required but use_interactive=False. "
                "Please provide client_secret for headless authentication."
            )

    def _get_token_client_credentials(self) -> str:
        """
        Get token using client credentials flow (app-only permissions)
        Note: This requires application permissions, not delegated permissions
        """
        app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority
        )

        # For client credentials, use .default scope
        result = app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )

        if "access_token" in result:
            print("✓ Authenticated with client credentials")
            return result["access_token"]
        else:
            error = result.get("error_description", result.get("error"))
            raise Exception(f"Client credentials authentication failed: {error}")

    def _get_token_interactive(self) -> str:
        """Get token using interactive flow (user login)"""
        app = PublicClientApplication(
            client_id=self.client_id,
            authority=self.authority
        )

        # Try silent authentication first
        accounts = app.get_accounts()
        if accounts:
            print("Found cached account, attempting silent authentication...")
            result = app.acquire_token_silent(
                scopes=self.scopes,
                account=accounts[0]
            )
            if result and "access_token" in result:
                print("✓ Authenticated silently (cached credentials)")
                return result["access_token"]

        # Fall back to interactive authentication
        print("Opening browser for authentication...")
        result = app.acquire_token_interactive(
            scopes=self.scopes,
            prompt="select_account"
        )

        if "access_token" in result:
            print("✓ Authenticated interactively")
            return result["access_token"]
        else:
            error = result.get("error_description", result.get("error"))
            raise Exception(f"Interactive authentication failed: {error}")

    def get_token_device_code(self) -> str:
        """
        Get token using device code flow (for remote/headless scenarios)
        User will need to visit a URL and enter a code
        """
        app = PublicClientApplication(
            client_id=self.client_id,
            authority=self.authority
        )

        flow = app.initiate_device_flow(scopes=self.scopes)

        if "user_code" not in flow:
            raise Exception("Failed to create device flow")

        print("\n" + "=" * 60)
        print("DEVICE CODE AUTHENTICATION")
        print("=" * 60)
        print(flow["message"])
        print("=" * 60 + "\n")

        # Wait for user to authenticate
        result = app.acquire_token_by_device_flow(flow)

        if "access_token" in result:
            print("✓ Authenticated with device code")
            return result["access_token"]
        else:
            error = result.get("error_description", result.get("error"))
            raise Exception(f"Device code authentication failed: {error}")


def get_graph_token_from_env(use_interactive: bool = False) -> str:
    """
    Convenience function to get Graph token from environment variables

    Environment variables:
        MS_CLIENT_ID: Required
        MS_CLIENT_SECRET: Optional (for headless auth)
        MS_TENANT_ID: Optional (defaults to "common")

    Args:
        use_interactive: Whether to allow interactive browser authentication

    Returns:
        Access token string
    """
    client_id = os.getenv("MS_CLIENT_ID")
    client_secret = os.getenv("MS_CLIENT_SECRET")
    tenant_id = os.getenv("MS_TENANT_ID", "common")

    if not client_id:
        raise Exception("MS_CLIENT_ID environment variable is required")

    auth = GraphAuthenticator(
        client_id=client_id,
        client_secret=client_secret,
        tenant_id=tenant_id
    )

    return auth.get_access_token(use_interactive=use_interactive)


if __name__ == "__main__":
    """Test authentication"""
    from dotenv import load_dotenv
    load_dotenv()

    print("Testing Microsoft Graph authentication...\n")

    try:
        token = get_graph_token_from_env(use_interactive=True)
        print(f"\n✓ Successfully obtained token")
        print(f"Token preview: {token[:50]}...")
    except Exception as e:
        print(f"\n✗ Authentication failed: {e}")
