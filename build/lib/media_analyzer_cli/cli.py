import asyncio
from pathlib import Path

import click
from loguru import logger

from .audio_analyzer import AudioAnalyzer
from .config import Config
from .image_analyzer import ImageAnalyzer


@click.command()
@click.option(
    "--type",
    "-t",
    required=True,
    type=click.Choice(["image", "audio"]),
    help="Analysis type: image or audio",
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
    required=True,
    type=click.Path(exists=True),
    help="Media file or directory path",
)
@click.option(
    "--audio-mode",
    type=click.Choice(["transcript", "description"]),
    help="Audio analysis mode (required for audio type)",
)
@click.option(
    "--word-count",
    "-w",
    default=100,
    help="Target description word count (for image or audio description mode)",
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
    "--concurrency", "-c", default=3, help="Concurrent requests for batch processing"
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
@click.version_option(package_name="media-analyzer")
def main(
    type: str,
    model: str,
    path: str,
    audio_mode: str | None,
    word_count: int,
    prompt: str | None,
    output: str,
    output_file: str | None,
    recursive: bool,
    concurrency: int,
    log_level: str,
    verbose: bool,
) -> None:
    """AI-powered media analysis tool supporting both image and audio content."""

    # Validate audio mode requirement
    if type == "audio" and not audio_mode:
        raise click.ClickException("--audio-mode is required when --type is 'audio'")

    if type == "image" and audio_mode:
        raise click.ClickException(
            "--audio-mode should not be used when --type is 'image'"
        )

    # Configure logging
    logger.remove()
    logger.add(lambda msg: click.echo(msg, err=True), level=log_level)

    # Load configuration
    config = Config.load()

    # Create appropriate analyzer
    if type == "image":
        analyzer = ImageAnalyzer(config)

        # Run image analysis
        try:
            result = asyncio.run(
                analyzer.analyze(
                    model=model,
                    path=Path(path),
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

    elif type == "audio":
        analyzer = AudioAnalyzer(config)

        # Run audio analysis
        try:
            result = asyncio.run(
                analyzer.analyze(
                    model=model,
                    path=Path(path),
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


if __name__ == "__main__":
    main()
