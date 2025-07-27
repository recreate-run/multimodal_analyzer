import asyncio
import json
import sys
from collections.abc import AsyncGenerator
from typing import Any

from loguru import logger


class StreamingInputReader:
    """Reads and validates JSONL messages from stdin for streaming input."""
    
    @staticmethod
    async def read_messages() -> AsyncGenerator[dict[str, Any], None]:
        """Read JSONL messages from stdin line by line."""
        try:
            # Try async stdin reading first
            reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(reader)
            await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
            
            while True:
                # Read line from async stdin
                try:
                    line_bytes = await reader.readline()
                    if not line_bytes:  # EOF reached
                        break
                    
                    line = line_bytes.decode("utf-8").strip()
                    if not line:
                        continue
                        
                    try:
                        message = json.loads(line)
                        StreamingInputReader.validate_message(message)
                        yield message
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in input line: {line}")
                        raise ValueError(f"Invalid JSON: {e}")
                    except ValueError as e:
                        logger.error(f"Invalid message format: {e}")
                        raise
                        
                except asyncio.IncompleteReadError:
                    # EOF reached during read
                    break
                    
        except (OSError, ValueError) as e:
            # Async setup failed (e.g., in test environment), fall back to synchronous
            logger.debug(f"Async stdin setup failed, falling back to sync: {e}")
            
            try:
                for line in sys.stdin:
                    line = line.strip()
                    if not line:
                        continue
                        
                    try:
                        message = json.loads(line)
                        StreamingInputReader.validate_message(message)
                        yield message
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in input line: {line}")
                        raise ValueError(f"Invalid JSON: {e}")
                    except ValueError as e:
                        logger.error(f"Invalid message format: {e}")
                        raise
            except Exception:
                # Handle EOF gracefully - just return without raising
                pass
    
    @staticmethod
    def validate_message(message: dict[str, Any]) -> None:
        """Validate that message has required fields and format."""
        if not isinstance(message, dict):
            raise ValueError("Message must be a JSON object")
        
        if "type" not in message:
            raise ValueError("Message must have 'type' field")
        
        if message["type"] != "user":
            raise ValueError("Message type must be 'user'")
        
        if "message" not in message:
            raise ValueError("Message must have 'message' field")
        
        inner_message = message["message"]
        if not isinstance(inner_message, dict):
            raise ValueError("Message 'message' field must be an object")
        
        if "role" not in inner_message:
            raise ValueError("Message 'message' must have 'role' field")
        
        if inner_message["role"] != "user":
            raise ValueError("Message role must be 'user'")
        
        if "content" not in inner_message:
            raise ValueError("Message 'message' must have 'content' field")
        
        content = inner_message["content"]
        if not isinstance(content, list):
            raise ValueError("Message content must be an array")
        
        if not content:
            raise ValueError("Message content cannot be empty")
        
        # Validate content items
        for item in content:
            if not isinstance(item, dict):
                raise ValueError("Content items must be objects")
            if "type" not in item:
                raise ValueError("Content items must have 'type' field")
            
            if item["type"] == "text":
                if "text" not in item:
                    raise ValueError("Text content items must have 'text' field")
            elif item["type"] == "image_url":
                if "image_url" not in item:
                    raise ValueError("Image content items must have 'image_url' field")
                if not isinstance(item["image_url"], dict) or "url" not in item["image_url"]:
                    raise ValueError("Image content items must have 'image_url.url' field")


class StreamingOutputWriter:
    """Writes streaming JSON responses to stdout immediately."""
    
    @staticmethod
    def write_response(
        content: str, 
        success: bool = True, 
        model: str | None = None, 
        error: str | None = None
    ) -> None:
        """Write a streaming response message to stdout."""
        response = {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": content
            },
            "metadata": {
                "success": success
            }
        }
        
        if model:
            response["metadata"]["model"] = model
        
        if error:
            response["metadata"]["error"] = error
        
        # Write to stdout immediately
        json_output = json.dumps(response, ensure_ascii=False)
        print(json_output, flush=True)
    
    @staticmethod 
    def write_error(error: str, model: str | None = None) -> None:
        """Write an error response message to stdout."""
        StreamingOutputWriter.write_response(
            content="", 
            success=False, 
            model=model, 
            error=error
        )


class MessageExtractor:
    """Extracts media content and text from streaming messages."""
    
    @staticmethod
    def extract_text_prompt(message: dict[str, Any]) -> str:
        """Extract text prompt from message content."""
        content = message["message"]["content"]
        text_parts = []
        
        for item in content:
            if item["type"] == "text":
                text_parts.append(item["text"])
        
        return " ".join(text_parts).strip()
    
    @staticmethod
    def extract_media_content(message: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract media content (images, audio, video) from message."""
        content = message["message"]["content"]
        media_items = []
        
        for item in content:
            if item["type"] in ["image_url", "audio_url", "video_url"]:
                media_items.append(item)
        
        return media_items
    
    @staticmethod
    def has_media_content(message: dict[str, Any]) -> bool:
        """Check if message contains media content."""
        return len(MessageExtractor.extract_media_content(message)) > 0