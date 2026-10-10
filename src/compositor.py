"""Mask-Protected Compositor module enforcing 100% real-food pixel integrity."""

import io
from typing import Tuple, List
from PIL import Image, ImageDraw, ImageFilter, ImageOps
import numpy as np

def extract_food_roi(original_img: Image.Image, box_2d: List[int]) -> Tuple[Image.Image, Tuple[int, int, int, int]]:
    """Extracts the food/dish bounding box in pixel coordinates."""
    w, h = original_img.size
    ymin, xmin, ymax, xmax = box_2d
    
    # Convert normalized (0-1000) coordinates to pixels
    left = int((xmin / 1000.0) * w)
    top = int((ymin / 1000.0) * h)
    right = int((xmax / 1000.0) * w)
    bottom = int((ymax / 1000.0) * h)

    # Constrain to image bounds
    left = max(0, min(w - 1, left))
    top = max(0, min(h - 1, top))
    right = max(left + 1, min(w, right))
    bottom = max(top + 1, min(h, bottom))

    crop = original_img.crop((left, top, right, bottom))
    return crop, (left, top, right, bottom)

def composite_food_onto_studio_background(
    original_img: Image.Image,
    studio_bg: Image.Image,
    box_2d: List[int],
    target_aspect: Tuple[int, int] = (4, 3),
    food_ratio: float = 0.55
) -> Tuple[Image.Image, Image.Image]:
    """
    Composites the untouched food pixels from original_img onto studio_bg,
    centering the dish and enforcing the food-to-background ratio.
    Returns (final_composite, food_mask).
    """
    orig_w, orig_h = original_img.size
    food_crop, (left, top, right, bottom) = extract_food_roi(original_img, box_2d)
    food_w, food_h = food_crop.size

    # Resize studio background to target resolution (e.g. 1200x900 for 4:3)
    target_canvas_w = 1200
    target_canvas_h = int(target_canvas_w * (target_aspect[1] / target_aspect[0]))
    canvas = studio_bg.resize((target_canvas_w, target_canvas_h), Image.Resampling.LANCZOS).convert("RGBA")

    # Scale food so its dominant dimension covers food_ratio of canvas
    scale_w = (target_canvas_w * food_ratio) / food_w
    scale_h = (target_canvas_h * food_ratio) / food_h
    scale = min(scale_w, scale_h)

    new_food_w = max(50, int(food_w * scale))
    new_food_h = max(50, int(food_h * scale))
    scaled_food = food_crop.resize((new_food_w, new_food_h), Image.Resampling.LANCZOS).convert("RGBA")

    # Center coordinates on canvas
    paste_x = (target_canvas_w - new_food_w) // 2
    paste_y = (target_canvas_h - new_food_h) // 2

    # Create smooth feathered elliptical mask around dish to avoid harsh rectangular cuts
    mask = Image.new("L", (new_food_w, new_food_h), 0)
    draw = ImageDraw.Draw(mask)
    # Draw oval / rounded rectangle
    draw.ellipse([2, 2, new_food_w - 3, new_food_h - 3], fill=255)
    # Feather edges with Gaussian Blur
    feathered_mask = mask.filter(ImageFilter.GaussianBlur(radius=4))

    # Paste scaled food cutout onto studio canvas using feathered alpha
    canvas.paste(scaled_food, (paste_x, paste_y), mask=feathered_mask)

    return canvas.convert("RGB"), feathered_mask
