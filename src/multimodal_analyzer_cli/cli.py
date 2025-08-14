import asyncio
from pathlib import Path

import click
import litellm
from loguru import logger

from .audio_analyzer import AudioAnalyzer
from .config import Config
from .image_analyzer import ImageAnalyzer
from .video_analyzer import VideoAnalyzer


def normalize_path(path_str: str) -> str:
    """Normalize path strings by removing quotes and unescaping backslashes."""
    if not path_str:
        return path_str
    
    # Strip surrounding quotes
    if (path_str.startswith('"') and path_str.endswith('"')) or \
       (path_str.startswith("'") and path_str.endswith("'")):
        path_str = path_str[1:-1]
    
    # Unescape backslash-escaped spaces and other common shell escapes
    path_str = path_str.replace('\\ ', ' ')
    path_str = path_str.replace('\\(', '(')
    path_str = path_str.replace('\\)', ')')
    
    return path_str


def get_concurrency_help() -> str:
    """Generate dynamic help text for concurrency option."""
    try:
        config = Config.load()
        return f"Concurrent requests for batch processing (max: {config.max_concurrency})"
    except Exception:
        return "Concurrent requests for batch processing"


@click.group(invoke_without_command=True)
@click.pass_context
@click.option(
    "--type",
    "type_",
    "-t",
    type=click.Choice(["image", "audio", "video"]),
    help="Analysis type: image, audio, or video",
)
@click.option(
    "--model",
    "-m",
    default="gemini/gemini-2.5-flash",
    help="LiteLLM model [default: gemini/gemini-2.5-flash]",
)
@click.option(
    "--path",
    "-p",
    type=click.Path(),
    help="Media file or directory path",
)
@click.option(
    "--files",
    "-f",
    multiple=True,
    help="Explicit list of media files to analyze",
)
@click.option(
    "--audio-mode",
    type=click.Choice(["transcript", "description"]),
    help="Audio analysis mode (required for audio type)",
)
@click.option(
    "--video-mode",
    type=click.Choice(["description"]),
    help="Video analysis mode (required for video type)",
)
@click.option(
    "--word-count",
    "-w",
    default=100,
    help="Target description word count",
)
@click.option("--prompt", help="Custom analysis prompt")
@click.option(
    "--system",
    type=click.Path(),
    help="Path to custom system prompt file (overrides default for media type)"
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "markdown", "text", "stream-json"]),
    default="json",
    help="Output format",
)
@click.option(
    "--input-format",
    type=click.Choice(["stream-json"]),
    help="Input format for streaming mode (requires --output stream-json and -p)",
)
@click.option("--output-file", help="Save results to file")
@click.option("--recursive", "-r", is_flag=True, help="Process directories recursively")
@click.option(
    "--concurrency", "-c", default=10, help=get_concurrency_help()
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default="WARNING",
    help="Logging level",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed output including model, prompt, and metadata",
)
@click.version_option(package_name="multimodal-analyzer")
def main(
    ctx: click.Context,
    type_: str | None,
    model: str,
    path: str | None,
    files: tuple[str, ...],
    audio_mode: str | None,
    video_mode: str | None,
    word_count: int,
    prompt: str | None,
    system: str | None,
    output: str,
    input_format: str | None,
    output_file: str | None,
    recursive: bool,
    concurrency: int,
    log_level: str,
    verbose: bool,
) -> None:
    """AI-powered media analysis tool supporting image, audio, and video content."""

    # If a subcommand was invoked, return early
    if ctx.invoked_subcommand is not None:
        return
    
    # Require --type for main analysis functionality
    if type_ is None:
        raise click.ClickException("--type is required when not using subcommands")

    # Validate mutually exclusive options
    if path and files:
        raise click.ClickException("Cannot specify both --path and --files")
    
    # Validate streaming mode requirements
    if input_format == "stream-json":
        if output != "stream-json":
            raise click.ClickException("--input-format stream-json requires --output stream-json")
        if not path:
            raise click.ClickException("--input-format stream-json requires -p flag")
        if files:
            raise click.ClickException("--input-format stream-json cannot be used with --files")
        if output_file:
            raise click.ClickException("--input-format stream-json cannot be used with --output-file")
    
    if output == "stream-json" and not input_format:
        raise click.ClickException("--output stream-json requires --input-format stream-json")
    
    # Standard validation for non-streaming mode
    if not input_format and not path and not files:
        raise click.ClickException("Must specify either --path or --files")

    # Validate mode requirements
    if type_ == "audio" and not audio_mode:
        raise click.ClickException("--audio-mode is required when --type is 'audio'")

    if type_ == "video" and not video_mode:
        raise click.ClickException("--video-mode is required when --type is 'video'")

    if type_ == "image" and audio_mode:
        raise click.ClickException(
            "--audio-mode should not be used when --type is 'image'"
        )

    if type_ == "image" and video_mode:
        raise click.ClickException(
            "--video-mode should not be used when --type is 'image'"
        )

    if type_ == "audio" and video_mode:
        raise click.ClickException(
            "--video-mode should not be used when --type is 'audio'"
        )

    if type_ == "video" and audio_mode:
        raise click.ClickException(
            "--audio-mode should not be used when --type is 'video'"
        )

    # Configure logging
    logger.remove()
    logger.add(lambda msg: click.echo(msg, err=True), level=log_level)

    # Enable LiteLLM verbose logging for DEBUG level
    if log_level == "DEBUG":
        litellm.set_verbose = True

    # Load configuration
    config = Config.load()

    # Validate concurrency limit
    if concurrency > config.max_concurrency:
        raise click.ClickException(
            f"Concurrency value {concurrency} exceeds maximum limit of {config.max_concurrency}"
        )

    # Check for streaming mode
    if input_format == "stream-json":
        # Handle streaming mode
        if type_ == "image":
            analyzer = ImageAnalyzer(config, system)
            try:
                asyncio.run(
                    analyzer.analyze_streaming(
                        model=model,
                        word_count=word_count,
                        prompt=prompt,
                        verbose=verbose,
                    )
                )
            except Exception as e:
                logger.error(f"Streaming image analysis failed: {e}")
                raise click.ClickException(str(e))
        elif type_ == "audio":
            # TODO: Implement audio streaming analysis
            raise click.ClickException("Audio streaming analysis not yet implemented")
        elif type_ == "video":
            # TODO: Implement video streaming analysis
            raise click.ClickException("Video streaming analysis not yet implemented")
        return

    # Create appropriate analyzer for regular (non-streaming) mode
    if type_ == "image":
        analyzer = ImageAnalyzer(config, system)

        # Run image analysis
        try:
            result = asyncio.run(
                analyzer.analyze(
                    model=model,
                    path=Path(normalize_path(path)) if path else None,
                    file_list=[Path(normalize_path(f)) for f in files] if files else None,
                    word_count=word_count,
                    prompt=prompt,
                    output_format=output,
                    output_file=output_file,
                    recursive=recursive,
                    concurrency=concurrency,
                    verbose=verbose,
                )
            )

            if not output_file:
                click.echo(result)

        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            raise click.ClickException(str(e))

    elif type_ == "audio":
        analyzer = AudioAnalyzer(config, system)

        # Run audio analysis
        try:
            result = asyncio.run(
                analyzer.analyze(
                    model=model,
                    path=Path(normalize_path(path)) if path else None,
                    file_list=[Path(normalize_path(f)) for f in files] if files else None,
                    mode=audio_mode,
                    word_count=word_count,
                    prompt=prompt,
                    output_format=output,
                    output_file=output_file,
                    recursive=recursive,
                    concurrency=concurrency,
                    verbose=verbose,
                )
            )

            if not output_file:
                click.echo(result)

        except Exception as e:
            logger.error(f"Audio analysis failed: {e}")
            raise click.ClickException(str(e))

    elif type_ == "video":
        analyzer = VideoAnalyzer(config, system)

        # Run video analysis
        try:
            result = asyncio.run(
                analyzer.analyze(
                    model=model,
                    path=Path(normalize_path(path)) if path else None,
                    file_list=[Path(normalize_path(f)) for f in files] if files else None,
                    mode=video_mode,
                    word_count=word_count,
                    prompt=prompt,
                    output_format=output,
                    output_file=output_file,
                    recursive=recursive,
                    concurrency=concurrency,
                    verbose=verbose,
                )
            )

            if not output_file:
                click.echo(result)

        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            raise click.ClickException(str(e))


