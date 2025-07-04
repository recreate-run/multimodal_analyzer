#!/usr/bin/env python3
"""
Example usage script for Media Analyzer CLI.

This script demonstrates how to use the Media Analyzer CLI programmatically
and provides examples of different analysis scenarios.
"""

import asyncio
import os
from pathlib import Path
from PIL import Image

from media_analyzer_cli.image_analyzer import ImageAnalyzer
from media_analyzer_cli.config import Config


async def create_sample_image(
    path: Path, color: str = "red", size: tuple = (400, 300)
) -> None:
    """Create a sample image for testing."""
    img = Image.new("RGB", size, color=color)

    # Add some simple shapes for more interesting analysis
    from PIL import ImageDraw

    draw = ImageDraw.Draw(img)

    # Draw some shapes
    draw.rectangle([50, 50, 150, 100], fill="blue")
    draw.ellipse([200, 80, 300, 180], fill="green")
    draw.polygon([(320, 50), (370, 50), (345, 100)], fill="yellow")

    img.save(path)
    print(f"Created sample image: {path}")


async def example_single_image_analysis():
    """Example: Analyze a single image."""
    print("\n=== Single Image Analysis Example ===")

    # Create sample image
    sample_path = Path("sample_image.jpg")
    await create_sample_image(sample_path, "lightblue")

    try:
        # Load configuration
        config = Config.load()
        analyzer = ImageAnalyzer(config)

        # Analyze the image
        result = await analyzer.analyze(
            model="gemini/gemini-2.5-flash",  # You can change this model
            path=sample_path,
            word_count=150,
            prompt="Describe the colors, shapes, and composition of this image.",
            output_format="json",
        )

        print("Analysis Result:")
        print(result)

    except Exception as e:
        print(f"Error: {e}")
        print("Note: You need to set appropriate API keys in environment variables")
    finally:
        # Clean up
        if sample_path.exists():
            sample_path.unlink()


async def example_batch_analysis():
    """Example: Analyze multiple images in batch."""
    print("\n=== Batch Analysis Example ===")

    # Create sample images directory
    samples_dir = Path("sample_images")
    samples_dir.mkdir(exist_ok=True)

    # Create multiple sample images
    colors = ["red", "green", "blue", "yellow", "purple"]
    sample_paths = []

    for i, color in enumerate(colors):
        sample_path = samples_dir / f"sample_{i+1}_{color}.jpg"
        await create_sample_image(sample_path, color)
        sample_paths.append(sample_path)

    try:
        # Load configuration
        config = Config.load()
        analyzer = ImageAnalyzer(config)

        # Analyze batch with progress tracking
        result = await analyzer.analyze(
            model="gemini/gemini-2.5-flash",
            path=samples_dir,
            word_count=100,
            output_format="markdown",
            output_file="batch_results.md",
            concurrency=2,
        )

        print("Batch analysis completed!")
        print("Results saved to: batch_results.md")

    except Exception as e:
        print(f"Error: {e}")
        print("Note: You need to set appropriate API keys in environment variables")
    finally:
        # Clean up
        for sample_path in sample_paths:
            if sample_path.exists():
                sample_path.unlink()
        if samples_dir.exists():
            samples_dir.rmdir()


async def example_different_output_formats():
    """Example: Generate different output formats."""
    print("\n=== Different Output Formats Example ===")

    # Create sample image
    sample_path = Path("format_test.png")
    await create_sample_image(sample_path, "orange", (300, 200))

    try:
        config = Config.load()
        analyzer = ImageAnalyzer(config)

        # Generate different formats
        formats = ["json", "markdown", "text"]

        for format_type in formats:
            result = await analyzer.analyze(
                model="gemini/gemini-2.5-flash",
                path=sample_path,
                word_count=80,
                output_format=format_type,
                output_file=f"result.{format_type if format_type != 'text' else 'txt'}",
            )

            print(f"\n{format_type.upper()} format saved to result.{format_type if format_type != 'text' else 'txt'}")
            if format_type == "json":
                print("Preview:")
                print(result[:200] + "..." if len(result) > 200 else result)

    except Exception as e:
        print(f"Error: {e}")
        print("Note: You need to set appropriate API keys in environment variables")
    finally:
        # Clean up
        if sample_path.exists():
            sample_path.unlink()


