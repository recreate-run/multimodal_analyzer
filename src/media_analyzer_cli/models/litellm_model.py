import base64
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import litellm
from PIL import Image
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..config import Config

class LiteLLMModel:
    """Unified interface for multiple LLM providers using LiteLLM."""
    
    def __init__(self, config: Config):
        self.config = config
        
    def _encode_image(self, image_path: Path) -> str:
        """Encode image to base64 string."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _validate_image(self, image_path: Path) -> bool:
        """Validate image file."""
        try:
            # Check file size
            file_size_mb = image_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.config.max_file_size_mb:
                logger.warning(f"Image {image_path} exceeds max size ({file_size_mb:.1f}MB)")
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
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def _call_litellm_with_retry(self, model: str, messages: list, timeout: int) -> Any:
        """Call LiteLLM with retry logic."""
        return await asyncio.to_thread(
            litellm.completion,
            model=model,
            messages=messages,
            timeout=timeout
        )
    
    async def analyze_image(
        self, 
        model: str, 
        image_path: Path, 
        prompt: str,
        word_count: int = 100
    ) -> Dict[str, Any]:
        """Analyze a single image using the specified model."""
        
        if not self._validate_image(image_path):
            raise ValueError(f"Invalid image: {image_path}")
        
        # Get API key for the model
        api_key = self.config.get_api_key(model)
        if api_key:
            # Set API key for litellm
            if model.startswith('gpt-') or model.startswith('openai/'):
                litellm.openai_key = api_key
            elif model.startswith('claude-') or model.startswith('anthropic/'):
                litellm.anthropic_key = api_key
            elif model.startswith('gemini') or model.startswith('google/'):
                litellm.google_key = api_key
        
        # Encode image
        image_base64 = self._encode_image(image_path)
        
        # Prepare the full prompt
        full_prompt = f"{prompt} Please provide approximately {word_count} words in your description."
        
        # Prepare messages for vision models
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": full_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
        
        try:
            # Call LiteLLM with retry logic
            response = await self._call_litellm_with_retry(
                model=model,
                messages=messages,
                timeout=self.config.timeout_seconds
            )
            
            analysis = response.choices[0].message.content
            
            return {
                "image_path": str(image_path),
                "model": model,
                "prompt": prompt,
                "word_count": word_count,
                "analysis": analysis,
                "success": True,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Analysis failed for {image_path} with model {model}: {e}")
            return {
                "image_path": str(image_path),
                "model": model,
                "prompt": prompt,
                "word_count": word_count,
                "analysis": None,
                "success": False,
                "error": str(e)
            }
    
    def _validate_audio(self, audio_path: Path) -> bool:
        """Validate audio file for transcription."""
        try:
            # Check file exists
            if not audio_path.exists():
                logger.error(f"Audio file does not exist: {audio_path}")
                return False
            
            # Check file size
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            max_audio_size_mb = getattr(self.config, 'max_audio_size_mb', 100)  # 100MB default
            if file_size_mb > max_audio_size_mb:
                logger.warning(f"Audio {audio_path} exceeds max size ({file_size_mb:.1f}MB)")
                return False
            
            # Check format - supported by Whisper
            supported_audio_formats = {'.mp3', '.wav', '.m4a', '.flac', '.ogg'}
            if audio_path.suffix.lower() not in supported_audio_formats:
                logger.warning(f"Unsupported audio format: {audio_path.suffix}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Audio validation failed for {audio_path}: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def _call_litellm_transcription_with_retry(self, model: str, audio_file, timeout: int) -> Any:
        """Call LiteLLM transcription with retry logic."""
        return await asyncio.to_thread(
            litellm.transcription,
            model=model,
            file=audio_file,
            timeout=timeout
        )
    
    async def transcribe_audio(
        self, 
        model: str, 
        audio_path: Path
    ) -> Dict[str, Any]:
        """Transcribe audio file using Whisper models."""
        
        if not self._validate_audio(audio_path):
            raise ValueError(f"Invalid audio file: {audio_path}")
        
        # Get API key for the model
        api_key = self.config.get_api_key(model)
        if api_key:
            # Set API key for litellm - prioritize Azure OpenAI, then OpenAI
            if hasattr(self.config, 'azure_openai_endpoint') and self.config.azure_openai_endpoint:
                litellm.azure_key = api_key
                litellm.azure_base = self.config.azure_openai_endpoint
            else:
                litellm.openai_key = api_key
        
        try:
            # Open audio file for transcription
            with open(audio_path, "rb") as audio_file:
                # Call LiteLLM transcription with retry logic
                response = await self._call_litellm_transcription_with_retry(
                    model=model,
                    audio_file=audio_file,
                    timeout=self.config.timeout_seconds
                )
            
            transcript = response.text if hasattr(response, 'text') else response['text']
            
            return {
                "audio_path": str(audio_path),
                "model": model,
                "transcript": transcript,
                "success": True,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Transcription failed for {audio_path} with model {model}: {e}")
            return {
                "audio_path": str(audio_path),
                "model": model,
                "transcript": None,
                "success": False,
                "error": str(e)
            }
    
    async def analyze_transcript(
        self, 
        model: str, 
        transcript: str, 
        prompt: Optional[str] = None,
        word_count: int = 100
    ) -> Dict[str, Any]:
        """Analyze transcript text using specified LLM model."""
        
        # Get API key for the model
        api_key = self.config.get_api_key(model)
        if api_key:
            # Set API key for litellm
            if model.startswith('gpt-') or model.startswith('openai/'):
                if hasattr(self.config, 'azure_openai_endpoint') and self.config.azure_openai_endpoint:
                    litellm.azure_key = api_key
                    litellm.azure_base = self.config.azure_openai_endpoint
                else:
                    litellm.openai_key = api_key
            elif model.startswith('claude-') or model.startswith('anthropic/'):
                litellm.anthropic_key = api_key
            elif model.startswith('gemini') or model.startswith('google/'):
                litellm.google_key = api_key
        
        # Prepare the analysis prompt
        if prompt:
            full_prompt = f"{prompt}\n\nTranscript to analyze:\n{transcript}\n\nPlease provide approximately {word_count} words in your analysis."
        else:
            full_prompt = f"Please analyze and describe the following audio transcript. Provide approximately {word_count} words in your analysis.\n\nTranscript:\n{transcript}"
        
        # Prepare messages for the model
        messages = [
            {
                "role": "user",
                "content": full_prompt
            }
        ]
        
        try:
            # Call LiteLLM with retry logic
            response = await self._call_litellm_with_retry(
                model=model,
                messages=messages,
                timeout=self.config.timeout_seconds
            )
            
            analysis = response.choices[0].message.content
            
            return {
                "transcript": transcript,
                "model": model,
                "prompt": prompt,
                "word_count": word_count,
                "analysis": analysis,
                "success": True,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Transcript analysis failed with model {model}: {e}")
            return {
                "transcript": transcript,
                "model": model,
                "prompt": prompt,
                "word_count": word_count,
                "analysis": None,
                "success": False,
                "error": str(e)
            }