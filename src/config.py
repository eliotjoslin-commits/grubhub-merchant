"""Configuration and constants for the Grubhub Merchant Menu Image Platform.
Configured strictly for Gemini 3.0+ foundation models on Google Cloud Vertex AI,
featuring Gemini 3.8 Flash as the primary multimodal perception and audit engine.
"""

import os
from pathlib import Path

# Base Paths - Dynamic resolution for both local development and containerized Cloud Run
WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_ROOT", str(Path(__file__).parent.parent.resolve())))

# Load local .env file if present (gitignored)
_PLACEHOLDER_PROJECTS = {"your-gcp-project-id", "your-project-id", "changeme", ""}
_env_file = WORKSPACE_ROOT / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            _k_clean = _k.strip()
            _v_clean = _v.strip().strip("'\"")
            if _k_clean == "GOOGLE_CLOUD_PROJECT" and _v_clean in _PLACEHOLDER_PROJECTS:
                continue
            os.environ.setdefault(_k_clean, _v_clean)

_photos_cand = WORKSPACE_ROOT / "Sample-Photos" / "Sample-Photos"
if not _photos_cand.exists() and (WORKSPACE_ROOT / "Sample-Photos").exists():
    _photos_cand = WORKSPACE_ROOT / "Sample-Photos"
SAMPLE_PHOTOS_DIR = _photos_cand

OUTPUT_DIR = WORKSPACE_ROOT / "results"
ENHANCED_DIR = OUTPUT_DIR / "enhanced_images"
REPORT_FILE = OUTPUT_DIR / "benchmark_report.html"
DECISIONS_FILE = OUTPUT_DIR / "moderation_decisions.json"
CSV_REPORT_FILE = OUTPUT_DIR / "capability_matrix_results.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ENHANCED_DIR.mkdir(parents=True, exist_ok=True)


def _resolve_gcp_project() -> str:
    """Resolves the active Google Cloud Project ID from env vars or ADC without hardcoded secrets."""
    for env_key in ("GOOGLE_CLOUD_PROJECT", "GCP_PROJECT", "GCLOUD_PROJECT"):
        val = (os.getenv(env_key) or "").strip()
        if val and val not in _PLACEHOLDER_PROJECTS:
            return val
    try:
        import google.auth
        creds, default_proj = google.auth.default()
        if default_proj and default_proj not in _PLACEHOLDER_PROJECTS:
            return default_proj
        quota_proj = getattr(creds, "quota_project_id", None)
        if quota_proj and quota_proj not in _PLACEHOLDER_PROJECTS:
            return quota_proj
    except Exception:
        pass
    return "your-gcp-project-id"


# GCP & Gemini 3.0+ Model Configuration
GCP_PROJECT = _resolve_gcp_project()
GCP_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "global")

# Gemini 3.0+ Models
# Primary Multimodal Perception & Policy Moderation Engine
INSPECTION_MODEL = os.getenv("INSPECTION_MODEL", "gemini-3.8-flash")
# Automated Truth-in-Advertising & Anti-Hallucination Audit Engine
AUDITOR_MODEL = os.getenv("AUDITOR_MODEL", "gemini-3.8-flash")
# Frontier Complex Reasoning & Copyright Arbitration
PRO_REASONING_MODEL = os.getenv("PRO_REASONING_MODEL", "gemini-3.1-pro-preview")
# Commercial Studio Photoshoot Generation (Gemini Nano Banana 2.1 - GA October 6, 2026)
ENHANCEMENT_MODEL = os.getenv("ENHANCEMENT_MODEL", "gemini-nano-banana-2.1")
PRO_ENHANCEMENT_MODEL = os.getenv("PRO_ENHANCEMENT_MODEL", "gemini-3-pro-image")
# SOTA Imagen 3 Capability Model (Strict Food-Lock Inpainting & BGSWAP)
IMAGEN_CAPABILITY_MODEL = os.getenv("IMAGEN_CAPABILITY_MODEL", "imagen-3.0-capability-001")
DEFAULT_ENHANCEMENT_MODE = os.getenv("DEFAULT_ENHANCEMENT_MODE", "studio_reshoot")
ENABLE_SYNTHID_PROVENANCE = True
ENABLE_CROP_HINTS_SALIENCY = True

# Portal Image Specifications
MIN_PORTAL_DIMENSION = 200  # px
MAX_PORTAL_DIMENSION = 32768  # px
MAX_WORKING_DIMENSION = 1600  # px (Pre-flight normalization cap for multi-megapixel uploads)
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
TARGET_CANVAS_ASPECT = (4, 3)
TARGET_FOOD_RATIO = 0.55  # 55% food / 45% background

# SOP & Truth-in-Advertising Thresholds
SUPERIMPOSED_TEXT_CONFIDENCE_THRESHOLD = 0.80
WATERMARK_CONFIDENCE_THRESHOLD = 0.80
PROHIBITED_ITEM_CONFIDENCE_THRESHOLD = 0.70
MIN_QUALITY_AUTO_APPROVE = 0.75
MIN_QUALITY_AUTO_ENHANCE = 0.35
MIN_FOOD_FIDELITY_SSIM = 0.90
MAX_ALLOWED_HALLUCINATED_ITEMS = 0
MAX_TRUTH_IN_ADVERTISING_RISK = 0.25
