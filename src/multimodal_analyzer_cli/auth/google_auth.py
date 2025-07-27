"""
Google-specific authentication integration for multimodal analyzer.
"""

import os

from loguru import logger

from .oauth_manager import GoogleOAuthManager


class GoogleAuthProvider:
    """Provides Google authentication for LiteLLM integration."""
    
    def __init__(self, 
                 callback_host: str = "localhost", 
                 callback_port: int | None = None) -> None:
        """
        Initialize Google authentication provider.
        
        Args:
            callback_host: OAuth callback host (defaults to localhost)
            callback_port: OAuth callback port (auto-detects if None)
        """
        self.callback_host = callback_host
        self.callback_port = callback_port
        self.oauth_manager = GoogleOAuthManager(callback_host, callback_port or 8080)
        self._api_key = os.getenv("GEMINI_API_KEY")
    
    @classmethod
    def from_environment(cls) -> "GoogleAuthProvider":
        """
        Create GoogleAuthProvider based on environment configuration.
        
        Returns:
            Configured GoogleAuthProvider instance
        """
        callback_host = os.getenv("OAUTH_CALLBACK_HOST", "localhost")
        callback_port_str = os.getenv("OAUTH_CALLBACK_PORT")
        callback_port = int(callback_port_str) if callback_port_str else None
        
        logger.debug(f"Google auth provider: callback_host={callback_host}, callback_port={callback_port}")
        
        return cls(
            callback_host=callback_host,
            callback_port=callback_port
        )
    
    def get_auth_token(self) -> str | None:
        """
        Get authentication token for Google/Gemini models using cascade authentication.
        
        Authentication cascade:
        1. Try OAuth with cached credentials (if available)
        2. Fall back to API key
        
        Returns:
            Authentication token (OAuth access token or API key), or None if unavailable
        """
        # 1. Try OAuth with cached credentials first
        if self.oauth_manager:
            access_token = self.oauth_manager.get_valid_access_token()
            if access_token:
                logger.debug("Using OAuth access token for Google authentication")
                return access_token
        
        # 2. Fall back to API key authentication
        if self._api_key:
            logger.debug("Using API key for Google authentication")
            return self._api_key
        
        # No authentication available
        logger.debug("No authentication available (no OAuth tokens or API key)")
        return None
    
    async def authenticate_interactive(self, open_browser: bool = True) -> bool:
        """
        Perform interactive OAuth authentication.
        
        Args:
            open_browser: Whether to open browser automatically
            
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            await self.oauth_manager.authenticate(open_browser=open_browser)
            logger.info("✅ Google OAuth authentication successful")
            return True
        except Exception as e:
            logger.error(f"❌ Google OAuth authentication failed: {e}")
            return False
    
    def logout(self) -> bool:
        """
        Clear stored OAuth credentials.
        
        Returns:
            True if logout successful, False otherwise
        """
        try:
            self.oauth_manager.logout()
            logger.info("✅ Successfully logged out from Google OAuth")
            return True
        except Exception as e:
            logger.error(f"❌ Logout failed: {e}")
            return False
    
    def get_auth_status(self) -> dict:
        """
        Get current authentication status.
        
        Returns:
            Dictionary with authentication status information
        """
        oauth_status = self.oauth_manager.get_auth_status()
        
        status = {
            "has_api_key": bool(self._api_key),
            "oauth_authenticated": oauth_status["authenticated"],
            "oauth_details": oauth_status
        }
        
        # Determine overall authentication status and method
        if status["oauth_authenticated"]:
            status["authenticated"] = True
            status["auth_method"] = "OAuth"
        elif status["has_api_key"]:
            status["authenticated"] = True
            status["auth_method"] = "API Key"
        else:
            status["authenticated"] = False
            status["auth_method"] = "None"
        
        return status
    
    def is_authenticated(self) -> bool:
        """
        Check if any form of authentication is available.
        
        Returns:
            True if authenticated (OAuth or API key), False otherwise
        """
        return self.get_auth_status()["authenticated"]
    
    def validate_for_model(self, model: str) -> None:
        """
        Validate that authentication is available for a Google/Gemini model.
        
        Args:
            model: Model name to validate for
            
        Raises:
            ValueError: If no authentication is available for the model
        """
        if not model.startswith(("gemini", "google/")):
            return  # Not a Google model, no validation needed
        
        if not self.is_authenticated():
            raise ValueError(
                "No Google authentication available. "
                "Run 'multimodal-analyzer auth login' to authenticate with OAuth, "
                "or set GEMINI_API_KEY environment variable."
            )