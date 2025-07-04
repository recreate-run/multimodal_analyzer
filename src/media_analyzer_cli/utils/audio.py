"""Audio processing utilities for the media analyzer."""

import os
import tempfile
from pathlib import Path

import ffmpeg
from loguru import logger
from pydub import AudioSegment

# Supported audio formats
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".wma"}

# Supported video formats (for audio extraction)
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm", ".m4v"}


def is_audio_file(file_path: Path) -> bool:
    """Check if file is a supported audio format."""
    return file_path.suffix.lower() in AUDIO_EXTENSIONS


def is_video_file(file_path: Path) -> bool:
    """Check if file is a supported video format."""
    return file_path.suffix.lower() in VIDEO_EXTENSIONS


def is_media_file(file_path: Path) -> bool:
    """Check if file is a supported media format (audio or video)."""
    return is_audio_file(file_path) or is_video_file(file_path)


def get_media_files(directory: Path, recursive: bool = False) -> list[Path]:
    """Get all media files from a directory."""
    media_files = []
    
    if recursive:
        pattern = "**/*"
    else:
        pattern = "*"
    
    for file_path in directory.glob(pattern):
        if file_path.is_file() and is_media_file(file_path):
            media_files.append(file_path)
    
    return sorted(media_files)


def extract_audio_from_video(video_path: Path, output_format: str = "wav") -> Path:
    """
    Extract audio from video file and save to temporary file.
    
    Args:
        video_path: Path to video file
        output_format: Output audio format (wav, mp3, etc.)
        
    Returns:
        Path to temporary audio file
        
    Raises:
        RuntimeError: If ffmpeg extraction fails
    """
    logger.info(f"Extracting audio from video: {video_path}")
    
    # Create temporary file for audio
    temp_dir = tempfile.gettempdir()
    temp_audio_path = Path(temp_dir) / f"extracted_audio_{os.getpid()}.{output_format}"
    
    try:
        # Use ffmpeg to extract audio
        stream = ffmpeg.input(str(video_path))
        stream = ffmpeg.output(stream, str(temp_audio_path), acodec="pcm_s16le" if output_format == "wav" else None)
        ffmpeg.run(stream, overwrite_output=True, quiet=True)
        
        if not temp_audio_path.exists():
            raise RuntimeError(f"Failed to extract audio from {video_path}")
            
        logger.info(f"Audio extracted to: {temp_audio_path}")
        return temp_audio_path
    
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg error extracting audio from {video_path}: {e}")
        if temp_audio_path.exists():
            temp_audio_path.unlink()
        raise RuntimeError(f"Failed to extract audio from {video_path}: {e}")


def get_audio_info(audio_path: Path) -> dict:
    """
    Get information about audio file.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Dictionary with audio information
    """
    try:
        audio = AudioSegment.from_file(str(audio_path))
        
        return {
            "duration_seconds": len(audio) / 1000.0,
            "duration_minutes": len(audio) / 60000.0,
            "sample_rate": audio.frame_rate,
            "channels": audio.channels,
            "file_size_bytes": audio_path.stat().st_size,
            "format": audio_path.suffix.lower().lstrip(".")
        }
    except Exception as e:
        logger.error(f"Error getting audio info for {audio_path}: {e}")
        return {
            "duration_seconds": 0,
            "duration_minutes": 0,
            "sample_rate": 0,
            "channels": 0,
            "file_size_bytes": audio_path.stat().st_size,
            "format": audio_path.suffix.lower().lstrip("."),
            "error": str(e)
        }


def prepare_audio_for_transcription(file_path: Path) -> tuple[Path, bool]:
    """
    Prepare audio file for transcription.
    
    Args:
        file_path: Path to media file (audio or video)
        
    Returns:
        Tuple of (audio_file_path, is_temporary)
        - audio_file_path: Path to audio file ready for transcription
        - is_temporary: True if audio file should be deleted after use
        
    Raises:
        ValueError: If file format is not supported
        RuntimeError: If audio extraction fails
    """
    if is_audio_file(file_path):
        logger.info(f"Using audio file directly: {file_path}")
        return file_path, False
    
    elif is_video_file(file_path):
        logger.info(f"Extracting audio from video file: {file_path}")
        audio_path = extract_audio_from_video(file_path, "wav")
        return audio_path, True
    
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")


def cleanup_temp_audio(audio_path: Path) -> None:
    """Clean up temporary audio file."""
    try:
        if audio_path.exists():
            audio_path.unlink()
            logger.info(f"Cleaned up temporary audio file: {audio_path}")
    except Exception as e:
        logger.warning(f"Failed to clean up temporary audio file {audio_path}: {e}")


def validate_audio_file(file_path: Path) -> bool:
    """
    Validate that audio file can be processed.
    
    Args:
        file_path: Path to audio file
        
    Returns:
        True if file is valid and can be processed
    """
    try:
        if not file_path.exists():
            logger.error(f"Audio file does not exist: {file_path}")
            return False
        
        if file_path.stat().st_size == 0:
            logger.error(f"Audio file is empty: {file_path}")
            return False
        
        # Try to load with pydub to validate format
        audio = AudioSegment.from_file(str(file_path))
        
        if len(audio) == 0:
            logger.error(f"Audio file has no content: {file_path}")
            return False
        
        logger.info(f"Audio file validated: {file_path} ({len(audio)/1000:.1f}s)")
        return True
        
    except Exception as e:
        logger.error(f"Audio file validation failed for {file_path}: {e}")
        return False