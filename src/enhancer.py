"""Image enhancement engine powered by Gemini 3.0+ models with Truth-in-Advertising guardrails."""

import io
from typing import Dict, Any, Tuple, Optional
from google import genai
from google.genai import types
from PIL import Image

from src.config import GCP_PROJECT, GCP_LOCATION, ENHANCEMENT_MODEL, PRO_ENHANCEMENT_MODEL, IMAGEN_CAPABILITY_MODEL
from src.preflight import image_to_bytes
from src.compositor import composite_food_onto_studio_background
from src.sota_vision import execute_strict_food_lock_swap, generate_digital_provenance

def get_genai_client() -> genai.Client:
    """Returns an authenticated Vertex AI Gemini Client configured for global endpoints."""
    valid_proj = GCP_PROJECT if (GCP_PROJECT and GCP_PROJECT != "your-gcp-project-id") else None
    return genai.Client(vertexai=True, project=valid_proj, location=GCP_LOCATION)

BACKGROUND_PRESETS = {
    "warm_slate": "Resting naturally on a clean, elegant dark slate restaurant serving board or tabletop with soft diffused ambient studio lighting and realistic contact shadows.",
    "rustic_wood": "Elegantly presented on a rustic dark walnut cutting board or dining table with rich natural wood grain, warm ambient restaurant lighting, and realistic contact shadows.",
    "white_marble": "Placed on a luxurious clean white Carrara marble tabletop with subtle pale gray veining, bright diffused daylight, and soft natural shadows.",
    "dark_granite": "Arranged on an elegant, matte dark charcoal granite dining surface with soft warm spotlighting and editorial restaurant depth of field."
}

