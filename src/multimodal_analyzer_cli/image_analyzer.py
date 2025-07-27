import asyncio
import base64
from pathlib import Path
from typing import Any

from loguru import logger
from tqdm.asyncio import tqdm

from .config import Config
from .models.litellm_model import LiteLLMModel
from .utils.file_discovery import validate_file_list
from .utils.image import find_images
from .utils.output import OutputFormatter
from .utils.prompts import PromptManager
from .utils.streaming import (
    MessageExtractor,
    StreamingInputReader,
    StreamingOutputWriter,
)


class ImageAnalyzer:
    """Core image analysis functionality."""

    def __init__(self, config: Config, custom_system_prompt: str | None = None):
        self.config = config
        self.model = LiteLLMModel(config, custom_system_prompt)

    async def analyze(
        self,
        model: str,
        path: Path | None = None,
        file_list: list[Path] | None = None,
        word_count: int = 100,
        prompt: str | None = None,
        output_format: str = "json",
        output_file: str | None = None,
        recursive: bool = False,
        concurrency: int = 10,
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
        if file_list:
            image_paths = validate_file_list([str(f) for f in file_list], "image")
        else:
            if not path:
                raise ValueError("Either path or file_list must be provided")
            image_paths = list(
                find_images(path, recursive, self.config.supported_image_formats)
            )

        if not image_paths:
            source_desc = "file list" if file_list else f"path {path}"
            raise ValueError(f"No supported image files found in {source_desc}")

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

    async def analyze_streaming(
        self,
        model: str,
        word_count: int = 100,
        prompt: str | None = None,
        verbose: bool = False,
    ) -> None:
        """Analyze images in streaming mode, reading JSONL from stdin and responding immediately."""
        
        # Validate configuration
        self.config.validate()
        
        # Initialize conversation context
        conversation_history = []
        
        # Add system prompt to conversation
        from .models.litellm_model import SystemPromptLoader
        system_prompt = SystemPromptLoader.load_system_prompt("image", self.model.custom_system_prompt)
        conversation_history.append({"role": "system", "content": system_prompt})
        
        logger.info(f"Starting streaming image analysis with model {model}")
        
        try:
            # Read messages from stdin
            async for message in StreamingInputReader.read_messages():
                try:
                    # Extract text prompt from message
                    text_prompt = MessageExtractor.extract_text_prompt(message)
                    
                    # Use custom prompt if provided, otherwise use extracted text
                    analysis_prompt = prompt or text_prompt
                    analysis_prompt = PromptManager.add_word_count_instruction(
                        analysis_prompt, word_count
                    )
                    
                    # Check if message contains media content
                    media_content = MessageExtractor.extract_media_content(message)
                    
                    if not media_content:
                        # No media content - respond with error
                        StreamingOutputWriter.write_error(
                            "No image content found in message. Please include an image for analysis.",
                            model=model
                        )
                        continue
                    
                    # Process image content
                    for media_item in media_content:
                        if media_item["type"] == "image_url":
                            image_url = media_item["image_url"]["url"]
                            
                            # Handle base64 images
                            if image_url.startswith("data:image/"):
                                # Extract base64 data
                                try:
                                    result = await self._analyze_image_from_base64(
                                        model, image_url, analysis_prompt, word_count
                                    )
                                    
                                    # Send successful response
                                    StreamingOutputWriter.write_response(
                                        content=result["analysis"],
                                        success=True,
                                        model=model
                                    )
                                    
                                    # Add to conversation history
                                    conversation_history.append(message["message"])
                                    conversation_history.append({
                                        "role": "assistant",
                                        "content": result["analysis"]
                                    })
                                    
                                except Exception as e:
                                    logger.error(f"Error analyzing image: {e}")
                                    StreamingOutputWriter.write_error(
                                        f"Error analyzing image: {str(e)}",
                                        model=model
                                    )
                            else:
                                StreamingOutputWriter.write_error(
                                    "Only base64 encoded images are supported in streaming mode",
                                    model=model
                                )
                        else:
                            StreamingOutputWriter.write_error(
                                f"Unsupported media type: {media_item['type']}",
                                model=model
                            )
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    StreamingOutputWriter.write_error(
                        f"Error processing message: {str(e)}",
                        model=model
                    )
                    
        except KeyboardInterrupt:
            logger.info("Streaming analysis interrupted by user")
        except Exception as e:
            logger.error(f"Streaming analysis failed: {e}")
            StreamingOutputWriter.write_error(
                f"Streaming analysis failed: {str(e)}",
                model=model
            )

    async def _analyze_image_from_base64(
        self, model: str, image_data_url: str, prompt: str, word_count: int
    ) -> dict[str, Any]:
        """Analyze an image from base64 data URL."""
        
        # Extract base64 data from data URL
        if not image_data_url.startswith("data:image/"):
            raise ValueError("Invalid image data URL format")
        
        # Parse data URL: data:image/jpeg;base64,<data>
        header, data = image_data_url.split(",", 1)
        image_base64 = data
        
        # Create a temporary file from base64 data
        import io
        import tempfile

        from PIL import Image
        
        # Decode base64 to bytes
        image_bytes = base64.b64decode(image_base64)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            
            # Validate it's a real image by opening with PIL
            image = Image.open(io.BytesIO(image_bytes))
            image.save(temp_file, format="JPEG")
        
        try:
            # Use the existing analyze_single_image method
            result = await self._analyze_single_image(model, temp_path, prompt, word_count)
            return result
        finally:
            # Clean up temporary file
            if temp_path.exists():
                temp_path.unlink()

    async def _analyze_single_image(
        self, model: str, image_path: Path, prompt: str, word_count: int
    ) -> dict[str, Any]:
        """Analyze a single image."""
        logger.info(f"Analyzing {image_path.name} with {model}")

        # Raise exceptions immediately instead of handling gracefully
        result = await self.model.analyze_image(
            model, image_path, prompt, word_count
        )
        logger.info(f"Analysis completed for {image_path.name}")
        return result

    async def _analyze_batch(
        self,
        model: str,
        image_paths: list[Path],
        prompt: str,
        word_count: int,
        concurrency: int,
    ) -> list[dict[str, Any]]:
        """Analyze multiple images with concurrency control."""
        logger.info(
            f"Starting batch analysis of {len(image_paths)} images with concurrency {concurrency}"
        )

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(min(concurrency, self.config.max_concurrency))

        async def analyze_with_semaphore(image_path: Path) -> dict[str, Any]:
            async with semaphore:
                return await self._analyze_single_image(
                    model, image_path, prompt, word_count
                )

        # Process all images concurrently - raise exceptions immediately
        tasks = [analyze_with_semaphore(image_path) for image_path in image_paths]
        results = await asyncio.gather(*tasks)

        logger.info(f"Batch analysis completed successfully for {len(results)} images")
        return results

    async def _analyze_batch_with_progress(
        self,
        model: str,
        image_paths: list[Path],
        prompt: str,
        word_count: int,
        concurrency: int,
    ) -> list[dict[str, Any]]:
        """Analyze multiple images with concurrency control and progress tracking."""
        logger.info(
            f"Starting batch analysis of {len(image_paths)} images with concurrency {concurrency}"
        )

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(min(concurrency, self.config.max_concurrency))

        async def analyze_with_semaphore_and_progress(
            image_path: Path, progress_bar
        ) -> dict[str, Any]:
            async with semaphore:
                try:
                    result = await self._analyze_single_image(
                        model, image_path, prompt, word_count
                    )
                    progress_bar.set_postfix(
                        status="✓" if result["success"] else "✗",
                    )
                    return result
                finally:
                    progress_bar.update(1)

        # Create progress bar
        progress_bar = tqdm(
            total=len(image_paths), desc="Analyzing images", unit="img", colour="green", disable=False
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
        self, results: list[dict[str, Any]], output_format: str, verbose: bool = False
    ) -> str:
        """Format results according to the specified output format."""
        if output_format == "json":
            return OutputFormatter.format_json(results, verbose=verbose)
        elif output_format == "markdown":
            return OutputFormatter.format_markdown(results, verbose=verbose)
        elif output_format == "text":
            return OutputFormatter.format_text(results, verbose=verbose)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