async def example_verbose_output():
    """Example: Demonstrate verbose vs non-verbose output."""
    print("\n=== Verbose Output Example ===")

    # Create sample image
    sample_path = Path("verbose_test.jpg")
    await create_sample_image(sample_path, "cyan", (250, 200))

    try:
        config = Config.load()
        analyzer = ImageAnalyzer(config)

        # Non-verbose analysis
        print("\n--- Non-verbose output (default) ---")
        result_minimal = await analyzer.analyze(
            model="gemini/gemini-2.5-flash",
            path=sample_path,
            word_count=50,
            output_format="json",
            verbose=False,
        )
        print("Minimal output (only essential fields):")
        print(result_minimal)

        # Verbose analysis
        print("\n--- Verbose output (--verbose flag) ---")
        result_verbose = await analyzer.analyze(
            model="gemini/gemini-2.5-flash",
            path=sample_path,
            word_count=50,
            prompt="Describe this image in detail.",
            output_format="json",
            verbose=True,
        )
        print("Verbose output (includes model, prompt, metadata):")
        print(result_verbose)

        # Markdown verbose comparison
        print("\n--- Markdown format comparison ---")
        md_minimal = await analyzer.analyze(
            model="gemini/gemini-2.5-flash",
            path=sample_path,
            word_count=50,
            output_format="markdown",
            verbose=False,
        )
        print("Minimal markdown:")
        print(md_minimal[:300] + "..." if len(md_minimal) > 300 else md_minimal)

        md_verbose = await analyzer.analyze(
            model="gemini/gemini-2.5-flash",
            path=sample_path,
            word_count=50,
            prompt="Describe this image.",
            output_format="markdown",
            verbose=True,
        )
        print("\nVerbose markdown:")
        print(md_verbose[:300] + "..." if len(md_verbose) > 300 else md_verbose)

    except Exception as e:
        print(f"Error: {e}")
        print("Note: You need to set appropriate API keys in environment variables")
    finally:
        # Clean up
        if sample_path.exists():
            sample_path.unlink()


def example_configuration():
    """Example: Configuration management."""
    print("\n=== Configuration Example ===")

    # Load default configuration
    config = Config.load()

    print("Current configuration:")
    print(f"  Default model: {config.default_model}")
    print(f"  Default word count: {config.default_word_count}")
    print(f"  Max concurrency: {config.max_concurrency}")
    print(f"  Max file size: {config.max_file_size_mb}MB")
    print(f"  Supported formats: {', '.join(config.supported_image_formats)}")

    # Validate configuration
    try:
        config.validate()
        print("  Configuration is valid ✓")
    except ValueError as e:
        print(f"  Configuration error: {e}")

    # Example of getting API key for a model
    models_to_test = [
        "gpt-4o-mini",
        "claude-3-sonnet-20240229",
        "gemini/gemini-2.5-flash",
    ]

    print("\nAPI Key Status:")
    for model in models_to_test:
        api_key = config.get_api_key(model)
        status = "✓ Available" if api_key else "✗ Missing"
        print(f"  {model}: {status}")


async def main():
    """Run all examples."""
    print("Media Analyzer CLI - Example Usage")
    print("=" * 50)

    # Configuration example (always runs)
    example_configuration()

    # Check if we have any API keys before running analysis examples
    config = Config.load()
    has_api_key = any(
        [config.openai_api_key, config.anthropic_api_key, config.gemini_api_key]
    )

    if not has_api_key:
        print("\n⚠️  No API keys found!")
        print(
            "Set API keys in environment variables or .env file to run analysis examples:"
        )
        print("  - OPENAI_API_KEY for OpenAI models")
        print("  - ANTHROPIC_API_KEY for Anthropic models")
        print("  - GEMINI_API_KEY for Google models")
        print("\nSkipping analysis examples...")
        return

    # Run analysis examples
    await example_single_image_analysis()
    await example_batch_analysis()
    await example_different_output_formats()
    await example_verbose_output()

    print("\n" + "=" * 50)
    print("All examples completed!")
    print("\nTo use the CLI directly, try:")
    print("uv run media-analyzer --model gemini/gemini-2.5-flash --path your_image.jpg")
    print("\nFor verbose output with detailed metadata:")
    print(
        "uv run media-analyzer --model gemini/gemini-2.5-flash --path your_image.jpg --verbose"
    )


if __name__ == "__main__":
    asyncio.run(main())
