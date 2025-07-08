from collections.abc import Generator
from pathlib import Path

from loguru import logger
from PIL import Image


def find_images(
    path: Path, 
    recursive: bool = False, 
    supported_formats: list[str] = None
) -> Generator[Path, None, None]:
    """Find all image files in the given path."""
    
    if supported_formats is None:
        supported_formats = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]
    
    if path.is_file():
        if path.suffix.lower() in supported_formats:
            yield path
        else:
            logger.warning(f"File {path} is not a supported image format")
        return
    
    if path.is_dir():
        pattern = "**/*" if recursive else "*"
        for file_path in path.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in supported_formats:
                yield file_path

def validate_image_file(image_path: Path, max_size_mb: int = 10) -> bool:
    """Validate an image file."""
    try:
        # Check if file exists
        if not image_path.exists():
            logger.error(f"Image file does not exist: {image_path}")
            return False
        
        # Check file size
        file_size_mb = image_path.stat().st_size / (1024 * 1024)
        if file_size_mb > max_size_mb:
            logger.error(f"Image {image_path} exceeds max size ({file_size_mb:.1f}MB > {max_size_mb}MB)")
            return False
        
        # Try to open and verify with PIL
        with Image.open(image_path) as img:
            img.verify()
        
        logger.debug(f"Image validation passed: {image_path}")
        return True
        
    except Exception as e:
        logger.error(f"Image validation failed for {image_path}: {e}")
        return False

def get_image_info(image_path: Path) -> dict:
    """Get basic information about an image."""
    try:
        with Image.open(image_path) as img:
            return {
                "path": str(image_path),
                "format": img.format,
                "mode": img.mode,
                "size": img.size,
                "width": img.width,
                "height": img.height,
                "file_size_mb": round(image_path.stat().st_size / (1024 * 1024), 2)
            }
    except Exception as e:
        logger.error(f"Failed to get image info for {image_path}: {e}")
        return {
            "path": str(image_path),
            "error": str(e)
        }