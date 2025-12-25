"""
Batch Import Script
Imports all images from a folder into the document intelligence system.
"""

import os
import sys
import time
import asyncio
from pathlib import Path

# Add the backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services import ocr_service, document_store
from app.core import logger

SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp', '.pdf'}


def import_images(folder_path: str, max_files: int = None):
    """
    Import all images from a folder.
    
    Args:
        folder_path: Path to folder containing images
        max_files: Maximum number of files to process (None for all)
    """
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"ERROR: Folder not found: {folder_path}")
        return
    
    # Get all supported files
    files = []
    for ext in SUPPORTED_EXTENSIONS:
        files.extend(folder.glob(f"*{ext}"))
        files.extend(folder.glob(f"*{ext.upper()}"))
    
    files = sorted(set(files))  # Remove duplicates and sort
    
    if max_files:
        files = files[:max_files]
    
    print(f"\n{'='*60}")
    print(f"BATCH IMPORT")
    print(f"{'='*60}")
    print(f"Folder: {folder_path}")
    print(f"Files found: {len(files)}")
    print(f"{'='*60}\n")
    
    if not files:
        print("No supported files found.")
        return
    
    successful = 0
    failed = 0
    start_time = time.time()
    
    for i, file_path in enumerate(files, 1):
        try:
            print(f"[{i}/{len(files)}] Processing: {file_path.name}...", end=" ", flush=True)
            
            file_start = time.time()
            
            # Read file
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
            
            # OCR
            text = ocr_service.extract_text_from_file(file_bytes, file_path.suffix.lower())
            
            if not text or len(text.strip()) < 10:
                print("SKIPPED (no text)")
                continue
            
            # Generate unique ID
            import uuid
            doc_id = str(uuid.uuid4())
            
            # Store document
            doc = document_store.add_document(
                doc_id=doc_id,
                filename=file_path.name,
                content=text,
                summary=text[:200] + "..." if len(text) > 200 else text,
                file_type=file_path.suffix.upper().replace('.', ''),
                metadata={
                    "source_path": str(file_path),
                    "import_batch": "batch_import"
                }
            )
            
            elapsed = time.time() - file_start
            print(f"OK ({elapsed:.1f}s, {len(text)} chars)")
            successful += 1
            
        except Exception as e:
            print(f"FAILED: {str(e)[:50]}")
            failed += 1
    
    total_time = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"IMPORT COMPLETE")
    print(f"{'='*60}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total time: {total_time:.1f}s")
    print(f"Avg per file: {total_time/len(files):.1f}s")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch import images")
    parser.add_argument("folder", help="Folder containing images")
    parser.add_argument("--max", type=int, help="Max files to process")
    
    args = parser.parse_args()
    
    import_images(args.folder, args.max)