@main.group()
def auth() -> None:
    """Authentication management commands."""


@auth.command()
@click.option(
    "--no-browser", 
    is_flag=True, 
    help="Don't open browser automatically (display URL instead)"
)
@click.option(
    "--callback-host", 
    default="localhost", 
    help="OAuth callback host [default: localhost]"
)
@click.option(
    "--callback-port", 
    default=8080, 
    type=int,
    help="OAuth callback port [default: 8080]"
)
def login(no_browser: bool, callback_host: str, callback_port: int) -> None:
    """Authenticate with Google OAuth."""
    try:
        from .auth import GoogleOAuthManager
        
        # Create OAuth manager with custom settings if provided
        oauth_manager = GoogleOAuthManager(
            callback_host=callback_host,
            callback_port=callback_port
        )
        
        click.echo("🔐 Starting Google OAuth authentication...")
        
        # Run authentication
        result = asyncio.run(oauth_manager.authenticate(open_browser=not no_browser))
        
        if result:
            click.echo("✅ Google OAuth authentication successful!")
            click.echo("You can now use Gemini models with OAuth authentication.")
        else:
            click.echo("❌ Authentication failed.")
            raise click.ClickException("OAuth authentication failed")
            
    except ImportError:
        click.echo("❌ OAuth dependencies not available. Please reinstall with OAuth support.")
        raise click.ClickException("OAuth not available")
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        click.echo(f"❌ Authentication failed: {e}")
        raise click.ClickException(str(e))


