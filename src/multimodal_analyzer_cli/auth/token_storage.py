"""
Secure token storage for OAuth credentials.
"""

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger


class TokenStorage:
    """Handles secure storage and retrieval of OAuth tokens."""

    def __init__(self, token_path: Path | None = None) -> None:
        """
        Initialize token storage.
        
        Args:
            token_path: Path to store tokens. Defaults to ~/.multimodal_analyzer/google_oauth.json
        """
        if token_path is None:
            token_path = Path.home() / ".multimodal_analyzer" / "google_oauth.json"
        
        self.token_path = token_path
        self._ensure_directory_exists()

    def _ensure_directory_exists(self) -> None:
        """Create the token directory if it doesn't exist."""
        self.token_path.parent.mkdir(parents=True, exist_ok=True)

    def store_tokens(self, tokens: dict) -> None:
        """
        Store OAuth tokens securely.
        
        Args:
            tokens: Dictionary containing OAuth tokens (access_token, refresh_token, etc.)
        """
        try:
            # Write tokens to file with restricted permissions
            with open(self.token_path, "w") as f:
                json.dump(tokens, f, indent=2)
            
            # Set file permissions to owner read/write only (0o600)
            os.chmod(self.token_path, 0o600)
            
            logger.debug(f"Stored OAuth tokens to {self.token_path}")
            
        except Exception as e:
            logger.error(f"Failed to store OAuth tokens: {e}")
            raise

    def load_tokens(self) -> dict | None:
        """
        Load stored OAuth tokens.
        
        Returns:
            Dictionary containing OAuth tokens, or None if no tokens exist
        """
        try:
            if not self.token_path.exists():
                logger.debug("No stored OAuth tokens found")
                return None
            
            with open(self.token_path) as f:
                tokens = json.load(f)
            
            logger.debug(f"Loaded OAuth tokens from {self.token_path}")
            return tokens
            
        except Exception as e:
            logger.error(f"Failed to load OAuth tokens: {e}")
            return None

    def clear_tokens(self) -> None:
        """Remove stored OAuth tokens."""
        try:
            if self.token_path.exists():
                self.token_path.unlink()
                logger.debug(f"Cleared OAuth tokens from {self.token_path}")
        except Exception as e:
            logger.error(f"Failed to clear OAuth tokens: {e}")
            raise

    def is_token_valid(self, tokens: dict | None = None) -> bool:
        """
        Check if stored tokens are valid (not expired).
        
        Args:
            tokens: Token dict to check, or None to load from storage
            
        Returns:
            True if tokens exist and are not expired
        """
        if tokens is None:
            tokens = self.load_tokens()
        
        if not tokens:
            return False
        
        # Check if access token exists
        if "access_token" not in tokens:
            return False
        
        # Check expiration if available
        if "expires_at" in tokens:
            try:
                expires_at = datetime.fromisoformat(tokens["expires_at"])
                now = datetime.now(UTC)
                
                # Add 5-minute buffer before expiration
                if expires_at <= now.replace(tzinfo=UTC):
                    logger.debug("OAuth token is expired")
                    return False
                    
            except ValueError:
                logger.warning("Invalid expires_at format in stored tokens")
                return False
        
        return True

    def get_access_token(self) -> str | None:
        """
        Get a valid access token.
        
        Returns:
            Access token string, or None if no valid token available
        """
        tokens = self.load_tokens()
        if self.is_token_valid(tokens):
            return tokens["access_token"]
        return None

    def update_access_token(self, access_token: str, expires_in: int | None = None) -> None:
        """
        Update just the access token (useful for token refresh).
        
        Args:
            access_token: New access token
            expires_in: Token expiry time in seconds from now
        """
        tokens = self.load_tokens() or {}
        tokens["access_token"] = access_token
        
        if expires_in:
            expires_at = datetime.now(UTC).timestamp() + expires_in
            tokens["expires_at"] = datetime.fromtimestamp(expires_at, UTC).isoformat()
        
        self.store_tokens(tokens)