"""Pre-flight validation, format normalization, and upscaling module."""

import io
from pathlib import Path
from typing import Tuple, Dict, Any
import numpy as np
from PIL import Image, ImageOps
from src.config import MIN_PORTAL_DIMENSION, MAX_PORTAL_DIMENSION, MAX_WORKING_DIMENSION, MAX_FILE_SIZE_BYTES

def inspect_and_normalize_image(image_path: Path) -> Tuple[Image.Image, Dict[str, Any]]:
    """Loads image, inspects technical specs, corrects EXIF orientation, and normalizes format."""
    file_size_bytes = image_path.stat().st_size
    
    with open(image_path, "rb") as f:
        raw_bytes = f.read()

    # Open image
    img = Image.open(io.BytesIO(raw_bytes))
    original_format = img.format or "JPEG"

    # Fix EXIF orientation if present
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    original_width, original_height = img.size

    # Ensure RGB mode (handling RGBA, palette, grayscale)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    elif img.mode == "L":
        img = img.convert("RGB")

    # Deterministic Technical Checks on raw dimensions
    aspect_ratio = round(original_width / max(1, original_height), 3)
    is_under_min = (original_width < MIN_PORTAL_DIMENSION or original_height < MIN_PORTAL_DIMENSION)
    is_over_max_dim = (original_width > MAX_PORTAL_DIMENSION or original_height > MAX_PORTAL_DIMENSION)
    is_over_max_file = (file_size_bytes > MAX_FILE_SIZE_BYTES)
    is_extreme_aspect = (aspect_ratio < 0.25 or aspect_ratio > 4.0)

    # Cap working resolution at MAX_WORKING_DIMENSION (1600px) so multi-megapixel DSLR/mobile
    # uploads do not bottleneck Laplacian blur calculation, Cloud Vision API, or Gemini Nano Banana 2.1
    downsampled = False
    if max(img.size) > MAX_WORKING_DIMENSION:
        scale_down = MAX_WORKING_DIMENSION / float(max(img.size))
        new_w = max(1, int(round(img.width * scale_down)))
        new_h = max(1, int(round(img.height * scale_down)))
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        downsampled = True

    width, height = img.size

    # Deterministic blank/solid-color image detection (< 5.0 std dev)
    gray_arr = np.array(img.convert("L"), dtype=np.float32)
    pixel_std = float(np.std(gray_arr))
    is_blank = (pixel_std < 5.0)

    # Deterministic Laplacian variance (objective blur / sharpness indicator)
    try:
        from scipy.ndimage import laplace, variance
        blur_score = float(variance(laplace(gray_arr)))
    except Exception:
        blur_score = 1000.0

    specs = {
        "filename": image_path.name,
        "original_format": original_format,
        "raw_width": original_width,
        "raw_height": original_height,
        "normalized_width": width,
        "normalized_height": height,
        "aspect_ratio": aspect_ratio,
        "file_size_bytes": file_size_bytes,
        "file_size_kb": round(file_size_bytes / 1024, 1),
        "is_under_min_size": is_under_min,
        "is_over_max_dimension": is_over_max_dim,
        "is_over_max_size": is_over_max_file,
        "is_extreme_aspect": is_extreme_aspect,
        "is_blank_placeholder": is_blank,
        "pixel_std_dev": round(pixel_std, 2),
        "objective_blur_score": round(blur_score, 1),
        "upscaled": False,
        "downsampled": downsampled
    }

    # If below portal minimum dimension (200x200), upscale with high-quality Lanczos resampling
    # for preview rendering, but specs["is_under_min_size"] remains True for deterministic policy rejection
    if is_under_min:
        scale_factor = max(MIN_PORTAL_DIMENSION / width, MIN_PORTAL_DIMENSION / height)
        target_scale = max(scale_factor, 400 / min(width, height))
        new_w = int(width * target_scale)
        new_h = int(height * target_scale)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        specs["upscaled"] = True
        specs["upscaled_width"] = new_w
        specs["upscaled_height"] = new_h
        specs["normalized_width"] = new_w
        specs["normalized_height"] = new_h

    return img, specs

def image_to_bytes(img: Image.Image, format: str = "JPEG", quality: int = 92) -> bytes:
    """Converts a PIL Image to bytes."""
    buf = io.BytesIO()
    img.save(buf, format=format, quality=quality)
    return buf.getvalue()