@auth.command()
def logout() -> None:
    """Clear stored OAuth credentials."""
    try:
        from .auth import GoogleOAuthManager
        
        oauth_manager = GoogleOAuthManager()
        oauth_manager.logout()
        
        click.echo("✅ Successfully logged out - OAuth tokens cleared")
        
    except ImportError:
        click.echo("❌ OAuth dependencies not available.")
        raise click.ClickException("OAuth not available")
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        click.echo(f"❌ Logout failed: {e}")
        raise click.ClickException(str(e))


@auth.command()
@click.option(
    "--verbose", 
    "-v", 
    is_flag=True, 
    help="Show detailed authentication information"
)
def status(verbose: bool) -> None:
    """Show current authentication status."""
    try:
        from .auth import GoogleAuthProvider
        
        # Load config to get OAuth settings
        config = Config.load()
        
        # Create auth provider
        auth_provider = GoogleAuthProvider.from_environment()
        
        # Get status
        status_info = auth_provider.get_auth_status()
        
        click.echo("🔍 Authentication Status:")
        click.echo(f"  API Key Available: {'✅' if status_info['has_api_key'] else '❌'}")
        click.echo(f"  OAuth Authenticated: {'✅' if status_info['oauth_authenticated'] else '❌'}")
        click.echo(f"  Overall Status: {'✅ Authenticated' if status_info['authenticated'] else '❌ Not Authenticated'}")
        click.echo(f"  Auth Method: {status_info['auth_method']}")
        
        if verbose:
            oauth_details = status_info.get("oauth_details", {})
            
            if "expires_at" in oauth_details:
                click.echo(f"  Token Expires: {oauth_details['expires_at']}")
            if "has_refresh_token" in oauth_details:
                click.echo(f"  Has Refresh Token: {'✅' if oauth_details['has_refresh_token'] else '❌'}")
        
        # Show usage instructions if not authenticated
        if not status_info["authenticated"]:
            click.echo("\n💡 To authenticate:")
            click.echo("  Run: multimodal-analyzer auth login")
            click.echo("  Or set GEMINI_API_KEY environment variable")
        
    except ImportError:
        click.echo("❌ OAuth dependencies not available.")
        raise click.ClickException("OAuth not available")
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        click.echo(f"❌ Status check failed: {e}")
        raise click.ClickException(str(e))


if __name__ == "__main__":
    main()
