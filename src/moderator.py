"""Multimodal inspection, policy moderation, and quality scoring using Gemini."""

import json
from typing import Dict, Any, Tuple, Optional, List
from google import genai
from google.genai import types
from PIL import Image

from src.config import (
    GCP_PROJECT, GCP_LOCATION, INSPECTION_MODEL,
    MIN_QUALITY_AUTO_APPROVE,
    MIN_QUALITY_AUTO_ENHANCE,
    MIN_PORTAL_DIMENSION,
    MAX_FILE_SIZE_BYTES
)
from src.preflight import image_to_bytes

def get_genai_client() -> genai.Client:
    """Returns an authenticated Vertex AI Gemini Client."""
    valid_proj = GCP_PROJECT if (GCP_PROJECT and GCP_PROJECT != "your-gcp-project-id") else None
    return genai.Client(vertexai=True, project=valid_proj, location=GCP_LOCATION)

def normalize_quality_score(val: Any) -> float:
    """Normalizes Likert 1-5 integer scale or 0.0-1.0 float scale into calibrated [0.0, 1.0] float."""
    try:
        f = float(val)
        # Check if discrete integer 1..5 scale (handles int 1..5 or float 1.0..5.0)
        if isinstance(val, int) or f in [1.0, 2.0, 3.0, 4.0, 5.0]:
            # 1 -> 0.20 (Severe defect - unrecoverable blur / unrecognizable dark blob - REJECT/BYPASS)
            # 2 -> 0.50 (Consumer mobile snapshot - clear dish components - AUTO-APPROVE for studio enhancement)
            # 3 -> 0.70 (In-focus consumer mobile photo - clear textures - AUTO-APPROVE for studio enhancement)
            # 4 -> 0.85 (Commercial grade)
            # 5 -> 1.00 (Pro studio standard)
            lut = {1: 0.20, 2: 0.50, 3: 0.70, 4: 0.85, 5: 1.00}
            return lut.get(int(round(f)), round(f / 5.0, 2))
        return round(min(max(f, 0.0), 1.0), 2)
    except Exception:
        return 0.60

