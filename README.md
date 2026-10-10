# Grubhub Merchant Menu Image Enhancement & Moderation Platform

Production-ready implementation and evaluation workbench built on Google Cloud Vertex AI and Gemini foundation models, configured to evaluate and enhance merchant menu photography across the 50 sample photos in `Sample-Photos/Sample-Photos/`.

---

## Architecture Overview

1. **Pre-flight Ingestion (`src/preflight.py`)**: 
   - Sniffs real image MIME types (detecting WebP, PNG disguised as JPEG) and corrects EXIF orientation.
   - Enforces portal minimums (minimum 200×200 px up to 32,768 px) and caps working resolution at 1,600 px (`MAX_WORKING_DIMENSION`) for consistent sub-second pre-flight processing.
   - Automatically upscales low-resolution merchant submissions (100–199 px) using high-quality Lanczos resampling and computes deterministic Laplacian variance blur and grayscale contrast checks (`A1`–`A5`).
2. **Multimodal Inspection & SOP Moderation (`src/moderator.py` & `src/sota_vision.py`)**:
   - Powered by **Gemini 3.8 Flash (`gemini-3.8-flash`)** on Vertex AI (`thinking_budget=0`) running concurrently with **Google Cloud Vision `web_detection`** reverse-image copyright/competitor verification (`B1`–`B12`).
   - Evaluates: Food validation, SafeSearch, body parts / chef hands on food (`B7`), prohibited items (CBD, vapes, tobacco, nitrous, weapons, lottery), alcohol detection, OCR for superimposed text and watermarks, and calibrated 4-axis visual quality scoring (`B8`).
   - Three-Tier SOP Decision Engine: `AUTO_APPROVE`, `FLAG_FOR_REVIEW` (quarantine for alcohol licensing or borderline quality `0.35–0.54`), and `AUTO_REJECT` (including unrecoverable quality `< 0.35`), with an interactive `force_enhancement` override option.
   - Generates taxonomy tags (cuisine, dietary markers), SEO alt-text, and appetizing item descriptions.
3. **Commercial Studio Photoshoot & Strict Food-Lock Enhancement (`src/enhancer.py`, `src/sota_vision.py`, `src/compositor.py`)**:
   - **Commercial Studio Reshoot (`studio_reshoot`)**: Powered by **Gemini Nano Banana 2.1 (`gemini-nano-banana-2.1`, GA Oct 6, 2026)** on Vertex AI, reconstructing studio tabletop lighting, natural plate geometry, and human/hand removal while preserving authentic dish ingredients.
   - **Strict Food-Lock Background Swap (`background_swap`)**: Powered by **Imagen 3 Capability (`imagen-3.0-capability-001`, `EDIT_MODE_BGSWAP`)** and mask-protected compositing (`src/compositor.py`), locking 100% of raw food pixels.
   - Embeds **Google DeepMind SynthID v2** digital watermarking and **C2PA Content Credentials**.
4. **7-Criteria Truth-in-Advertising Audit & Closed-Loop Self-Healing (`src/authenticity_auditor.py` & `src/evaluator.py`)**:
   - **Gemini 3.8 Flash (`gemini-3.8-flash`)** side-by-side auditor evaluates raw vs. enhanced assets across 7 anti-hallucination criteria (`PASS_AUTHENTIC` vs. `FLAG_OVER_ENHANCED`), automatically triggering a **Pass 2 Self-Healing Retry** when needed.
   - Computes deterministic **Masked SSIM** (Structural Similarity Index Measure) and **PSNR** strictly over the food region between the raw input and enhanced asset, plus Quality Score lift ($\Delta Q = Q_{\text{post}} - Q_{\text{pre}}$).
   - Exports machine-readable decisions, CSV capability matrix, and an interactive HTML before/after workbench (`results/benchmark_report.html`).

---

## Quickstart & Evaluation Commands

1. Configure your Google Cloud project in `.env` (or export `GOOGLE_CLOUD_PROJECT`):
```bash
cp .env.example .env
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
```

2. Create or use the Python virtual environment at `.venv/`:
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 1. Run Evaluation on Sample Photos
Process a test subset of photos:
```bash
.venv/bin/python -m src.batch_runner --limit 5
```

Process a specific image by name:
```bash
.venv/bin/python -m src.batch_runner --image Sandwich4.jpg
```

Process all 50 sample photos:
```bash
.venv/bin/python -m src.batch_runner --all
```

### 2. View Deliverables & Interactive Reports
After running the batch evaluator, the following deliverables are generated in `results/`:
- **`results/benchmark_report.html`**: Interactive HTML dashboard with side-by-side Before / After comparison cards, quality lift metrics, SSIM food fidelity scores, and filter buttons.
- **`results/moderation_decisions.json`**: Full machine-readable moderation decisions, confidence scores, bounding boxes, and generated descriptions.
- **`results/capability_matrix_results.csv`**: Tabular CSV matrix detailing every image's decision, quality delta, SSIM, dimensions, and latency.
- **`results/enhanced_images/`**: High-resolution enhanced studio photos.

### 3. Launch Local Interactive Workbench UI
Launch the local FastAPI workbench:
```bash
.venv/bin/uvicorn src.server:app --host 0.0.0.0 --port 8080
```
Open `http://localhost:8080/` in your browser to view the interactive dashboard.

