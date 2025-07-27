import asyncio
import base64
from pathlib import Path
from typing import Any

import litellm
from litellm.caching.caching import Cache
from loguru import logger
from PIL import Image
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..config import Config


class SystemPromptLoader:
    """Manages loading and caching of system prompts for different media types."""
    
    _cache = {}
    
    @classmethod
    def load_system_prompt(cls, media_type: str, custom_prompt_path: str | None = None) -> str:
        """Load system prompt for the specified media type.
        
        Args:
            media_type: Type of media (image, audio, video)
            custom_prompt_path: Optional path to custom system prompt file
            
        Returns:
            System prompt content as string
        """
        if custom_prompt_path:
            return cls._load_from_file(custom_prompt_path)
        
        if media_type not in cls._cache:
            prompt_file = Path(__file__).parent.parent / "prompts" / f"{media_type}_system_prompt.md"
            cls._cache[media_type] = cls._load_from_file(prompt_file)
        
        return cls._cache[media_type]
    
    @classmethod
    def _load_from_file(cls, file_path: Path | str) -> str:
        """Load system prompt from file."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"System prompt file not found: {file_path}")
        
        with open(file_path, encoding="utf-8") as f:
            content = f.read().strip()
        
        if not content:
            raise ValueError(f"System prompt file is empty: {file_path}")
        
        return content

litellm.cache = Cache(type="disk", cache_dir="./.litellm_cache")
litellm.drop_params = True # drop unsupported OpenAI params automatically


class LiteLLMModel:
    """Unified interface for multiple LLM providers using LiteLLM."""

    # Image preprocessing threshold in KB - images larger than this will be converted to JPEG
    IMAGE_PREPROCESSING_THRESHOLD_KB = 500

    def __init__(self, config: Config, custom_system_prompt: str | None = None):
        self.config = config
        self.custom_system_prompt = custom_system_prompt

    def _encode_image(self, image_path: Path) -> str:
        """Encode image to base64 string."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def _preprocess_image(self, image_path: Path) -> Path:
        """Preprocess image if needed (convert to JPEG if > 500KB)."""
        # Check file size
        file_size = image_path.stat().st_size
        threshold_bytes = self.IMAGE_PREPROCESSING_THRESHOLD_KB * 1024

        if file_size > threshold_bytes:
            logger.debug(f"Image {image_path.name} is {file_size} bytes (> {self.IMAGE_PREPROCESSING_THRESHOLD_KB}KB), converting to JPEG")

            # Create a temporary path for the converted image
            temp_path = image_path.parent / f"{image_path.stem}_preprocessed.jpg"

            # Convert to JPEG
            with Image.open(image_path) as img:
                # Convert to RGB if needed (for transparency handling)
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")

                # Save as JPEG with high quality
                img.save(temp_path, "JPEG", quality=95)

            logger.debug(f"Converted {image_path.name} to JPEG format: {temp_path.name}")
            return temp_path
        else:
            logger.debug(f"Image {image_path.name} is {file_size} bytes (<= {self.IMAGE_PREPROCESSING_THRESHOLD_KB}KB), no preprocessing needed")
            return image_path

    def _encode_audio(self, audio_path: Path) -> str:
        """Encode audio to base64 string."""
        with open(audio_path, "rb") as audio_file:
            return base64.b64encode(audio_file.read()).decode("utf-8")

    def _encode_video(self, video_path: Path) -> str:
        """Encode video to base64 string."""
        with open(video_path, "rb") as video_file:
            return base64.b64encode(video_file.read()).decode("utf-8")

    def _validate_image(self, image_path: Path) -> bool:
        """Validate image file."""
        try:
            # Check file size
            file_size_mb = image_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.config.max_file_size_mb:
                logger.warning(
                    f"Image {image_path} exceeds max size ({file_size_mb:.1f}MB)"
                )
                return False

            # Check format
            if image_path.suffix.lower() not in self.config.supported_image_formats:
                logger.warning(f"Unsupported format: {image_path.suffix}")
                return False

            # Try to open with PIL
            with Image.open(image_path) as img:
                img.verify()

            return True
        except Exception as e:
            logger.error(f"Image validation failed for {image_path}: {e}")
            return False

    def _validate_audio(self, audio_path: Path) -> bool:
        """Validate audio file for Gemini processing."""
        try:
            # Check file exists
            if not audio_path.exists():
                logger.error(f"Audio file does not exist: {audio_path}")
                return False

            # Check file size
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            max_audio_size_mb = getattr(
                self.config, "max_audio_size_mb", 100
            )  # 100MB default
            if file_size_mb > max_audio_size_mb:
                logger.warning(
                    f"Audio {audio_path} exceeds max size ({file_size_mb:.1f}MB)"
                )
                return False

            # Check format - supported by Gemini
            supported_audio_formats = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac"}
            if audio_path.suffix.lower() not in supported_audio_formats:
                logger.warning(f"Unsupported audio format: {audio_path.suffix}")
                return False

            return True
        except Exception as e:
            logger.error(f"Audio validation failed for {audio_path}: {e}")
            return False

    def _validate_video(self, video_path: Path) -> bool:
        """Validate video file for Gemini processing."""
        try:
            # Check file exists
            if not video_path.exists():
                logger.error(f"Video file does not exist: {video_path}")
                return False

            # Check file size
            file_size_mb = video_path.stat().st_size / (1024 * 1024)
            max_video_size_mb = getattr(
                self.config, "max_video_size_mb", 2048
            )  # 2GB default for Gemini 2.0
            if file_size_mb > max_video_size_mb:
                logger.warning(
                    f"Video {video_path} exceeds max size ({file_size_mb:.1f}MB)"
                )
                return False

            # Check format - supported by Gemini
            supported_video_formats = {
                ".mp4",
                ".avi",
                ".mov",
                ".mkv",
                ".wmv",
                ".flv",
                ".webm",
                ".m4v",
            }
            if video_path.suffix.lower() not in supported_video_formats:
                logger.warning(f"Unsupported video format: {video_path.suffix}")
                return False

            return True
        except Exception as e:
            logger.error(f"Video validation failed for {video_path}: {e}")
            return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    async def _call_litellm_with_retry(
        self, model: str, messages: list, timeout: int
    ) -> Any:
        """Call LiteLLM with retry logic."""
        return await asyncio.to_thread(
            litellm.completion, model=model, messages=messages, timeout=timeout, temperature=0
        )

    async def analyze_image(
        self, model: str, image_path: Path, prompt: str, word_count: int = 100
    ) -> dict[str, Any]:
        """Analyze a single image using the specified model."""

        if not self._validate_image(image_path):
            raise ValueError(f"Invalid image: {image_path}")

        # Get API key or OAuth token for the model
        api_key = self.config.get_api_key(model)
        if api_key:
            # Set API key/token for litellm
            if model.startswith("gpt-") or model.startswith("openai/"):
                litellm.openai_key = api_key
            elif model.startswith("claude-") or model.startswith("anthropic/"):
                litellm.anthropic_key = api_key
            elif model.startswith("gemini") or model.startswith("google/"):
                litellm.google_key = api_key

        # Preprocess image if needed (convert to JPEG if > 1KB)
        processed_image_path = self._preprocess_image(image_path)

        try:
            # Encode image
            image_base64 = self._encode_image(processed_image_path)

            # Load system prompt
            system_prompt = SystemPromptLoader.load_system_prompt(
                "image", self.custom_system_prompt
            )

            # Prepare the full prompt
            full_prompt = f"{prompt} Please provide approximately {word_count} words in your description."

            # Prepare messages for vision models with system prompt
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": full_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                        },
                    ],
                }
            ]

            # Call LiteLLM with retry logic - raise exceptions immediately
            response = await self._call_litellm_with_retry(
                model=model, messages=messages, timeout=self.config.timeout_seconds
            )

            analysis = response.choices[0].message.content

            return {
                "image_path": str(image_path),
                "model": model,
                "prompt": prompt,
                "word_count": word_count,
                "analysis": analysis,
                "success": True,
                "error": None,
            }
        finally:
            # Clean up temporary file if it was created
            if processed_image_path != image_path and processed_image_path.exists():
                processed_image_path.unlink()
                logger.debug(f"Cleaned up temporary file: {processed_image_path.name}")

    async def analyze_audio_directly(
        self,
        model: str,
        audio_path: Path,
        mode: str,
        prompt: str | None = None,
        word_count: int = 100,
    ) -> dict[str, Any]:
        """Analyze audio directly using Gemini's multimodal capabilities."""

        # Only support Gemini models for audio analysis
        if not model.startswith("gemini"):
            raise ValueError(
                f"Audio analysis only supports Gemini models. Received: {model}"
            )

        if not self._validate_audio(audio_path):
            raise ValueError(f"Invalid audio file: {audio_path}")

        # Get API key or OAuth token for Gemini
        api_key = self.config.get_api_key(model)
        if api_key:
            litellm.google_key = api_key
            # Log authentication method for Google models
            if self.config.google_oauth_enabled:
                logger.debug("Using OAuth token for Google/Gemini authentication")
            else:
                logger.debug("Using API key for Google/Gemini authentication")

        # Encode audio to base64
        audio_base64 = self._encode_audio(audio_path)

        # Determine MIME type based on file extension
        mime_types = {
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".m4a": "audio/mp4",
            ".flac": "audio/flac",
            ".ogg": "audio/ogg",
            ".aac": "audio/aac",
        }
        mime_type = mime_types.get(audio_path.suffix.lower(), "audio/mpeg")

        # Load system prompt
        system_prompt = SystemPromptLoader.load_system_prompt(
            "audio", self.custom_system_prompt
        )

        # Prepare prompt based on mode
        if mode == "transcript":
            full_prompt = (
                "Please transcribe this audio file and return only the transcript text."
            )
        elif mode == "description":
            if prompt:
                full_prompt = f"{prompt}\n\nPlease analyze this audio content. Provide approximately {word_count} words in your analysis."
            else:
                full_prompt = f"Please analyze and describe the content of this audio file. Provide approximately {word_count} words in your analysis."
        else:
            raise ValueError(f"Invalid mode: {mode}. Use 'transcript' or 'description'")

        # Prepare messages for Gemini with audio content
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": full_prompt},
                    {
                        "type": "file",
                        "file": {
                            "file_data": f"data:{mime_type};base64,{audio_base64}"
                        },
                    },
                ],
            }
        ]

        # Call Gemini with audio content - raise exceptions immediately
        response = await self._call_litellm_with_retry(
            model=model, messages=messages, timeout=self.config.timeout_seconds
        )

        content = response.choices[0].message.content

        result = {
            "audio_path": str(audio_path),
            "model": model,
            "mode": mode,
            "success": True,
            "error": None,
        }

        if mode == "transcript":
            result["transcript"] = content
        elif mode == "description":
            result["transcript"] = (
                content  # Gemini provides both transcript and analysis
            )
            result["analysis"] = content
            result["prompt"] = prompt
            result["word_count"] = word_count

        return result

    async def analyze_video(
        self,
        model: str,
        video_path: Path,
        mode: str,
        prompt: str | None = None,
        word_count: int = 100,
    ) -> dict[str, Any]:
        """Analyze video directly using Gemini's multimodal capabilities."""

        # Only support Gemini models for video analysis
        if not model.startswith("gemini"):
            raise ValueError(
                f"Video analysis only supports Gemini models. Received: {model}"
            )

        if not self._validate_video(video_path):
            raise ValueError(f"Invalid video file: {video_path}")

        # Get API key or OAuth token for Gemini
        api_key = self.config.get_api_key(model)
        if api_key:
            litellm.google_key = api_key
            # Log authentication method for Google models
            if self.config.google_oauth_enabled:
                logger.debug("Using OAuth token for Google/Gemini authentication")
            else:
                logger.debug("Using API key for Google/Gemini authentication")

        # Encode video to base64
        video_base64 = self._encode_video(video_path)

        # Determine MIME type based on file extension
        mime_types = {
            ".mp4": "video/mp4",
            ".avi": "video/x-msvideo",
            ".mov": "video/quicktime",
            ".mkv": "video/x-matroska",
            ".wmv": "video/x-ms-wmv",
            ".flv": "video/x-flv",
            ".webm": "video/webm",
            ".m4v": "video/mp4",
        }
        mime_type = mime_types.get(video_path.suffix.lower(), "video/mp4")

        # Only support description mode for video analysis
        if mode != "description":
            raise ValueError(
                f"Invalid mode: {mode}. Video analysis only supports 'description' mode"
            )

        # Load system prompt
        system_prompt = SystemPromptLoader.load_system_prompt(
            "video", self.custom_system_prompt
        )

        # Prepare prompt for description mode
        if prompt:
            full_prompt = f"{prompt}\n\nPlease analyze this video content including both visual and audio elements. Provide approximately {word_count} words in your analysis."
        else:
            full_prompt = f"Please analyze and describe the content of this video file, including both visual and audio elements. Provide approximately {word_count} words in your analysis."

        # Prepare messages for Gemini with video content
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": full_prompt},
                    {
                        "type": "file",
                        "file": {
                            "file_data": f"data:{mime_type};base64,{video_base64}"
                        },
                    },
                ],
            }
        ]

        # Call Gemini with video content - raise exceptions immediately
        response = await self._call_litellm_with_retry(
            model=model, messages=messages, timeout=self.config.timeout_seconds
        )

        content = response.choices[0].message.content

        result = {
            "video_path": str(video_path),
            "model": model,
            "mode": mode,
            "analysis": content,
            "prompt": prompt,
            "word_count": word_count,
            "success": True,
            "error": None,
        }

        return result

    async def analyze_transcript(
        self,
        model: str,
        transcript: str,
        prompt: str | None = None,
        word_count: int = 100,
    ) -> dict[str, Any]:
        """Analyze transcript text using specified LLM model."""

        # Get API key or OAuth token for the model
        api_key = self.config.get_api_key(model)
        if api_key:
            # Set API key/token for litellm
            if model.startswith("azure/"):
                litellm.azure_key = api_key
                if (
                    hasattr(self.config, "azure_openai_endpoint")
                    and self.config.azure_openai_endpoint
                ):
                    litellm.azure_base = self.config.azure_openai_endpoint
            elif model.startswith("gpt-") or model.startswith("openai/"):
                litellm.openai_key = api_key
            elif model.startswith("claude-") or model.startswith("anthropic/"):
                litellm.anthropic_key = api_key
            elif model.startswith("gemini") or model.startswith("google/"):
                litellm.google_key = api_key

        # Load system prompt
        system_prompt = SystemPromptLoader.load_system_prompt(
            "audio", self.custom_system_prompt
        )

        # Prepare the analysis prompt
        if prompt:
            full_prompt = f"{prompt}\n\nTranscript to analyze:\n{transcript}\n\nPlease provide approximately {word_count} words in your analysis."
        else:
            full_prompt = f"Please analyze and describe the following audio transcript. Provide approximately {word_count} words in your analysis.\n\nTranscript:\n{transcript}"

        # Prepare messages for the model
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ]

        # Call LiteLLM with retry logic - raise exceptions immediately
        response = await self._call_litellm_with_retry(
            model=model, messages=messages, timeout=self.config.timeout_seconds
        )

        analysis = response.choices[0].message.content

        return {
            "transcript": transcript,
            "model": model,
            "prompt": prompt,
            "word_count": word_count,
            "analysis": analysis,
            "success": True,
            "error": None,
        }
