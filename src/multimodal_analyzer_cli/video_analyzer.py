"""Video analysis functionality for the media analyzer."""

import asyncio
from pathlib import Path
from typing import Any

from loguru import logger
from tqdm.asyncio import tqdm

from .config import Config
from .models.litellm_model import LiteLLMModel
from .utils.file_discovery import validate_file_list
from .utils.output import OutputFormatter
from .utils.video import find_videos, get_video_info, validate_video_file


class VideoAnalyzer:
    """Video analysis using Gemini models with multimodal capabilities."""

    def __init__(self, config: Config, custom_system_prompt: str | None = None):
        self.config = config
        self.model = LiteLLMModel(config, custom_system_prompt)
        self.output_formatter = OutputFormatter()

    async def analyze_single_video(
        self,
        model: str,
        video_path: Path,
        mode: str,
        word_count: int = 100,
        prompt: str | None = None,
        verbose: bool = False
    ) -> dict[str, Any]:
        """Analyze a single video file."""
        
        logger.info(f"Starting video analysis: {video_path}")
        
        # Validate mode early
        if mode != "description":
            raise ValueError(f"Invalid mode: {mode}. Video analysis only supports 'description' mode")
        
        # Only support Gemini models for video analysis
        if not model.startswith("gemini"):
            raise ValueError(
                f"Video analysis only supports Gemini models. Received: {model}"
            )
        
        # Validate video file
        if not validate_video_file(video_path):
            raise ValueError("Video file validation failed")
        
        # Get video information
        video_info = get_video_info(video_path)
        
        logger.info(f"Analyzing video with Gemini model: {model}")
        
        result = await self.model.analyze_video(
            model=model,
            video_path=video_path,
            mode=mode,
            prompt=prompt,
            word_count=word_count
        )
        
        if not result["success"]:
            raise RuntimeError(result["error"])
        
        # Add video info to the result
        result["video_info"] = video_info
        
        # Add verbose information if requested
        if verbose:
            result["verbose"] = {
                "original_file": str(video_path),
                "video_info": video_info
            }
        
        logger.info(f"Video analysis completed successfully: {video_path}")
        return result

    async def analyze_batch(
        self,
        model: str,
        video_files: list[Path],
        mode: str,
        word_count: int = 100,
        prompt: str | None = None,
        concurrency: int = 3,
        verbose: bool = False
    ) -> list[dict[str, Any]]:
        """Analyze multiple video files with concurrency control."""
        
        logger.info(f"Starting batch analysis of {len(video_files)} video files")
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(min(concurrency, self.config.max_concurrency))
        
        async def analyze_with_semaphore(video_path: Path) -> dict[str, Any]:
            async with semaphore:
                return await self.analyze_single_video(
                    model=model,
                    video_path=video_path,
                    mode=mode,
                    word_count=word_count,
                    prompt=prompt,
                    verbose=verbose
                )
        
        # Run all analyses concurrently - raise exceptions immediately
        tasks = [analyze_with_semaphore(video_path) for video_path in video_files]
        results = await asyncio.gather(*tasks)
        
        success_count = sum(1 for r in results if r["success"])
        logger.info(f"Batch analysis completed. Success: {success_count}/{len(results)}")
        return results

    async def analyze_batch_with_progress(
        self,
        model: str,
        video_files: list[Path],
        mode: str,
        word_count: int = 100,
        prompt: str | None = None,
        concurrency: int = 3,
        verbose: bool = False
    ) -> list[dict[str, Any]]:
        """Analyze multiple video files with concurrency control and progress tracking."""
        
        logger.info(f"Starting batch analysis of {len(video_files)} video files with concurrency {concurrency}")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(min(concurrency, self.config.max_concurrency))
        
        async def analyze_with_semaphore_and_progress(
            video_path: Path, progress_bar
        ) -> dict[str, Any]:
            async with semaphore:
                try:
                    result = await self.analyze_single_video(
                        model, video_path, mode, word_count, prompt, verbose
                    )
                    progress_bar.set_postfix(
                        current=video_path.name,
                        status="✓" if result["success"] else "✗",
                    )
                    return result
                finally:
                    progress_bar.update(1)
        
        # Create progress bar
        progress_bar = tqdm(
            total=len(video_files), desc="Analyzing videos", unit="video", colour="blue"
        )
        
        try:
            # Process all videos concurrently with progress tracking
            tasks = [
                analyze_with_semaphore_and_progress(video_path, progress_bar)
                for video_path in video_files
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            progress_bar.close()
        
        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task failed for {video_files[i].name}: {result}")
                processed_results.append(
                    {
                        "video_path": str(video_files[i]),
                        "model": model,
                        "mode": mode,
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

    async def analyze(
        self,
        model: str,
        mode: str,
        path: Path | None = None,
        file_list: list[Path] | None = None,
        word_count: int = 100,
        prompt: str | None = None,
        output_format: str = "json",
        output_file: str | None = None,
        recursive: bool = False,
        concurrency: int = 3,
        verbose: bool = False
    ) -> str:
        """Main analysis method that handles files, directories, and explicit file lists."""
        
        # Validate configuration
        self.config.validate()
        self.config.validate_api_keys(model)
        
        if file_list:
            # File list analysis
            video_files = validate_file_list([str(f) for f in file_list], "video")
            
            if len(video_files) == 1:
                # Single video processing
                result = await self.analyze_single_video(
                    model=model,
                    video_path=video_files[0],
                    mode=mode,
                    word_count=word_count,
                    prompt=prompt,
                    verbose=verbose
                )
                results = [result]
            else:
                # Batch processing with progress tracking
                results = await self.analyze_batch_with_progress(
                    model=model,
                    video_files=video_files,
                    mode=mode,
                    word_count=word_count,
                    prompt=prompt,
                    concurrency=concurrency,
                    verbose=verbose
                )
        else:
            if not path:
                raise ValueError("Either path or file_list must be provided")
            
            if path.is_file():
                # Single file analysis
                result = await self.analyze_single_video(
                    model=model,
                    video_path=path,
                    mode=mode,
                    word_count=word_count,
                    prompt=prompt,
                    verbose=verbose
                )
                results = [result]
                
            elif path.is_dir():
                # Directory analysis
                video_files = list(find_videos(path, recursive=recursive))
                
                if not video_files:
                    raise ValueError(f"No video files found in {path}")
                
                logger.info(f"Found {len(video_files)} video files in {path}")
                
                if len(video_files) == 1:
                    # Single video processing
                    results = [
                        await self.analyze_single_video(
                            model, video_files[0], mode, word_count, prompt, verbose
                        )
                    ]
                else:
                    # Batch processing with progress tracking
                    results = await self.analyze_batch_with_progress(
                        model=model,
                        video_files=video_files,
                        mode=mode,
                        word_count=word_count,
                        prompt=prompt,
                        concurrency=concurrency,
                        verbose=verbose
                    )
            else:
                raise ValueError(f"Path does not exist: {path}")
        
        # Format output
        formatted_output = self._format_output(results, output_format, verbose)
        
        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(formatted_output)
                
            logger.info(f"Results saved to: {output_path}")
        
        return formatted_output

    def _format_output(
        self, results: list[dict[str, Any]], output_format: str, verbose: bool = False
    ) -> str:
        """Format results according to the specified output format."""
        return self.output_formatter.format_video_results(
            results=results,
            format_type=output_format,
            verbose=verbose
        )