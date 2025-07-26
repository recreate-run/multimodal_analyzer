"""Audio analysis functionality for the media analyzer."""

import asyncio
from pathlib import Path
from typing import Any

from loguru import logger
from tqdm.asyncio import tqdm

from .config import Config
from .models.litellm_model import LiteLLMModel
from .utils.audio import (
    cleanup_temp_audio,
    get_audio_info,
    get_media_files,
    prepare_audio_for_transcription,
    validate_audio_file,
)
from .utils.file_discovery import validate_file_list
from .utils.output import OutputFormatter
from .utils.prompts import get_default_audio_prompt


class AudioAnalyzer:
    """Audio analysis using LiteLLM models."""

    def __init__(self, config: Config, custom_system_prompt: str | None = None):
        self.config = config
        self.model = LiteLLMModel(config, custom_system_prompt)
        self.output_formatter = OutputFormatter()

    async def analyze_single_audio(
        self,
        model: str,
        audio_path: Path,
        mode: str,
        word_count: int = 100,
        prompt: str | None = None,
        verbose: bool = False
    ) -> dict[str, Any]:
        """Analyze a single audio file."""

        logger.info(f"Starting audio analysis: {audio_path}")

        # Validate mode early to avoid unnecessary processing
        if mode not in ["transcript", "description"]:
            raise ValueError(f"Invalid mode: {mode}. Use 'transcript' or 'description'")

        # Prepare audio for transcription (extract from video if needed)
        prepared_audio_path, is_temp = prepare_audio_for_transcription(audio_path)

        try:
            # Validate the prepared audio file
            if not validate_audio_file(prepared_audio_path):
                raise ValueError("Audio file validation failed")

            # Get audio information
            audio_info = get_audio_info(prepared_audio_path)

            # Only support Gemini models for audio analysis
            if not model.startswith("gemini"):
                raise ValueError(
                    f"Audio analysis only supports Gemini models. Received: {model}"
                )

            # Use Gemini's direct audio analysis
            logger.info(f"Analyzing audio directly with Gemini model: {model}")

            # Use custom prompt or default for description mode
            analysis_prompt = prompt if mode == "description" else None
            if mode == "description" and not analysis_prompt:
                analysis_prompt = get_default_audio_prompt()

            result = await self.model.analyze_audio_directly(
                model=model,
                audio_path=prepared_audio_path,
                mode=mode,
                prompt=analysis_prompt,
                word_count=word_count
            )

            if not result["success"]:
                raise RuntimeError(result["error"])

            # Override audio_path with original file path (user submitted path)
            result["audio_path"] = str(audio_path)

            # Add audio info to the result
            result["audio_info"] = audio_info

            # Add verbose information if requested
            if verbose:
                result["verbose"] = {
                    "original_file": str(audio_path),
                    "processed_file": str(prepared_audio_path),
                    "is_temporary": is_temp,
                    "audio_info": audio_info
                }

            logger.info(f"Audio analysis completed successfully: {audio_path}")
            return result

        finally:
            # Clean up temporary audio file if created
            if is_temp:
                cleanup_temp_audio(prepared_audio_path)

    async def analyze_batch(
        self,
        model: str,
        audio_files: list[Path],
        mode: str,
        word_count: int = 100,
        prompt: str | None = None,
        concurrency: int = 3,
        verbose: bool = False
    ) -> list[dict[str, Any]]:
        """Analyze multiple audio files with concurrency control."""

        logger.info(f"Starting batch analysis of {len(audio_files)} audio files")

        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(min(concurrency, self.config.max_concurrency))

        async def analyze_with_semaphore(audio_path: Path) -> dict[str, Any]:
            async with semaphore:
                return await self.analyze_single_audio(
                    model=model,
                    audio_path=audio_path,
                    mode=mode,
                    word_count=word_count,
                    prompt=prompt,
                    verbose=verbose
                )

        # Run all analyses with progress bar
        tasks = [analyze_with_semaphore(audio_path) for audio_path in audio_files]
        results = await tqdm.gather(*tasks, desc="Analyzing audio files")

        success_count = sum(1 for r in results if r["success"])
        logger.info(f"Batch analysis completed. Success: {success_count}/{len(results)}")
        return results

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
        concurrency: int = 10,
        verbose: bool = False
    ) -> str:
        """Main analysis method that handles files, directories, and explicit file lists."""

        if file_list:
            # File list analysis
            audio_files = validate_file_list([str(f) for f in file_list], "audio")

            if len(audio_files) == 1:
                # Single file analysis
                result = await self.analyze_single_audio(
                    model=model,
                    audio_path=audio_files[0],
                    mode=mode,
                    word_count=word_count,
                    prompt=prompt,
                    verbose=verbose
                )
                results = [result]
            else:
                # Batch analysis
                results = await self.analyze_batch(
                    model=model,
                    audio_files=audio_files,
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
                result = await self.analyze_single_audio(
                    model=model,
                    audio_path=path,
                    mode=mode,
                    word_count=word_count,
                    prompt=prompt,
                    verbose=verbose
                )
                results = [result]

            elif path.is_dir():
                # Directory analysis
                audio_files = get_media_files(path, recursive=recursive)

                if not audio_files:
                    raise ValueError(f"No audio/video files found in {path}")

                logger.info(f"Found {len(audio_files)} media files in {path}")

                results = await self.analyze_batch(
                    model=model,
                    audio_files=audio_files,
                    mode=mode,
                    word_count=word_count,
                    prompt=prompt,
                    concurrency=concurrency,
                    verbose=verbose
                )
            else:
                raise ValueError(f"Path does not exist: {path}")

        # Format output
        formatted_output = self.output_formatter.format_audio_results(
            results=results,
            format_type=output_format,
            verbose=verbose
        )

        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(formatted_output)

            logger.info(f"Results saved to: {output_path}")

        return formatted_output
