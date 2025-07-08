import asyncio
from pathlib import Path

import click
import litellm
from loguru import logger

from .audio_analyzer import AudioAnalyzer
from .config import Config
from .image_analyzer import ImageAnalyzer
from .video_analyzer import VideoAnalyzer


def get_concurrency_help() -> str:
    """Generate dynamic help text for concurrency option."""
    try:
        config = Config.load()
        return f"Concurrent requests for batch processing (max: {config.max_concurrency})"
    except Exception:
        return "Concurrent requests for batch processing"


@click.command()
@click.option(
    "--type",
    "type_",
    "-t",
    required=True,
    type=click.Choice(["image", "audio", "video"]),
    help="Analysis type: image, audio, or video",
)
@click.option(
    "--model",
    "-m",
    required=True,
    help="LiteLLM model (e.g., gemini/gemini-2.5-flash, gpt-4o-mini)",
)
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True),
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
    help="Target description word count (for image, audio description, or video description mode)",
)
@click.option("--prompt", help="Custom analysis prompt")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "markdown", "text"]),
    default="json",
    help="Output format",
)
@click.option("--output-file", help="Save results to file")
@click.option("--recursive", "-r", is_flag=True, help="Process directories recursively")
@click.option(
    "--concurrency", "-c", default=10, help=get_concurrency_help()
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default="INFO",
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
    type_: str,
    model: str,
    path: str | None,
    files: tuple[str, ...],
    audio_mode: str | None,
    video_mode: str | None,
    word_count: int,
    prompt: str | None,
    output: str,
    output_file: str | None,
    recursive: bool,
    concurrency: int,
    log_level: str,
    verbose: bool,
) -> None:
    """AI-powered media analysis tool supporting image, audio, and video content."""

    # Validate mutually exclusive options
    if path and files:
        raise click.ClickException("Cannot specify both --path and --files")
    if not path and not files:
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

    # Create appropriate analyzer
    if type_ == "image":
        analyzer = ImageAnalyzer(config)

        # Run image analysis
        try:
            result = asyncio.run(
                analyzer.analyze(
                    model=model,
                    path=Path(path) if path else None,
                    file_list=[Path(f) for f in files] if files else None,
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
        analyzer = AudioAnalyzer(config)

        # Run audio analysis
        try:
            result = asyncio.run(
                analyzer.analyze(
                    model=model,
                    path=Path(path) if path else None,
                    file_list=[Path(f) for f in files] if files else None,
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
        analyzer = VideoAnalyzer(config)

        # Run video analysis
        try:
            result = asyncio.run(
                analyzer.analyze(
                    model=model,
                    path=Path(path) if path else None,
                    file_list=[Path(f) for f in files] if files else None,
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


if __name__ == "__main__":
    main()
