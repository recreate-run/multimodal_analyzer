"""File discovery utilities for hybrid input support."""

import unicodedata
from pathlib import Path

from .audio import AUDIO_EXTENSIONS, VIDEO_EXTENSIONS, is_audio_file, is_video_file
from .video import SUPPORTED_VIDEO_FORMATS

# Image format extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}

# Media type mappings
MEDIA_TYPE_EXTENSIONS = {
    "image": IMAGE_EXTENSIONS,
    "audio": AUDIO_EXTENSIONS | VIDEO_EXTENSIONS,  # Audio analysis supports video files
    "video": SUPPORTED_VIDEO_FORMATS,
}


def validate_file_list(files: list[str], media_type: str) -> list[Path]:
    """
    Validate and process explicit file lists with fail-fast error handling.
    
    Args:
        files: List of file path strings
        media_type: Type of media ("image", "audio", "video")
        
    Returns:
        List of validated Path objects
        
    Raises:
        FileNotFoundError: If any file doesn't exist
        ValueError: If any file has unsupported format or no valid files provided
    """
    if not files:
        raise ValueError("No files provided")
    
    if media_type not in MEDIA_TYPE_EXTENSIONS:
        raise ValueError(f"Unsupported media type: {media_type}")
    
    supported_extensions = MEDIA_TYPE_EXTENSIONS[media_type]
    validated_files = []
    
    for file_path_str in files:
        file_path_str = unicodedata.normalize('NFC', file_path_str)
        file_path = Path(file_path_str)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        if file_path.suffix.lower() not in supported_extensions:
            raise ValueError(f"Unsupported format for {media_type}: {file_path}")
        
        validated_files.append(file_path)
    
    if not validated_files:
        raise ValueError("No valid files provided")
    
    return sorted(validated_files)


def get_files_by_type(files: list[Path], media_type: str) -> list[Path]:
    """
    Filter files by media type.
    
    Args:
        files: List of Path objects
        media_type: Type of media ("image", "audio", "video")
        
    Returns:
        List of filtered Path objects sorted by name
    """
    if media_type not in MEDIA_TYPE_EXTENSIONS:
        raise ValueError(f"Unsupported media type: {media_type}")
    
    supported_extensions = MEDIA_TYPE_EXTENSIONS[media_type]
    filtered_files = []
    
    for file_path in files:
        if file_path.suffix.lower() in supported_extensions:
            filtered_files.append(file_path)
    
    return sorted(filtered_files)


def ensure_files_exist(files: list[Path]) -> None:
    """
    Check all files exist and are readable.
    
    Args:
        files: List of Path objects to check
        
    Raises:
        FileNotFoundError: If any file doesn't exist
        ValueError: If any path is not a file
    """
    for file_path in files:
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")


def is_supported_format(file_path: Path, media_type: str) -> bool:
    """
    Check if a file is a supported format for the given media type.
    
    Args:
        file_path: Path to the file
        media_type: Type of media ("image", "audio", "video")
        
    Returns:
        True if file format is supported for the media type
    """
    if media_type == "image":
        return file_path.suffix.lower() in IMAGE_EXTENSIONS
    elif media_type == "audio":
        return is_audio_file(file_path) or is_video_file(file_path)
    elif media_type == "video":
        return file_path.suffix.lower() in SUPPORTED_VIDEO_FORMATS
    else:
        return False