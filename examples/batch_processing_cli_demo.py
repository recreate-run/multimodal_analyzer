"""Simple batch processing demo using CLI subprocess."""

import json
import subprocess
import sys
from pathlib import Path


def main():
    """Demo batch processing of images using CLI subprocess."""

    # Define CLI command parameters
    model = "gemini/gemini-2.5-flash"
    batch_path = "data/image_batch"

    print(f"Starting batch analysis of images in {batch_path}")
    print(f"Using model: {model}")
    print("Running CLI via subprocess...")
    print("-" * 50)

    # Build CLI command
    cmd = [
        "uv", "run", "multimodal-analyzer",
        "--prompt", "describe the image in 10 words",
        "--type", "image",
        "--model", model,
        "--path", batch_path,
        "--output", "json",
        "--concurrency", "2",
        "--verbose"
    ]

    try:
        # Run CLI command and capture output
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            text=True,
            check=True
        )

        print("CLI execution completed!")
        print("-" * 50)

        # Parse JSON output
        parsed_results = json.loads(result.stdout)

        print(f"Processed {len(parsed_results)} images")

        # Show summary
        success_count = sum(1 for r in parsed_results if r.get("success", False))
        print(f"Success rate: {success_count}/{len(parsed_results)}")

        # Display sample result
        if parsed_results:
            print(f"\nSample result for {parsed_results[0].get('image_path', 'unknown')}:")
            print(f"Analysis: {parsed_results[0].get('analysis', 'No analysis')[:200]}...")

    except subprocess.CalledProcessError as e:
        print(f"CLI command failed with return code {e.returncode}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON output: {e}")
        print(f"Raw output: {result.stdout}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()