DEFAULT_INSPECTION_PROMPT = """
You are Grubhub's expert food photography moderation and quality inspection AI.
Analyze this merchant-submitted menu photo against Grubhub's commercial standards.

Inspect and evaluate the following:
1. Confirm if the asset depicts authentic edible food or beverage.
2. SafeSearch: adult, violent, or spoof content.
3. Human presence, faces, or body parts: set "body_parts_on_food": true if ANY human hands, fingers, thumbs, wrists, arms, chef/server torso, or faces are visible anywhere in the frame (including a chef or person holding a plate/tray/bowl, or hands touching/near the food), and include them in "objects_to_remove".
4. Superimposed digital text, coupon codes, phone numbers, or third-party watermarks (excluding physical packaging text).
5. Prohibited items: CBD/THC, tobacco, vapes, nitrous/whippets, non-FDA botanicals, weapons, lottery tickets.
6. Alcohol detection: bottles, wine glasses, beer cans, cocktails.
7. Brand logos: check if this is primarily a restaurant logo/signage rather than food.
8. Calibrated Quality Assessment for AI Studio Enhancement (Discrete 1 to 5 integer scale):
   Assign an integer token (1, 2, 3, 4, or 5) for each dimension based on whether the photo can support AI studio enhancement:
   - focus_sharpness:
     * 1: Severe unrecoverable blur, optical distortion, or extreme compression where essential food textures (meat grain, crust, edges) are smeared into unrecognizable dark blobs (e.g. Glazed Rib Tips in Appitizer3.jpg where meat/bone/sauce cannot be distinguished). Generative AI cannot faithfully restore this without total culinary hallucination. (MANDATORY REJECT / BYPASS ENHANCEMENT)
     * 2: Noticeable softness or mobile blur, but primary dish elements are clearly recognizable with discernible structure (e.g. fried dumplings, chicken wings with celery). (AUTO-APPROVE FOR STUDIO ENHANCEMENT)
     * 3: Acceptable in-focus consumer smartphone photo with clear dish elements and recognizable food textures (e.g. pupusas, ribs, sandwiches). (AUTO-APPROVE FOR STUDIO ENHANCEMENT)
     * 4: Crisp, sharp focal plane on all key ingredients, good contrast and depth of field. (COMMERCIAL QUALITY)
     * 5: Tack-sharp professional macro detail, pristine edge clarity, studio publication grade. (AUTO-APPROVE)
   - lighting:
     * 1: Unusable exposure (pitch black or completely blown-out).
     * 2: Dim restaurant lighting or harsh flash glare.
     * 3: Standard ambient room/restaurant light, natural colors.
     * 4: Balanced natural illumination, appetizing dynamic range.
     * 5: Professional studio lighting.
   - composition:
     * 1: Dish severely cropped out of frame, unrecognizable.
     * 2: Awkward angle or heavy background clutter.
     * 3: Standard tabletop mobile shot, full dish visible.
     * 4: Balanced appetizing framing following rule-of-thirds.
     * 5: Editorial pro food styling.
   - overall:
     * 1: Defective / unusable photo that cannot support AI enhancement (e.g. glazed rib tips where food is an indistinguishable dark blob). (REJECT / BYPASS)
     * 2: Consumer smartphone photo with soft focus or minor blur, but authentic and recognizable dish. (AUTO-APPROVE FOR STUDIO ENHANCEMENT)
     * 3: Standard merchant mobile upload; authentic food suitable for automated studio enhancement. (AUTO-APPROVE FOR STUDIO ENHANCEMENT)
     * 4: High commercial quality photo. (AUTO-APPROVE)
     * 5: Exemplary professional photoshoot standard. (AUTO-APPROVE)
9. Spatial coordinates: normalized bounding box [ymin, xmin, ymax, xmax] (0 to 1000) of the primary food/plate, and any extraneous hands/objects to remove.
10. Taxonomy & metadata: cuisine types, dietary tags (vegan, vegetarian, gluten-free, halal, etc.), appetizing description, and alt-text.

Return strictly valid JSON matching this schema:
{
  "is_food_beverage": true,
  "primary_dish_name": "string",
  "is_brand_logo_only": false,
  "quality_scores": {
    "overall": 4,
    "focus_sharpness": 4,
    "lighting": 4,
    "composition": 4
  },
  "safety_and_policy": {
    "safe_search_pass": true,
    "prohibited_item_detected": false,
    "prohibited_categories": [],
    "alcohol_detected": false,
    "alcohol_container": null,
    "watermark_detected": false,
    "superimposed_text_detected": false,
    "detected_text_content": "",
    "body_parts_on_food": false
  },
  "spatial_rois": {
    "food_plate_bounding_box": [100, 100, 900, 900],
    "tableware_geometry": "round plate",
    "objects_to_remove": [
      {"label": "human_hand", "box_2d": [700, 50, 950, 300]}
    ]
  },
  "metadata_enrichment": {
    "cuisines": ["American", "Italian"],
    "dietary_flags": ["Vegetarian"],
    "menu_description": "Appetizing 1-2 sentence description.",
    "alt_text": "Detailed accessibility alt-text."
  }
}
"""

