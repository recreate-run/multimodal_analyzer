"""Audio analysis functionality for the media analyzer."""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from loguru import logger
from tqdm.asyncio import tqdm

from .config import Config
from .models.litellm_model import LiteLLMModel
from .utils.audio import (
    get_media_files, 
    prepare_audio_for_transcription, 
    cleanup_temp_audio,
    get_audio_info,
    validate_audio_file
)
from .utils.output import OutputFormatter
from .utils.prompts import get_default_audio_prompt


class AudioAnalyzer:
    """Audio analysis using LiteLLM models."""

    def __init__(self, config: Config):
        self.config = config
        self.model = LiteLLMModel(config)
        self.output_formatter = OutputFormatter()

    async def analyze_single_audio(
        self,
        model: str,
        audio_path: Path,
        mode: str,
        word_count: int = 100,
        prompt: Optional[str] = None,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """Analyze a single audio file."""
        
        logger.info(f"Starting audio analysis: {audio_path}")
        
        # Validate mode early to avoid unnecessary processing
        if mode not in ["transcript", "description"]:
            return {
                "audio_path": str(audio_path),
                "model": model,
                "mode": mode,
                "success": False,
                "error": f"Invalid mode: {mode}. Use 'transcript' or 'description'"
            }
        
        # Prepare audio for transcription (extract from video if needed)
        prepared_audio_path, is_temp = prepare_audio_for_transcription(audio_path)
        
        try:
            # Validate the prepared audio file
            if not validate_audio_file(prepared_audio_path):
                return {
                    "audio_path": str(audio_path),
                    "model": model,
                    "mode": mode,
                    "success": False,
                    "error": "Audio file validation failed"
                }
            
            # Get audio information
            audio_info = get_audio_info(prepared_audio_path)
            
            # Step 1: Always transcribe the audio first
            logger.info(f"Transcribing audio with model: {model}")
            transcription_result = await self.model.transcribe_audio(
                model="whisper-1",  # Use Whisper for transcription
                audio_path=prepared_audio_path
            )
            
            if not transcription_result["success"]:
                return {
                    "audio_path": str(audio_path),
                    "model": model,
                    "mode": mode,
                    "success": False,
                    "error": f"Transcription failed: {transcription_result['error']}"
                }
            
            transcript = transcription_result["transcript"]
            
            # Step 2: Handle different modes
            if mode == "transcript":
                # For transcript mode, return the raw transcript
                result = {
                    "audio_path": str(audio_path),
                    "model": "whisper-1",
                    "mode": mode,
                    "transcript": transcript,
                    "audio_info": audio_info,
                    "success": True,
                    "error": None
                }
                
            elif mode == "description":
                # For description mode, analyze the transcript with the specified model
                logger.info(f"Analyzing transcript with model: {model}")
                
                # Use custom prompt or default
                analysis_prompt = prompt or get_default_audio_prompt()
                
                analysis_result = await self.model.analyze_transcript(
                    model=model,
                    transcript=transcript,
                    prompt=analysis_prompt,
                    word_count=word_count
                )
                
                if not analysis_result["success"]:
                    return {
                        "audio_path": str(audio_path),
                        "model": model,
                        "mode": mode,
                        "transcript": transcript,
                        "success": False,
                        "error": f"Analysis failed: {analysis_result['error']}"
                    }
                
                result = {
                    "audio_path": str(audio_path),
                    "transcription_model": "whisper-1",
                    "analysis_model": model,
                    "mode": mode,
                    "transcript": transcript,
                    "analysis": analysis_result["analysis"],
                    "prompt": analysis_prompt,
                    "word_count": word_count,
                    "audio_info": audio_info,
                    "success": True,
                    "error": None
                }
            
            else:
                return {
                    "audio_path": str(audio_path),
                    "model": model,
                    "mode": mode,
                    "success": False,
                    "error": f"Invalid mode: {mode}. Use 'transcript' or 'description'"
                }
            
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
            
        except Exception as e:
            logger.error(f"Unexpected error analyzing {audio_path}: {e}")
            return {
                "audio_path": str(audio_path),
                "model": model,
                "mode": mode,
                "success": False,
                "error": str(e)
            }
        
        finally:
            # Clean up temporary audio file if created
            if is_temp:
                cleanup_temp_audio(prepared_audio_path)

    async def analyze_batch(
        self,
        model: str,
        audio_files: List[Path],
        mode: str,
        word_count: int = 100,
        prompt: Optional[str] = None,
        concurrency: int = 3,
        verbose: bool = False
    ) -> List[Dict[str, Any]]:
        """Analyze multiple audio files with concurrency control."""
        
        logger.info(f"Starting batch analysis of {len(audio_files)} audio files")
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(min(concurrency, self.config.max_concurrency))
        
        async def analyze_with_semaphore(audio_path: Path) -> Dict[str, Any]:
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
        
        logger.info(f"Batch analysis completed. Success: {sum(1 for r in results if r['success'])}/{len(results)}")
        return results

    async def analyze(
        self,
        model: str,
        path: Path,
        mode: str,
        word_count: int = 100,
        prompt: Optional[str] = None,
        output_format: str = "json",
        output_file: Optional[str] = None,
        recursive: bool = False,
        concurrency: int = 3,
        verbose: bool = False
    ) -> str:
        """Main analysis method that handles both single files and directories."""
        
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
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_output)
                
            logger.info(f"Results saved to: {output_path}")
        
        return formatted_output