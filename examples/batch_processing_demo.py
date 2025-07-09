"""Simple batch processing demo using the ImageAnalyzer class directly."""

import asyncio
from pathlib import Path

from multimodal_analyzer_cli.config import Config
from multimodal_analyzer_cli.image_analyzer import ImageAnalyzer


async def main():
    """Demo batch processing of images using ImageAnalyzer directly."""

    # Initialize configuration
    config = Config()
    model = "gemini/gemini-2.5-flash"
    batch_path = Path("data/image_batch")

    print(f"Starting batch analysis of images in {batch_path}")
    print(f"Using model: {model}")
    print("-" * 50)

    # Create analyzer instance
    analyzer = ImageAnalyzer(config)

    try:
        # Analyze batch of images
        results = await analyzer.analyze(
            model=model,
            path=batch_path,
            prompt="describe the image in 10 words",
            word_count=10,
            output_format="json",
            concurrency=2,
            verbose=True
        )

        print("Batch analysis completed!")
        print("-" * 50)

        # Parse results
        import json
        parsed_results = json.loads(results)

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
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)