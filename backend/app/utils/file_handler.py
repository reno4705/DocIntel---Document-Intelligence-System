import os
import uuid
import aiofiles
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile

from app.core import settings, logger


class FileHandler:
    def __init__(self):
        self.temp_dir = Path(settings.TEMP_DIR)
        self.temp_dir.mkdir(exist_ok=True)
    
    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, str]:
        extension = Path(filename).suffix.lower()
        
        if extension not in settings.ALLOWED_EXTENSIONS:
            return False, f"File type not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
        
        if file_size > settings.MAX_FILE_SIZE:
            return False, f"File too large. Maximum size: {settings.MAX_FILE_SIZE // (1024*1024)}MB"
        
        return True, ""
    
    async def save_temp_file(self, file: UploadFile) -> Tuple[str, bytes]:
        file_id = str(uuid.uuid4())
        extension = Path(file.filename).suffix.lower()
        temp_path = self.temp_dir / f"{file_id}{extension}"
        
        content = await file.read()
        
        async with aiofiles.open(temp_path, "wb") as f:
            await f.write(content)
        
        logger.info(f"Saved temp file: {temp_path}")
        return str(temp_path), content
    
    def cleanup_temp_file(self, file_path: str) -> None:
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup temp file: {str(e)}")
    
    def get_file_extension(self, filename: str) -> str:
        return Path(filename).suffix.lower()


file_handler = FileHandler()