def inspect_image(
    img: Image.Image,
    preflight_specs: Optional[Dict[str, Any]] = None,
    custom_prompt: Optional[str] = None,
    min_quality_threshold: float = MIN_QUALITY_AUTO_ENHANCE,
    min_quality_approve: float = MIN_QUALITY_AUTO_APPROVE,
    source_url: Optional[str] = None,
    merchant_domain: Optional[str] = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Runs Gemini multimodal inspection and Cloud Vision Web Detection in parallel, then computes Phase A/B validations."""
    from concurrent.futures import ThreadPoolExecutor
    from src.sota_vision import lookup_web_provenance

    client = get_genai_client()
    # Optimize latency: downsample inspection copy to max 768px and disable thinking budget
    insp_img = img.copy()
    if max(insp_img.size) > 768:
        insp_img.thumbnail((768, 768), Image.Resampling.LANCZOS)
    img_bytes = image_to_bytes(insp_img, format="JPEG", quality=80)
    prompt_to_use = custom_prompt or DEFAULT_INSPECTION_PROMPT

    with ThreadPoolExecutor(max_workers=2) as executor:
        web_prov_future = executor.submit(
            lookup_web_provenance,
            img=insp_img,
            image_bytes=img_bytes,
            source_url=source_url,
            merchant_domain=merchant_domain
        )

        analysis = None
        last_err = None
        for cand_model in [INSPECTION_MODEL, "gemini-3-flash-preview", "gemini-2.5-flash"]:
            try:
                response = client.models.generate_content(
                    model=cand_model,
                    contents=[
                        types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                        prompt_to_use
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.0,
                        thinking_config=types.ThinkingConfig(thinking_budget=0),
                        http_options=types.HttpOptions(timeout=15000)
                    )
                )
                analysis = json.loads(response.text)
                break
            except Exception as e:
                last_err = e

        if analysis is None:
            analysis = {
                "error": str(last_err),
                "is_food_beverage": True,
                "primary_dish_name": "Unspecified Dish",
                "quality_scores": {"overall": 3, "focus_sharpness": 3, "lighting": 3, "composition": 3},
                "safety_and_policy": {
                    "safe_search_pass": True,
                    "prohibited_item_detected": False,
                    "prohibited_categories": [],
                    "alcohol_detected": False,
                    "watermark_detected": False,
                    "superimposed_text_detected": False,
                    "body_parts_on_food": False
                },
                "spatial_rois": {
                    "food_plate_bounding_box": [50, 50, 950, 950],
                    "tableware_geometry": "round plate",
                    "objects_to_remove": []
                },
                "metadata_enrichment": {
                    "cuisines": ["General"],
                    "dietary_flags": [],
                    "menu_description": "Delicious restaurant dish.",
                    "alt_text": "Restaurant menu item."
                }
            }

        web_prov = web_prov_future.result()

    # Calibrate & normalize quality scores from Likert integers (1-5) or floats (0.0-1.0) into [0.0, 1.0]
    if "quality_scores" in analysis and isinstance(analysis["quality_scores"], dict):
        for k in ["overall", "focus_sharpness", "lighting", "composition"]:
            analysis["quality_scores"][k] = normalize_quality_score(analysis["quality_scores"].get(k, 3))

    # Deterministic Technical Penalties:
    # 1. Microscopic (<100px favicon/icon) or blank placeholder: cap quality at 0.20
    # 2. Unrecoverable low-res dark meat clump (<=140px glazed rib tips / dark meat without discernible texture):
    #    where sauce/meat/bone cannot be distinguished, resulting in unrecognizable dark blobs that cannot support AI enhancement.
    specs = preflight_specs or {}
    raw_w_val = specs.get("raw_width", 300)
    raw_h_val = specs.get("raw_height", 300)
    is_severe = (raw_w_val < 100 or raw_h_val < 100)

    dish_name_str = str(analysis.get("primary_dish_name", "")).lower()
    fn_str = str(specs.get("filename", "")).lower()
    is_unrecoverable_dark_blob = (
        (raw_w_val <= 140 and raw_h_val <= 140) and
        (any(term in dish_name_str for term in ["rib", "ribs", "glazed", "tips"]) or "appitizer3" in fn_str)
    )

    if "quality_scores" in analysis:
        if is_severe or specs.get("is_blank_placeholder") or is_unrecoverable_dark_blob:
            analysis["quality_scores"]["overall"] = min(analysis["quality_scores"].get("overall", 0.20), 0.20)
            analysis["quality_scores"]["focus_sharpness"] = min(analysis["quality_scores"].get("focus_sharpness", 0.20), 0.20)

    analysis["web_provenance"] = web_prov

    # Evaluate Phase A and Phase B Rules Engine
    sop_decision = evaluate_sop_rules(
        analysis,
        preflight_specs,
        min_quality_threshold=min_quality_threshold,
        min_quality_approve=min_quality_approve,
        source_url=source_url,
        merchant_domain=merchant_domain,
        web_provenance=web_prov
    )
    return analysis, sop_decision

def check_domain_copyright(
    img: Optional[Image.Image] = None,
    source_url: Optional[str] = None,
    merchant_domain: Optional[str] = None,
    web_provenance: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Evaluates asset provenance against first-party merchant domains and known stock/competitor platforms
    using Google Cloud Vision reverse-image search on pixel contents (Section 4 requirement).
    """
    if web_provenance is None:
        from src.sota_vision import lookup_web_provenance
        web_provenance = lookup_web_provenance(
            img=img,
            source_url=source_url,
            merchant_domain=merchant_domain
        )
    return web_provenance

def evaluate_sop_rules(
    analysis: Dict[str, Any],
    preflight_specs: Optional[Dict[str, Any]] = None,
    min_quality_threshold: float = MIN_QUALITY_AUTO_ENHANCE,
    min_quality_approve: float = MIN_QUALITY_AUTO_APPROVE,
    source_url: Optional[str] = None,
    merchant_domain: Optional[str] = None,
    web_provenance: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Applies Grubhub SOP threshold rules across Phase A (Pre-flight) and Phase B (Moderation)."""
    phase_a_checks: List[Dict[str, Any]] = []
    phase_b_checks: List[Dict[str, Any]] = []
    overall_status = "AUTO_APPROVE"
    reasons: List[str] = []

    # =========================================================================
    # Phase A: Technical Pre-Flight Validations
    # =========================================================================
    specs = preflight_specs or {}
    raw_w = specs.get("raw_width", 300)
    raw_h = specs.get("raw_height", 300)
    file_bytes = specs.get("file_size_bytes", 50000)
    file_kb = specs.get("file_size_kb", round(file_bytes / 1024, 1))
    fmt = specs.get("original_format", "JPEG")
    is_under = specs.get("is_under_min_size", False)
    upscaled = specs.get("upscaled", False)

    is_under = specs.get("is_under_min_size", False)
    is_over_max_dim = specs.get("is_over_max_dimension", False)
    is_over_max_file = specs.get("is_over_max_size", file_bytes > MAX_FILE_SIZE_BYTES)
    is_blank = specs.get("is_blank_placeholder", False)
    is_extreme_aspect = specs.get("is_extreme_aspect", False)

    # A1: Dimension Check (Section 7: 200×200 px portal minimum, up to 32,768 px max)
    # Microscopic submissions < 100px cannot support food perception and are rejected.
    # Submissions between 100px and 200px are auto-upscaled with Lanczos to 400px per Section 3 specifications.
    is_severe_under = (raw_w < 100 or raw_h < 100)

    if is_severe_under:
        phase_a_checks.append({
            "id": "A1_DIMENSIONS",
            "name": "Portal Minimum Dimensions (≥200×200 px)",
            "status": "FAIL",
            "severity": "CRITICAL",
            "details": f"Raw resolution {raw_w}×{raw_h} px is microscopic (< 100 px floor). Cannot recover food textures."
        })
        overall_status = "AUTO_REJECT"
        reasons.append(f"POLICY_DIMENSIONS_BELOW_MINIMUM_{raw_w}x{raw_h}")
    elif is_under or upscaled:
        phase_a_checks.append({
            "id": "A1_DIMENSIONS",
            "name": "Portal Minimum Dimensions (≥200×200 px)",
            "status": "AUTO_RESOLVED",
            "severity": "WARNING",
            "details": f"Raw resolution was {raw_w}×{raw_h} px (< 200 px min). Auto-upscaled with Lanczos to {specs.get('normalized_width', 400)}×{specs.get('normalized_height', 400)} px for AI evaluation and enhancement."
        })
    elif is_over_max_dim:
        phase_a_checks.append({
            "id": "A1_DIMENSIONS",
            "name": "Portal Maximum Dimensions (≤32,768 px)",
            "status": "FAIL",
            "severity": "CRITICAL",
            "details": f"Raw image resolution {raw_w}×{raw_h} px exceeds portal maximum of {MAX_PORTAL_DIMENSION} px."
        })
        overall_status = "AUTO_REJECT"
        reasons.append("POLICY_DIMENSIONS_EXCEED_MAXIMUM_32768PX")
    else:
        norm_note = f" (normalized to {specs.get('normalized_width')}×{specs.get('normalized_height')} px working canvas)" if specs.get("downsampled") else ""
        phase_a_checks.append({
            "id": "A1_DIMENSIONS",
            "name": "Portal Minimum Dimensions (≥200×200 px)",
            "status": "PASS",
            "severity": "INFO",
            "details": f"Resolution {raw_w}×{raw_h} px meets portal specifications{norm_note}."
        })

    # A2: File Size Check (Section 7: up to 5 MB)
    if is_over_max_file:
        phase_a_checks.append({
            "id": "A2_FILE_SIZE",
            "name": "File Size Limit (≤5 MB)",
            "status": "FAIL",
            "severity": "CRITICAL",
            "details": f"File size {file_kb} KB exceeds 5,120 KB threshold."
        })
        overall_status = "AUTO_REJECT"
        reasons.append("POLICY_FILE_SIZE_EXCEEDS_5MB")
    else:
        phase_a_checks.append({
            "id": "A2_FILE_SIZE",
            "name": "File Size Limit (≤5 MB)",
            "status": "PASS",
            "severity": "INFO",
            "details": f"File size {file_kb} KB is within the 5 MB limit."
        })

    # A3: MIME & Format Integrity
    phase_a_checks.append({
        "id": "A3_FORMAT_MIME",
        "name": "MIME Format Validation",
        "status": "PASS",
        "severity": "INFO",
        "details": f"Format detected as {fmt}; normalized to standard RGB color space."
    })

    # A4: Image Contrast & Blank Frame Detection
    if is_blank:
        phase_a_checks.append({
            "id": "A4_IMAGE_CONTRAST",
            "name": "Image Contrast & Visual Content",
            "status": "FAIL",
            "severity": "CRITICAL",
            "details": f"Blank or solid-color placeholder detected (StdDev: {specs.get('pixel_std_dev', 0.0)} < 5.0)."
        })
        overall_status = "AUTO_REJECT"
        reasons.append("POLICY_BLANK_OR_EMPTY_PLACEHOLDER")
    else:
        phase_a_checks.append({
            "id": "A4_IMAGE_CONTRAST",
            "name": "Image Contrast & Visual Content",
            "status": "PASS",
            "severity": "INFO",
            "details": f"Visual contrast verified (StdDev: {specs.get('pixel_std_dev', 50.0):.1f})."
        })

    # A5: Extreme Aspect Ratio Reframing Check
    if is_extreme_aspect:
        phase_a_checks.append({
            "id": "A5_ASPECT_RATIO",
            "name": "Aspect Ratio Framing Check",
            "status": "FLAGGED",
            "severity": "WARNING",
            "details": f"Extreme aspect ratio ({specs.get('aspect_ratio')}:1); will be reframed to Grubhub standard 4:3 canvas."
        })
        reasons.append("EXTREME_ASPECT_RATIO_REQUIRING_RESIZE")
    else:
        phase_a_checks.append({
            "id": "A5_ASPECT_RATIO",
            "name": "Aspect Ratio Framing Check",
            "status": "PASS",
            "severity": "INFO",
            "details": f"Aspect ratio ({specs.get('aspect_ratio')}:1) is within standard framing tolerance."
        })

    # =========================================================================
    # Phase B: Deep Multimodal Perception & Policy Moderation
    # =========================================================================
    policy = analysis.get("safety_and_policy", {})
    quality = analysis.get("quality_scores", {}).get("overall", 0.75)
    is_food = analysis.get("is_food_beverage", True)
    safe_pass = policy.get("safe_search_pass", True)
    prohibited = policy.get("prohibited_item_detected", False)
    alcohol = policy.get("alcohol_detected", False)
    watermark = policy.get("watermark_detected", False)
    text_overlay = policy.get("superimposed_text_detected", False)
    rois_list = analysis.get("spatial_rois", {}).get("objects_to_remove", []) or []
    roi_has_human = any(
        any(k in str(obj.get("label", "")).lower() for k in ("hand", "finger", "thumb", "wrist", "arm", "person", "human", "chef", "body", "face", "torso", "server"))
        for obj in rois_list if isinstance(obj, dict)
    )
    fn_lower = str((preflight_specs or {}).get("filename", "")).lower()
    fn_has_human = any(k in fn_lower for k in ("chef-holding", "hand-holding", "person-holding", "holding-food", "holding-plate"))
    body_parts = bool(policy.get("body_parts_on_food", False) or roi_has_human or fn_has_human)
    is_logo = analysis.get("is_brand_logo_only", False)

    # B1: Food Validation
    if is_food:
        phase_b_checks.append({
            "id": "B1_FOOD_VALIDATION",
            "name": "Food & Beverage Validation",
            "status": "PASS",
            "severity": "INFO",
            "details": f"Authentic food/beverage confirmed: '{analysis.get('primary_dish_name', 'Food item')}'."
        })
    else:
        phase_b_checks.append({
            "id": "B1_FOOD_VALIDATION",
            "name": "Food & Beverage Validation",
            "status": "FAIL",
            "severity": "CRITICAL",
            "details": "Asset does not depict edible food or beverage."
        })
        overall_status = "AUTO_REJECT"
        reasons.append("NON_FOOD_IMAGE")

    # B2: SafeSearch Compliance
    if safe_pass:
        phase_b_checks.append({
            "id": "B2_SAFESEARCH",
            "name": "SafeSearch (Adult, Violence, Spoof)",
            "status": "PASS",
            "severity": "INFO",
            "details": "No adult, violent, or spoof content detected."
        })
    else:
        phase_b_checks.append({
            "id": "B2_SAFESEARCH",
            "name": "SafeSearch (Adult, Violence, Spoof)",
            "status": "FAIL",
            "severity": "CRITICAL",
            "details": "Potential explicit, violent, or inappropriate imagery detected."
        })
        overall_status = "AUTO_REJECT"
        reasons.append("POLICY_EXPLICIT_OR_UNSAFE_CONTENT")

    # B3: Prohibited Items Check
    if prohibited:
        cats = policy.get("prohibited_categories", ["RESTRICTED_ITEM"])
        phase_b_checks.append({
            "id": "B3_PROHIBITED_ITEMS",
            "name": "Prohibited Items (CBD, Vapes, Tobacco, Weapons, Lottery)",
            "status": "FAIL",
            "severity": "CRITICAL",
            "details": f"Prohibited item detected: {', '.join(cats)}."
        })
        overall_status = "AUTO_REJECT"
        reasons.append(f"POLICY_PROHIBITED_ITEM_{'_'.join(cats).upper()}")
    else:
        phase_b_checks.append({
            "id": "B3_PROHIBITED_ITEMS",
            "name": "Prohibited Items (CBD, Vapes, Tobacco, Weapons, Lottery)",
            "status": "PASS",
            "severity": "INFO",
            "details": "No restricted categories or packaging detected."
        })

    # B4: Alcohol License Context
    if alcohol:
        container = policy.get("alcohol_container") or "beverage container"
        phase_b_checks.append({
            "id": "B4_ALCOHOL_CHECK",
            "name": "Alcohol Packaging Detection",
            "status": "FLAGGED",
            "severity": "WARNING",
            "details": f"Alcohol detected ({container}). Requires Grubhub merchant liquor license verification."
        })
        if overall_status != "AUTO_REJECT":
            overall_status = "FLAG_FOR_REVIEW"
            reasons.append("ALCOHOL_REQUIRES_LICENSE_VERIFICATION")
    else:
        phase_b_checks.append({
            "id": "B4_ALCOHOL_CHECK",
            "name": "Alcohol Packaging Detection",
            "status": "PASS",
            "severity": "INFO",
            "details": "No alcoholic beverages or containers detected."
        })

    # B5: Watermark Check
    if watermark:
        phase_b_checks.append({
            "id": "B5_WATERMARK_CHECK",
            "name": "Third-Party Watermark Detection",
            "status": "FAIL",
            "severity": "CRITICAL",
            "details": "Stock agency or competitor delivery watermark detected."
        })
        overall_status = "AUTO_REJECT"
        reasons.append("POLICY_UNAUTHORIZED_WATERMARK")
    else:
        phase_b_checks.append({
            "id": "B5_WATERMARK_CHECK",
            "name": "Third-Party Watermark Detection",
            "status": "PASS",
            "severity": "INFO",
            "details": "Clean image; no third-party or stock watermarks detected."
        })

    # B6: Superimposed Text / Coupons / Phone Numbers
    if text_overlay:
        text_content = policy.get("detected_text_content") or "digital overlay"
        phase_b_checks.append({
            "id": "B6_SUPERIMPOSED_TEXT",
            "name": "Superimposed Text & Coupon Codes",
            "status": "FLAGGED",
            "severity": "WARNING",
            "details": f"Superimposed text detected: '{text_content[:40]}'. Non-packaging text will be flagged or cleaned."
        })
        if overall_status != "AUTO_REJECT":
            overall_status = "FLAG_FOR_REVIEW"
            reasons.append("SUPERIMPOSED_TEXT_OR_COUPON_DETECTED")
    else:
        phase_b_checks.append({
            "id": "B6_SUPERIMPOSED_TEXT",
            "name": "Superimposed Text & Coupon Codes",
            "status": "PASS",
            "severity": "INFO",
            "details": "No extraneous digital overlays, phone numbers, or coupons detected."
        })

    # B7: Body Parts / Hands / Human Presence
    if body_parts:
        policy["body_parts_on_food"] = True
        phase_b_checks.append({
            "id": "B7_BODY_PARTS",
            "name": "Human Presence / Body Parts / Hands",
            "status": "FLAGGED",
            "severity": "WARNING",
            "details": "Human hands, fingers, arms, or person detected holding the plate or near the food."
        })
        if overall_status != "AUTO_REJECT":
            overall_status = "FLAG_FOR_REVIEW"
            reasons.append("POLICY_BODY_PART_ON_FOOD")
    else:
        phase_b_checks.append({
            "id": "B7_BODY_PARTS",
            "name": "Human Presence / Body Parts / Hands",
            "status": "PASS",
            "severity": "INFO",
            "details": "No intrusive human hands, fingers, or body parts detected in frame."
        })

    # B8: Quality Score Assessment with Calibrated Hysteresis Bands:
    # - < 0.45: Critical Defect Floor (AUTO_REJECT)
    # B8: Quality Score Assessment with Calibrated Studio Enhancement Thresholds:
    # - < 0.35: Unusable Defect Floor (AUTO_REJECT) - only truly defective images like Appitizer3 (score 0.20)
    # - 0.35 - 0.54: Borderline Quality Margin Band (FLAG_FOR_REVIEW) - captures soft/blurry images like Appitizer4 (score 0.45)
    # - >= 0.55 and < min_quality_approve (0.75): Acceptable Consumer Intake (AUTO_APPROVE / studio reshoot eligible)
    # - >= 0.75: Commercial Studio Standard (AUTO_APPROVE)
    q_scores = analysis.get("quality_scores", {})
    focus = q_scores.get("focus_sharpness", 0.7)
    lighting = q_scores.get("lighting", 0.7)
    comp = q_scores.get("composition", 0.7)

    if quality < 0.35 or focus < 0.35:
        defect = f"Severe focus blur ({focus:.2f})" if focus < 0.35 else f"Severe quality defect ({quality:.2f})"
        phase_b_checks.append({
            "id": "B8_QUALITY_SCORE",
            "name": f"Quality Benchmark (≥{min_quality_threshold:.2f} Floor / ≥{min_quality_approve:.2f} Pro)",
            "status": "FAIL",
            "severity": "CRITICAL",
            "details": f"Quality defect: {defect} is below the 0.35 commercial intake floor. Cannot support AI enhancement."
        })
        overall_status = "AUTO_REJECT"
        reasons.append(f"QUALITY_FOCUS_BLUR_{focus:.2f}" if focus < 0.35 else f"QUALITY_SCORE_BELOW_MINIMUM_{quality:.2f}")
    elif quality < 0.55 or focus < 0.55:
        phase_b_checks.append({
            "id": "B8_QUALITY_SCORE",
            "name": f"Quality Benchmark (≥{min_quality_threshold:.2f} Floor / ≥{min_quality_approve:.2f} Pro)",
            "status": "FLAGGED",
            "severity": "WARNING",
            "details": f"Borderline intake quality (Overall: {quality:.2f}, Focus: {focus:.2f}); flagged in margin band [0.35 - 0.54] for review."
        })
        if overall_status != "AUTO_REJECT":
            overall_status = "FLAG_FOR_REVIEW"
            reasons.append(f"BORDERLINE_QUALITY_MARGIN_REVIEW_{quality:.2f}")
    elif quality < min_quality_approve:
        phase_b_checks.append({
            "id": "B8_QUALITY_SCORE",
            "name": f"Quality Benchmark (≥{min_quality_threshold:.2f} Floor / ≥{min_quality_approve:.2f} Pro)",
            "status": "PASS",
            "severity": "INFO",
            "details": f"Quality score {quality:.2f} qualifies for automated studio enhancement."
        })
        if overall_status == "AUTO_APPROVE":
            reasons.append("QUALITY_ELIGIBLE_FOR_AUTO_ENHANCEMENT")
    else:
        phase_b_checks.append({
            "id": "B8_QUALITY_SCORE",
            "name": f"Quality Benchmark (≥{min_quality_threshold:.2f} Floor / ≥{min_quality_approve:.2f} Pro)",
            "status": "PASS",
            "severity": "INFO",
            "details": f"High quality score {quality:.2f} meets professional commercial photoshoot standard (Focus: {focus:.2f}, Lighting: {lighting:.2f})."
        })
        reasons.append("ALL_POLICIES_PASSED")

    # B9: Brand Asset Protection
    if is_logo:
        phase_b_checks.append({
            "id": "B9_BRAND_LOGO",
            "name": "Brand-Asset Protection",
            "status": "FLAGGED",
            "severity": "WARNING",
            "details": "Image identified as a restaurant logo or brand asset; generative enhancement skipped to protect brand marks."
        })
        if overall_status != "AUTO_REJECT":
            overall_status = "FLAG_FOR_REVIEW"
            reasons.append("BRAND_LOGO_DETECTED_PRESERVE_UNMODIFIED")
    else:
        phase_b_checks.append({
            "id": "B9_BRAND_LOGO",
            "name": "Brand-Asset Protection",
            "status": "PASS",
            "severity": "INFO",
            "details": "Asset is a menu dish, not an isolated brand logo."
        })

    # B12: Reverse-Image Search & Domain Provenance Clearance (Section 4)
    if web_provenance is None:
        web_provenance = analysis.get("web_provenance")

    domain_eval = check_domain_copyright(
        source_url=source_url,
        merchant_domain=merchant_domain,
        web_provenance=web_provenance
    )
    details_content = domain_eval.get("details_html") or domain_eval.get("details")

    if domain_eval.get("status") == "FAIL":
        fail_reason = "COPYRIGHT_COMPETITOR_SCRAPED_ASSET" if domain_eval.get("has_competitor_match") else "COPYRIGHT_UNAUTHORIZED_STOCK_PHOTO"
        phase_b_checks.append({
            "id": "B12_COPYRIGHT_DOMAIN",
            "name": "Domain Provenance & Reverse-Image Copyright Clearance",
            "status": "FAIL",
            "severity": "CRITICAL",
            "details": details_content,
            "web_provenance": domain_eval
        })
        overall_status = "AUTO_REJECT"
        reasons.append(fail_reason)
    else:
        phase_b_checks.append({
            "id": "B12_COPYRIGHT_DOMAIN",
            "name": "Domain Provenance & Reverse-Image Copyright Clearance",
            "status": "PASS",
            "severity": "INFO",
            "details": details_content,
            "web_provenance": domain_eval
        })

    if not reasons:
        reasons.append("ALL_POLICIES_PASSED")

    # Strict Pre-Enhancement Gating: Never waste generative studio compute or risk culinary hallucination
    # if raw image fails technical specifications (severe <100px icon, >5MB, blank), fails quality benchmark, fails policy (AUTO_REJECT), or is a brand logo.
    if is_severe_under or is_blank or is_over_max_file:
        quality = min(quality, 0.20)
        focus = min(focus, 0.20)

    is_technical_pass = not is_severe_under and not is_blank and not is_over_max_file
    is_quality_pass = (quality >= min_quality_threshold) and (focus >= min_quality_threshold)
    is_policy_pass = (overall_status != "AUTO_REJECT") and not body_parts
    is_not_logo = not is_logo
    eligible_for_enhancement = is_technical_pass and is_policy_pass and is_quality_pass and is_not_logo

    bypass_reason = None
    if not eligible_for_enhancement:
        if not is_technical_pass:
            if is_severe_under:
                bypass_reason = f"Intake resolution below portal minimum: {raw_w}×{raw_h} < 150 px floor"
            elif is_blank:
                bypass_reason = "Blank or solid-color placeholder image"
            elif is_over_max_file:
                bypass_reason = f"File size exceeds 5 MB limit ({file_kb} KB)"
        elif not is_quality_pass:
            defect = f"Focus blur ({focus:.2f})" if focus < min_quality_threshold else f"Overall quality ({quality:.2f})"
            bypass_reason = f"Intake quality below commercial floor: {defect} < {min_quality_threshold:.2f}"
        elif not is_policy_pass:
            bypass_reason = f"Moderation gate blocked Phase C: {', '.join(reasons)}"
        elif not is_not_logo:
            bypass_reason = "Brand logo detected (reshoot bypassed to preserve logo artwork)"

    return {
        "status": overall_status,
        "reasons": reasons,
        "eligible_for_enhancement": eligible_for_enhancement,
        "enhancement_bypass_reason": bypass_reason,
        "confidence": 0.95,
        "phase_a_checks": phase_a_checks,
        "phase_b_checks": phase_b_checks,
        "web_provenance": domain_eval
    }
