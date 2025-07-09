"""Video utilities for media analyzer."""

from collections.abc import Generator
from pathlib import Path
from typing import Any

import ffmpeg
from loguru import logger

SUPPORTED_VIDEO_FORMATS = {
    ".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm", ".m4v"
}


def find_videos(
    path: Path, 
    recursive: bool = False, 
    supported_formats: set[str] | None = None
) -> Generator[Path, None, None]:
    """Find all video files in the given path."""
    
    if supported_formats is None:
        supported_formats = SUPPORTED_VIDEO_FORMATS
    
    if path.is_file():
        if path.suffix.lower() in supported_formats:
            yield path
        else:
            logger.warning(f"File {path} is not a supported video format")
        return
    
    if path.is_dir():
        pattern = "**/*" if recursive else "*"
        for file_path in path.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in supported_formats:
                yield file_path


def validate_video_file(video_path: Path) -> bool:
    """Validate a video file using ffmpeg probe."""
    if not video_path.exists():
        raise FileNotFoundError(f"Video file does not exist: {video_path}")
    
    if video_path.suffix.lower() not in SUPPORTED_VIDEO_FORMATS:
        raise ValueError(f"Unsupported video format: {video_path.suffix}")
    
    try:
        probe = ffmpeg.probe(str(video_path))
        
        # Check if file has video streams
        video_streams = [stream for stream in probe.get("streams", []) 
                        if stream.get("codec_type") == "video"]
        
        if not video_streams:
            raise ValueError(f"No video streams found in {video_path}")
        
        logger.debug(f"Video validation passed: {video_path}")
        return True
        
    except ffmpeg.Error as e:
        raise ValueError(f"Video validation failed for {video_path}: {e}")


def get_video_info(video_path: Path) -> dict[str, Any]:
    """Get video metadata using ffmpeg probe."""
    if not video_path.exists():
        raise FileNotFoundError(f"Video file does not exist: {video_path}")
    
    try:
        probe = ffmpeg.probe(str(video_path))
        
        # Get video stream info
        video_streams = [stream for stream in probe.get("streams", []) 
                        if stream.get("codec_type") == "video"]
        audio_streams = [stream for stream in probe.get("streams", []) 
                        if stream.get("codec_type") == "audio"]
        
        if not video_streams:
            raise ValueError(f"No video streams found in {video_path}")
        
        video_stream = video_streams[0]
        format_info = probe.get("format", {})
        
        # Calculate duration
        duration_seconds = float(format_info.get("duration", 0))
        duration_minutes = duration_seconds / 60.0
        
        # Get file size
        file_size_mb = video_path.stat().st_size / (1024 * 1024)
        
        return {
            "path": str(video_path),
            "format": format_info.get("format_name", "unknown"),
            "duration_seconds": duration_seconds,
            "duration_minutes": duration_minutes,
            "file_size_mb": round(file_size_mb, 2),
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "fps": eval(video_stream.get("r_frame_rate", "0/1")),
            "video_codec": video_stream.get("codec_name", "unknown"),
            "audio_codec": audio_streams[0].get("codec_name", "none") if audio_streams else "none",
            "bitrate": int(format_info.get("bit_rate", 0)),
            "has_audio": len(audio_streams) > 0,
            "video_streams": len(video_streams),
            "audio_streams": len(audio_streams)
        }
        
    except ffmpeg.Error as e:
        raise ValueError(f"Failed to get video info for {video_path}: {e}")


def is_video_file(file_path: Path) -> bool:
    """Check if a file is a supported video format."""
    return file_path.suffix.lower() in SUPPORTED_VIDEO_FORMATS