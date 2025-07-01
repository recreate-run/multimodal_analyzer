import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from loguru import logger
from tqdm.asyncio import tqdm

from .config import Config
from .models.litellm_model import LiteLLMModel
from .utils.image import find_images, validate_image_file
from .utils.prompts import PromptManager
from .utils.output import OutputFormatter, ResultProcessor


class ImageAnalyzer:
    """Core image analysis functionality."""

    def __init__(self, config: Config):
        self.config = config
        self.model = LiteLLMModel(config)

    async def analyze(
        self,
        model: str,
        path: Path,
        word_count: int = 100,
        prompt: Optional[str] = None,
        output_format: str = "json",
        output_file: Optional[str] = None,
        recursive: bool = False,
        concurrency: int = 3,
        verbose: bool = False,
    ) -> str:
        """Analyze image(s) and return results."""

        # Validate configuration
        self.config.validate()

        # Get the prompt to use
        analysis_prompt = prompt or self.config.default_prompt
        analysis_prompt = PromptManager.add_word_count_instruction(
            analysis_prompt, word_count
        )

        # Find images to process
        image_paths = list(
            find_images(path, recursive, self.config.supported_image_formats)
        )

        if not image_paths:
            raise ValueError(f"No supported image files found in {path}")

        logger.info(f"Found {len(image_paths)} image(s) to analyze")

        # Process images
        if len(image_paths) == 1:
            # Single image processing
            results = [
                await self._analyze_single_image(
                    model, image_paths[0], analysis_prompt, word_count
                )
            ]
        else:
            # Batch processing with concurrency and progress tracking
            results = await self._analyze_batch_with_progress(
                model, image_paths, analysis_prompt, word_count, concurrency
            )

        # Format output
        formatted_output = self._format_output(results, output_format, verbose)

        # Save to file if requested
        if output_file:
            OutputFormatter.save_to_file(formatted_output, output_file)
            logger.info(f"Results saved to {output_file}")

        return formatted_output

    async def _analyze_single_image(
        self, model: str, image_path: Path, prompt: str, word_count: int
    ) -> Dict[str, Any]:
        """Analyze a single image."""
        logger.info(f"Analyzing {image_path.name} with {model}")

        try:
            result = await self.model.analyze_image(
                model, image_path, prompt, word_count
            )
            logger.info(f"Analysis completed for {image_path.name}")
            return result
        except Exception as e:
            logger.error(f"Analysis failed for {image_path.name}: {e}")
            return {
                "image_path": str(image_path),
                "model": model,
                "prompt": prompt,
                "word_count": word_count,
                "analysis": None,
                "success": False,
                "error": str(e),
            }

    async def _analyze_batch(
        self,
        model: str,
        image_paths: List[Path],
        prompt: str,
        word_count: int,
        concurrency: int,
    ) -> List[Dict[str, Any]]:
        """Analyze multiple images with concurrency control."""
        logger.info(
            f"Starting batch analysis of {len(image_paths)} images with concurrency {concurrency}"
        )

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(min(concurrency, self.config.max_concurrency))

        async def analyze_with_semaphore(image_path: Path) -> Dict[str, Any]:
            async with semaphore:
                return await self._analyze_single_image(
                    model, image_path, prompt, word_count
                )

        # Process all images concurrently
        tasks = [analyze_with_semaphore(image_path) for image_path in image_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task failed for {image_paths[i].name}: {result}")
                processed_results.append(
                    {
                        "image_path": str(image_paths[i]),
                        "model": model,
                        "prompt": prompt,
                        "word_count": word_count,
                        "analysis": None,
                        "success": False,
                        "error": str(result),
                    }
                )
            else:
                processed_results.append(result)

        logger.info(
            f"Batch analysis completed. Success rate: {sum(1 for r in processed_results if r['success'])}/{len(processed_results)}"
        )
        return processed_results

    async def _analyze_batch_with_progress(
        self,
        model: str,
        image_paths: List[Path],
        prompt: str,
        word_count: int,
        concurrency: int,
    ) -> List[Dict[str, Any]]:
        """Analyze multiple images with concurrency control and progress tracking."""
        logger.info(
            f"Starting batch analysis of {len(image_paths)} images with concurrency {concurrency}"
        )

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(min(concurrency, self.config.max_concurrency))

        async def analyze_with_semaphore_and_progress(
            image_path: Path, progress_bar
        ) -> Dict[str, Any]:
            async with semaphore:
                try:
                    result = await self._analyze_single_image(
                        model, image_path, prompt, word_count
                    )
                    progress_bar.set_postfix(
                        current=image_path.name,
                        status="✓" if result["success"] else "✗",
                    )
                    return result
                finally:
                    progress_bar.update(1)

        # Create progress bar
        progress_bar = tqdm(
            total=len(image_paths), desc="Analyzing images", unit="img", colour="green"
        )

        try:
            # Process all images concurrently with progress tracking
            tasks = [
                analyze_with_semaphore_and_progress(image_path, progress_bar)
                for image_path in image_paths
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            progress_bar.close()

        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task failed for {image_paths[i].name}: {result}")
                processed_results.append(
                    {
                        "image_path": str(image_paths[i]),
                        "model": model,
                        "prompt": prompt,
                        "word_count": word_count,
                        "analysis": None,
                        "success": False,
                        "error": str(result),
                    }
                )
            else:
                processed_results.append(result)

        success_count = sum(1 for r in processed_results if r["success"])
        logger.info(
            f"Batch analysis completed. Success rate: {success_count}/{len(processed_results)}"
        )
        return processed_results

    def _format_output(
        self, results: List[Dict[str, Any]], output_format: str, verbose: bool = False
    ) -> str:
        """Format results according to the specified output format."""
        if output_format == "json":
            return OutputFormatter.format_json(results, verbose=verbose)
        elif output_format == "markdown":
            return OutputFormatter.format_markdown(results, verbose=verbose)
        elif output_format == "csv":
            return OutputFormatter.format_csv(results, verbose=verbose)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