def enhance_menu_image(
    original_img: Image.Image,
    analysis: Dict[str, Any],
    sop_decision: Dict[str, Any],
    custom_bg_prompt: Optional[str] = None,
    food_ratio: float = 0.55,
    target_aspect: Tuple[int, int] = (4, 3),
    use_pro_model: bool = False,
    strict_anti_hallucination: bool = True,
    enhancement_mode: str = "studio_reshoot",
    corrective_directive: Optional[str] = None,
    self_healing_fallback_retry: bool = False
) -> Tuple[Image.Image, Dict[str, Any]]:
    """
    Executes commercial food photoshoot enhancement via SOTA Google Cloud tools (as of Oct 2026):
    - Mode 'background_swap': Imagen 3 Capability EDIT_MODE_BGSWAP (Strict 100% raw food pixel lock).
    - Mode 'studio_reshoot': Gemini Nano Banana 2.1 (gemini-nano-banana-2.1) / Gemini 3 Pro Image commercial reshoot.
    Both modes automatically embed SynthID v2 watermarking and C2PA Content Credentials.
    """
    client = get_genai_client()
    transformation_log = []
    dish_name = analysis.get("primary_dish_name", "dish")
    metadata = analysis.get("metadata_enrichment", {})
    cuisines = ", ".join(metadata.get("cuisines", ["restaurant cuisine"]))
    surface_desc = custom_bg_prompt or BACKGROUND_PRESETS["warm_slate"]

    # =========================================================================
    # SOTA Mode A: Imagen 3 Strict Food-Lock Background Swap (EDIT_MODE_BGSWAP)
    # =========================================================================
    if enhancement_mode == "background_swap":
        swap_img, swap_meta = execute_strict_food_lock_swap(
            original_img=original_img,
            analysis=analysis,
            surface_prompt=surface_desc,
            target_aspect=target_aspect
        )
        provenance = generate_digital_provenance(
            filename=dish_name,
            transformation_mode="STRICT_FOOD_LOCK_BGSWAP",
            model_used=IMAGEN_CAPABILITY_MODEL,
            is_authentic=True
        )
        metadata_out = {
            "transformation_log": swap_meta.get("transformation_log", []),
            "enhanced_width": swap_img.width,
            "enhanced_height": swap_img.height,
            "aspect_ratio": f"{swap_img.width}:{swap_img.height}",
            "model_used": IMAGEN_CAPABILITY_MODEL,
            "background_prompt_used": surface_desc,
            "strict_anti_hallucination": True,
            "is_commercial_studio_shoot": True,
            "is_strict_food_lock": True,
            "enhancement_mode": "background_swap",
            "digital_provenance": provenance
        }
        return swap_img, metadata_out

    # =========================================================================
    # SOTA Mode B: Gemini Nano Banana 2.1 / Gemini 3 Pro Commercial Studio Reshoot
    # =========================================================================
    model_to_use = PRO_ENHANCEMENT_MODEL if use_pro_model else ENHANCEMENT_MODEL

    # Truth-in-Advertising anti-hallucination constraint block
    anti_text_constraint = (
        " CRITICAL MANDATORY REQUIREMENT - ZERO TEXT TOLERANCE: Absolutely NO text, NO words, NO letters, "
        "NO numbers, NO typography, NO slogans, NO titles, NO subtitles, NO watermarks, NO brand names, and NO labels. "
        "The output must be 100% clean culinary photography depicting ONLY the physical food and tabletop surface. "
        "Do NOT render any marketing copy, ad text, or headlines anywhere on the canvas."
    )
    guardrail_constraint = ""
    if strict_anti_hallucination:
        guardrail_constraint = (
            " STRICT TRUTH-IN-ADVERTISING GUARDRAIL: Do NOT add any garnishes, herbs, cilantro, parsley, "
            "sesame seeds, chili flakes, extra dipping sauce ramekins, side dishes, wine glasses, or cutlery "
            "that do not already exist in the original submission. Maintain the exact food ingredients, portion size, and arrangement. "
            "Do NOT invent or embellish gourmet textures that diverge from the raw upload."
            f"{anti_text_constraint}"
        )

    # Plate & Tableware Geometry preservation directive (with handheld food remediation)
    body_parts_present = analysis.get("safety_and_policy", {}).get("body_parts_on_food", False)
    objects_to_remove = analysis.get("spatial_rois", {}).get("objects_to_remove", [])
    has_hand_roi = any(
        any(k in str(obj.get("label", "")).lower() for k in ("hand", "finger", "thumb", "wrist", "arm", "person", "human", "chef", "body", "torso"))
        for obj in objects_to_remove if isinstance(obj, dict)
    )
    tableware_geom = analysis.get("spatial_rois", {}).get("tableware_geometry", "restaurant serving dish")
    if not tableware_geom or any(w in tableware_geom.lower() for w in ["hand", "none", "air", "finger", "wrapper"]):
        tableware_geom = "clean ceramic restaurant plate or wooden serving board"

    if body_parts_present or has_hand_roi:
        plate_geometry_directive = (
            f" CRITICAL HUMAN & BODY PART REMOVAL: Completely remove all human hands, fingers, thumbs, wrists, arms, chef/person torsos, aprons, and people from the image. "
            f"Reconstruct any food or plate edges previously occluded by fingers or hands naturally and seamlessly. "
            f"Place the plated dish ({tableware_geom}) or handheld food naturally resting flat onto {surface_desc} with realistic gravity and contact shadows."
        )
    else:
        plate_geometry_directive = (
            f" TABLEWARE & PLATING GEOMETRY PRESERVATION: Preserve the authentic plating format, container type, and vessel geometry of the original submission (e.g. {tableware_geom}). "
            "The food must remain in or on its authentic vessel (upgraded to clean, commercial restaurant ceramic, porcelain, or stoneware matching the original geometry and proportions). "
            "Do NOT discard the plate, do NOT dump food directly onto the bare table surface, and do NOT alter the fundamental vessel geometry (e.g. do not turn a bowl into a flat plate or vice versa)."
        )

    corrective_block = ""
    if corrective_directive:
        corrective_block = (
            f" MANDATORY AUDITOR REMEDIATION DIRECTIVE (PASS 2 SELF-HEALING): "
            f"{corrective_directive} "
            f"Adhere strictly to this instruction and do not reproduce the rejected elements."
        )

    # Commercial Menu Framing & Studio Presentation directive
    framing_directive = (
        f" COMMERCIAL MENU FRAMING & STUDIO COMPOSITION: Present the complete plated dish in an appetizing, professional restaurant menu photoshoot. "
        f"If the raw submission is tightly cropped or cuts off edges of the dish/tableware, naturally reframe and uncrop the complete plated dish ({tableware_geom}) on {surface_desc}, "
        f"revealing the natural plate perimeter, contact shadows, clean tabletop surface, and warm restaurant dining atmosphere."
    )

    if self_healing_fallback_retry:
        enhancement_prompt = (
            f"High-end commercial restaurant menu photography of the authentic {dish_name} from the submission ({cuisines}). "
            f"Present the single complete plated dish ({tableware_geom}) resting naturally on {surface_desc} with warm studio lighting and realistic contact shadows. "
            f"STRICT TRUTH-IN-ADVERTISING GUARDRAIL: Preserve the exact food ingredients, toppings, portion size, and crust/texture from the submission. "
            f"Do NOT add any fresh basil leaves, herbs, greens, oil cruets, salt shakers, side props, cutlery, or extra dishes that are not on the original dish. "
            f"{corrective_block} "
            f"Depict ONLY the plated food on the clean tabletop surface—no people, no hands, no background kitchen equipment, and zero text, letters, or numbers anywhere on the image."
        )
    else:
        enhancement_prompt = (
            f"High-end commercial restaurant menu photography of authentic {dish_name} ({cuisines}). "
            f"The plated dish ({tableware_geom}) rests naturally on {surface_desc}. "
            f"{framing_directive} "
            f"{plate_geometry_directive} "
            f"{guardrail_constraint} "
            f"{corrective_block} "
            f"Ensure the plated dish and all original sauces are grounded naturally with realistic contact shadows, "
            f"warm appetizing studio lighting, subtle depth of field, and crisp commercial resolution. "
            f"Completely remove any human hands, fingers, arms, body parts, greasy paper wrappers, or cluttered background objects, leaving only the appetizing food on its serving dish. "
            f"Strictly forbidden: Any human hands or fingers, or any text, letters, or words anywhere in the photo."
        )

    # Optimize upload transit: cap input image at 1536px while preserving full photographic fidelity
    input_img = original_img.copy()
    if max(input_img.size) > 1536:
        input_img.thumbnail((1536, 1536), Image.Resampling.LANCZOS)
    img_bytes = image_to_bytes(input_img, format="JPEG", quality=92)
    transformation_log.append(f"GEMINI_3_IMAGE_DISPATCHED_{model_to_use}")

    candidate_models = [model_to_use]
    for fb_m in ["gemini-nano-banana-2.1", "gemini-2.5-flash-image"]:
        if fb_m not in candidate_models:
            candidate_models.append(fb_m)

    for candidate_model in candidate_models:
        try:
            response = client.models.generate_content(
                model=candidate_model,
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                    enhancement_prompt
                ]
            )
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.data:
                        enhanced_img = Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
                        transformation_log.append("COMMERCIAL_STUDIO_PHOTO_GENERATED_GEMINI_3")
                        provenance = generate_digital_provenance(
                            filename=dish_name,
                            transformation_mode="COMMERCIAL_STUDIO_RESHOOT",
                            model_used=model_to_use,
                            is_authentic=True
                        )
                        metadata_out = {
                            "transformation_log": transformation_log,
                            "enhanced_width": enhanced_img.width,
                            "enhanced_height": enhanced_img.height,
                            "aspect_ratio": f"{enhanced_img.width}:{enhanced_img.height}",
                            "model_used": model_to_use,
                            "backend_endpoint_used": candidate_model,
                            "background_prompt_used": surface_desc,
                            "strict_anti_hallucination": strict_anti_hallucination,
                            "is_commercial_studio_shoot": True,
                            "is_strict_food_lock": False,
                            "enhancement_mode": "studio_reshoot",
                            "digital_provenance": provenance
                        }
                        return enhanced_img, metadata_out
        except Exception as e:
            if candidate_model == model_to_use:
                transformation_log.append(f"GEMINI_PRIMARY_ENDPOINT_RETRY_{candidate_model}")
            else:
                transformation_log.append(f"GEMINI_3_IMAGE_ERROR_{str(e)[:80]}")

    # Fallback to mask-protected compositing if generation fails
    transformation_log.append("FALLBACK_MASK_PROTECTED_COMPOSITOR")
    studio_canvas = Image.new("RGB", (1200, 900), color=(235, 233, 230))
    spatial = analysis.get("spatial_rois", {})
    box_2d = spatial.get("food_plate_bounding_box", [100, 100, 900, 900])
    comp_img, _ = composite_food_onto_studio_background(original_img, studio_canvas, box_2d, target_aspect, food_ratio)
    provenance = generate_digital_provenance(
        filename=dish_name,
        transformation_mode="FALLBACK_COMPOSITOR",
        model_used="MaskProtectedCompositor",
        is_authentic=True
    )
    return comp_img, {
        "transformation_log": transformation_log,
        "enhanced_width": comp_img.width,
        "enhanced_height": comp_img.height,
        "aspect_ratio": f"{comp_img.width}:{comp_img.height}",
        "model_used": "MaskProtectedCompositor",
        "backend_endpoint_used": "MaskProtectedCompositor",
        "background_prompt_used": surface_desc,
        "strict_anti_hallucination": strict_anti_hallucination,
        "is_commercial_studio_shoot": False,
        "is_strict_food_lock": True,
        "enhancement_mode": "food_lock",
        "digital_provenance": provenance
    }
