"""
OAuth 2.0 flow management for Google authentication.
"""

import base64
import hashlib
import os
import secrets
import socket
import urllib.parse
import webbrowser
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import requests
from loguru import logger

from .token_storage import TokenStorage

# OAuth configuration constants
OAUTH_CLIENT_ID = "681255809395-oo8ft2oprdrnp9e3aqf6av3hmdib135j.apps.googleusercontent.com"
OAUTH_CLIENT_SECRET = "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"
OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


def get_available_port(start_port: int = 8080) -> int:
    """Find an available port starting from the given port."""
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("localhost", port))
                return port
        except OSError:
            continue
    raise RuntimeError("No available ports found")


def should_suppress_browser() -> bool:
    """
    Determine if browser should be suppressed based on environment.
    Similar to Gemini CLI's browser detection logic.
    """
    # Check NO_BROWSER environment variable
    if os.getenv("NO_BROWSER"):
        return True
    
    # Check for CI/headless environments
    if os.getenv("CI"):
        return True
    
    if os.getenv("DEBIAN_FRONTEND") == "noninteractive":
        return True
    
    # Check for SSH session
    if os.getenv("SSH_CONNECTION"):
        return True
    
    # Check for display availability on Linux
    if os.name == "posix":
        if not any(os.getenv(var) for var in ["DISPLAY", "WAYLAND_DISPLAY", "MIR_SOCKET"]):
            return True
    
    return False


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callback."""
    
    def __init__(self, *args, oauth_manager=None, **kwargs):
        self.oauth_manager = oauth_manager
        super().__init__(*args, **kwargs)
    
    def do_GET(self) -> None:
        """Handle GET request for OAuth callback."""
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        if parsed_url.path == "/oauth2callback":
            try:
                # Extract authorization code and state
                code = query_params.get("code", [None])[0]
                state = query_params.get("state", [None])[0]
                error = query_params.get("error", [None])[0]
                
                if error:
                    self._send_error_response(f"OAuth error: {error}")
                    self.oauth_manager.auth_result = {"error": error}
                    return
                
                if not code or not state:
                    self._send_error_response("Missing authorization code or state")
                    self.oauth_manager.auth_result = {"error": "missing_params"}
                    return
                
                # Validate state parameter
                if state != self.oauth_manager.state:
                    self._send_error_response("Invalid state parameter")
                    self.oauth_manager.auth_result = {"error": "invalid_state"}
                    return
                
                # Store the authorization code
                self.oauth_manager.auth_result = {"code": code}
                self._send_success_response()
                
            except Exception as e:
                logger.error(f"OAuth callback error: {e}")
                self._send_error_response(f"Internal error: {e}")
                self.oauth_manager.auth_result = {"error": str(e)}
        else:
            self._send_error_response("Not found")
    
    def _send_success_response(self) -> None:
        """Send success response to browser."""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        html = """
        <html>
        <head><title>Authentication Successful</title></head>
        <body>
        <h1>✅ Authentication Successful!</h1>
        <p>You can now close this window and return to the command line.</p>
        </body>
        </html>
        """
        self.wfile.write(html.encode())
    
    def _send_error_response(self, error_msg: str) -> None:
        """Send error response to browser."""
        self.send_response(400)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        html = f"""
        <html>
        <head><title>Authentication Error</title></head>
        <body>
        <h1>❌ Authentication Error</h1>
        <p>{error_msg}</p>
        <p>Please try again or check your configuration.</p>
        </body>
        </html>
        """
        self.wfile.write(html.encode())
    
    def log_message(self, format: str, *args) -> None:
        """Suppress default HTTP server logging."""


class GoogleOAuthManager:
    """Manages Google OAuth 2.0 authentication flow."""
    
    def __init__(self, callback_host: str = "localhost", callback_port: int | None = None) -> None:
        """
        Initialize OAuth manager.
        
        Args:
            callback_host: Host for OAuth callback server
            callback_port: Port for OAuth callback server (auto-detects if None)
        """
        self.callback_host = callback_host
        # Auto-detect available port if not specified
        self.callback_port = callback_port or get_available_port()
        self.redirect_uri = f"http://{callback_host}:{self.callback_port}/oauth2callback"
        
        self.token_storage = TokenStorage()
        self.state: str | None = None
        self.code_verifier: str | None = None
        self.auth_result: dict | None = None
    
    def _generate_pkce_params(self) -> tuple[str, str]:
        """
        Generate PKCE code verifier and challenge.
        
        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        # Generate code verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")
        
        # Generate code challenge
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode("utf-8")).digest()
        ).decode("utf-8").rstrip("=")
        
        return code_verifier, code_challenge
    
    def _build_auth_url(self) -> str:
        """
        Build authorization URL with PKCE parameters.
        
        Returns:
            Authorization URL string
        """
        # Generate PKCE parameters
        self.code_verifier, code_challenge = self._generate_pkce_params()
        
        # Generate state parameter for CSRF protection
        self.state = secrets.token_urlsafe(32)
        
        # Build authorization URL
        auth_params = {
            "client_id": OAUTH_CLIENT_ID,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(OAUTH_SCOPES),
            "response_type": "code",
            "state": self.state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "access_type": "offline",  # Request refresh token
            "prompt": "consent"  # Force consent to get refresh token
        }
        
        auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(auth_params)
        return auth_url
    
    def _exchange_code_for_tokens(self, authorization_code: str) -> dict:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            authorization_code: Authorization code from OAuth callback
            
        Returns:
            Dictionary containing tokens
        """
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            "client_id": OAUTH_CLIENT_ID,
            "client_secret": OAUTH_CLIENT_SECRET,
            "code": authorization_code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
            "code_verifier": self.code_verifier
        }
        
        response = requests.post(token_url, data=data)
        
        if response.status_code != 200:
            error_details = response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
            raise ValueError(f"Token exchange failed: {error_details}")
        
        tokens = response.json()
        
        # Add expiration timestamp
        if "expires_in" in tokens:
            expires_at = datetime.now(UTC).timestamp() + tokens["expires_in"]
            tokens["expires_at"] = datetime.fromtimestamp(expires_at, UTC).isoformat()
        
        return tokens
    
    def _start_callback_server(self) -> HTTPServer:
        """
        Start local HTTP server for OAuth callback.
        
        Returns:
            HTTPServer instance
        """
        def handler_factory(*args, **kwargs):
            return OAuthCallbackHandler(*args, oauth_manager=self, **kwargs)
        
        server = HTTPServer((self.callback_host, self.callback_port), handler_factory)
        return server
    
    async def authenticate(self, open_browser: bool | None = None) -> dict:
        """
        Perform OAuth authentication flow.
        
        Args:
            open_browser: Whether to automatically open browser for authorization.
                         If None, auto-detects based on environment.
            
        Returns:
            Dictionary containing access and refresh tokens
        """
        try:
            # Check if we have valid existing tokens
            if self.token_storage.is_token_valid():
                logger.info("Using existing valid OAuth tokens")
                return self.token_storage.load_tokens()
            
            logger.info("Starting OAuth authentication flow...")
            
            # Build authorization URL
            auth_url = self._build_auth_url()
            
            # Start callback server
            server = self._start_callback_server()
            logger.debug(f"Started OAuth callback server on {self.callback_host}:{self.callback_port}")
            
            # Determine whether to open browser
            if open_browser is None:
                open_browser = not should_suppress_browser()
            
            # Open browser or display URL
            if open_browser:
                try:
                    webbrowser.open(auth_url)
                    logger.info("Opened browser for authentication")
                except Exception as e:
                    logger.warning(f"Failed to open browser: {e}")
                    open_browser = False
            
            if not open_browser:
                logger.info("Please visit the following URL to authenticate:")
                logger.info(auth_url)
            
            # Wait for callback
            logger.info("Waiting for OAuth callback...")
            self.auth_result = None
            
            while self.auth_result is None:
                server.handle_request()
            
            server.server_close()
            
            # Check for errors
            if "error" in self.auth_result:
                raise ValueError(f"OAuth authentication failed: {self.auth_result['error']}")
            
            # Exchange code for tokens
            authorization_code = self.auth_result["code"]
            tokens = self._exchange_code_for_tokens(authorization_code)
            
            # Store tokens securely
            self.token_storage.store_tokens(tokens)
            
            logger.info("✅ OAuth authentication successful!")
            return tokens
            
        except Exception as e:
            logger.error(f"OAuth authentication failed: {e}")
            raise
    
    def has_oauth_setup(self) -> bool:
        """
        Check if OAuth has been previously configured (tokens exist).
        
        Returns:
            True if OAuth tokens exist (even if expired), False if never set up
        """
        tokens = self.token_storage.load_tokens()
        return tokens is not None and bool(tokens)

    def refresh_token(self) -> dict | None:
        """
        Refresh access token using stored refresh token.
        
        Returns:
            New tokens dictionary, or None if refresh failed
        """
        try:
            tokens = self.token_storage.load_tokens()
            if not tokens or "refresh_token" not in tokens:
                # Only warn if OAuth was previously set up but tokens are missing/invalid
                if self.has_oauth_setup():
                    logger.warning("No refresh token available")
                return None
            
            refresh_url = "https://oauth2.googleapis.com/token"
            
            data = {
                "client_id": OAUTH_CLIENT_ID,
                "client_secret": OAUTH_CLIENT_SECRET,
                "refresh_token": tokens["refresh_token"],
                "grant_type": "refresh_token"
            }
            
            response = requests.post(refresh_url, data=data)
            
            if response.status_code != 200:
                logger.error(f"Token refresh failed: {response.text}")
                return None
            
            new_tokens = response.json()
            
            # Update stored tokens with new access token
            tokens.update(new_tokens)
            
            # Add expiration timestamp
            if "expires_in" in new_tokens:
                expires_at = datetime.now(UTC).timestamp() + new_tokens["expires_in"]
                tokens["expires_at"] = datetime.fromtimestamp(expires_at, UTC).isoformat()
            
            self.token_storage.store_tokens(tokens)
            logger.debug("Successfully refreshed OAuth tokens")
            
            return tokens
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return None
    
    def get_valid_access_token(self) -> str | None:
        """
        Get a valid access token, refreshing if necessary.
        
        Returns:
            Valid access token string, or None if unavailable
        """
        # Check current tokens
        if self.token_storage.is_token_valid():
            return self.token_storage.get_access_token()
        
        # Only proceed with refresh if OAuth was previously set up
        if not self.has_oauth_setup():
            # No OAuth setup - silently return None to allow API key fallback
            return None
        
        # Try to refresh
        logger.debug("Access token expired, attempting refresh...")
        refreshed_tokens = self.refresh_token()
        
        if refreshed_tokens:
            return refreshed_tokens.get("access_token")
        
        logger.warning("No valid access token available - re-authentication required")
        return None
    
    def logout(self) -> None:
        """Clear stored OAuth tokens."""
        try:
            self.token_storage.clear_tokens()
            logger.info("Successfully logged out - OAuth tokens cleared")
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            raise
    
    def get_auth_status(self) -> dict:
        """
        Get current authentication status.
        
        Returns:
            Dictionary with authentication status information
        """
        tokens = self.token_storage.load_tokens()
        
        if not tokens:
            return {
                "authenticated": False,
                "message": "No OAuth tokens found"
            }
        
        is_valid = self.token_storage.is_token_valid(tokens)
        
        status = {
            "authenticated": is_valid,
            "has_refresh_token": "refresh_token" in tokens,
        }
        
        if "expires_at" in tokens:
            try:
                expires_at = datetime.fromisoformat(tokens["expires_at"])
                status["expires_at"] = expires_at.isoformat()
                status["expired"] = expires_at <= datetime.now(UTC)
            except ValueError:
                status["expires_at"] = "Invalid format"
        
        if is_valid:
            status["message"] = "OAuth authentication is valid"
        else:
            status["message"] = "OAuth tokens are expired or invalid"
        
        return status