"""Simple batch processing demo for image analysis."""

import asyncio
import json
from pathlib import Path

from multimodal_analyzer_cli.config import Config
from multimodal_analyzer_cli.image_analyzer import ImageAnalyzer


async def main():
    """Demo batch processing of images with progress bar."""

    # Load configuration
    config = Config.load()

    # Initialize image analyzer
    analyzer = ImageAnalyzer(config)

    # Define batch processing parameters
    model = "gemini/gemini-2.5-flash"
    batch_path = Path("data/image_batch")

    print(f"Starting batch analysis of images in {batch_path}")
    print(f"Using model: {model}")
    print("-" * 50)

    try:
        # Run batch analysis with progress tracking
        results = await analyzer.analyze(
            model=model,
            path=batch_path,
            word_count=100,
            output_format="json",
            concurrency=5,
            verbose=True
        )

        # Parse and display results
        parsed_results = json.loads(results)

        print(f"\nBatch analysis completed!")
        print(f"Processed {len(parsed_results)} images")

        # Show summary
        success_count = sum(1 for r in parsed_results if r.get("success", False))
        print(f"Success rate: {success_count}/{len(parsed_results)}")

        # Display sample result
        if parsed_results:
            print(f"\nSample result for {parsed_results[0].get('image_path', 'unknown')}:")
            print(f"Analysis: {parsed_results[0].get('analysis', 'No analysis')[:200]}...")

    except Exception as e:
        print(f"Error during batch processing: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
