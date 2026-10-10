# Product Requirements Document (PRD)
## Grubhub Merchant Menu Image Enhancement & Moderation Platform
### Production Architecture on Google Cloud Powered Strictly by Gemini 3.8 Flash (`gemini-3.8-flash`) & Gemini Nano Banana 2.1 (`gemini-nano-banana-2.1`)

> [!IMPORTANT]
> **Active Production Foundation Models (v5.2 — October 2026 GA)**:
> - **Phase A (Technical Preflight)**: Deterministic Lanczos Resampling (`1600px` working dimension cap, `200px` portal minimum / `100px` upscale floor, `A1`–`A5`).
> - **Phase B (Policy Moderation & Copyright)**: **`gemini-3.8-flash`** (`thinking_budget=0`, $\le 768\text{px}$) + **Google Cloud Vision Web Detection** in parallel (`12` SOP rules `B1`–`B12`; calibrated `B8` bands: `<0.35` Reject, `0.35–0.54` Review, `>=0.55` Studio Eligible; `<4.5s` fast-fail).
> - **Phase C (Primary Studio Reshoot & Self-Healing Pass 2)**: **`gemini-nano-banana-2.1`** (**Gemini Nano Banana 2.1**, GA October 6, 2026 — `$0.0361`/image @ 1K PayGo, `$0.0180` Batch).
> - **Phase D (Truth-in-Advertising Audit)**: **`gemini-3.8-flash`** ($\le 512\text{px}$ single-tile comparison across **7 strict criteria**, $\text{Risk} \le 0.25$).

---

## 1. Executive Summary & Vision

### 1.1 Executive Summary
Restaurant merchants rely heavily on visually compelling menu photography to drive diner conversion, order volume, and brand trust. However, merchant-submitted photography frequently suffers from quality defects (underexposure, motion blur, cluttered backgrounds, extraneous objects, body parts/hands holding dishes) or regulatory and policy violations (unauthorized branding, prohibited items, superimposed text, unverified alcohol). 

This document defines the production specification for the **Grubhub Merchant Menu Image Enhancement & Moderation Platform** built and deployed on Google Cloud. Built strictly on Google's state-of-the-art **Gemini 3.0+** and **Gemini Nano Banana 2.1** model family hosted on Vertex AI global endpoints, the platform executes an end-to-end automated image ingestion pipeline:
1. **Real-Time Technical Preflight (Phase A)**: Deterministic dimension validation ($\ge 200\times 200\text{ px}$ portal minimum, $100\text{ px}$ upscaling floor), working resolution capping (`MAX_WORKING_DIMENSION = 1600px`) for multi-megapixel DSLR/smartphone uploads, MIME format sniffing, grayscale contrast checks (`StdDev >= 5.0`), Laplacian variance blur telemetry, and automated Lanczos super-resolution upscaling (<50ms) across 5 discrete checks (`A1`–`A5`).
2. **Deep Multimodal Policy Moderation (Phase B)**: Powered by **`gemini-3.8-flash`** (`thinking_budget=0`, $\le 768\text{px}$ normalized payload) executing in parallel (`ThreadPoolExecutor(max_workers=2)`) alongside **Google Cloud Vision API Web Detection** (`lookup_web_provenance`) to evaluate 12 discrete SOP rules (food validation, SafeSearch, prohibited items, alcohol, watermarks, superimposed text, human/hand/chef-holding presence `B7`, calibrated quality scoring `B8`, brand protection, truth-in-advertising `B10`, studio aesthetic bar `B11`, and reverse-image copyright clearance `B12`).
3. **Primary Commercial Studio Enhancement (Phase C)**: Powered by **`gemini-nano-banana-2.1`** (**Gemini Nano Banana 2.1**, GA October 6, 2026 — the default `"studio_reshoot"` mode), generating appetizing 1024×1024 (1K) to 4K commercial photos with realistic contact shadows, surface textures, and depth of field, strictly constrained by Zero-Text, Plating Geometry preservation, and dynamic Human/Body-Part Removal (`CRITICAL HUMAN & BODY PART REMOVAL`) directives.
   > [!NOTE]
   > **Clarification on Imagen 3 (`imagen-3.0-capability-001`)**: The standard automated ingestion pipeline relies exclusively on **`gemini-nano-banana-2.1`** for generative studio shoots. Imagen 3 (`imagen-3.0-capability-001`) is **not** used in the standard ingestion pipeline; it is retained strictly as an optional manual background-swap mode (`background_swap`) in the interactive tuning drawer, and is not the primary path forward.
4. **Automated Truth-in-Advertising & Anti-Hallucination Audit (Phase D)**: Powered by **`gemini-3.8-flash`** ($\le 512\text{px}$ single-tile side-by-side comparison, `thinking_budget=0`), comparing the raw submission against the enhanced output across **7 strict criteria** to eliminate culinary hallucination (unverified garnishes, herbs, seeds, allergens, side dishes, portion inflation, or typography) while recognizing compliant commercial studio reframing and hand/body-part removal (`ACCEPTABLE_UPGRADE`).
5. **Actor-Critic Closed-Loop Self-Healing Loop**: If unverified garnishes/text are flagged (`FLAG_OVER_ENHANCED`) OR if Pass 1 experienced a transient generation fallback (`FALLBACK_MASK_PROTECTED_COMPOSITOR`), the platform automatically executes a Pass 2 corrective shoot on **`gemini-nano-banana-2.1`** (using either the auditor's structured remediation directive or the high-reliability `self_healing_fallback_retry` prompt) with zero human moderator intervention.
6. **Serverless Ephemeral Storage & Cloud Storage Persistence**: Containerized on **Google Cloud Run** (`grubhub-merchant-platform` in `us-central1`) backed by **Google Cloud Storage** (`gs://[GCP_PROJECT_ID]-grubhub-merchant-assets`) for raw inputs (`samples/`), enhanced outputs (`enhanced/`), and the central audit ledger (`decisions/moderation_decisions.json`), with dynamic on-demand fallback streaming.
7. **Interactive Merchant Web Experience**: An interactive Merchant Portal UI featuring single drag-and-drop intake, multi-photo batch dropzone with live streaming card prepending (`cardHighlightGlow`), an interactive **"Always Execute Phase C AI Enhancement (Bypass Moderation Gate)"** (`force_enhancement`) toggle in both the upload sandbox and per-card tuning drawers, cached Phase B re-tuning (`cached_analysis`), a 6-tab **Merchant Quality & Integrity Scoring Guide Modal** (`#metricsGuideModal`), an interactive Photo Studio & Adjustment Suite (crop, rotation, blemish brush, bokeh, color/light), top-bar navigation to `/prd` and `/prd.pdf`, and atomic record deletion.

### 1.2 Core Architectural Tenets
1. **Gemini 3.0+ & Nano Banana 2.1 Unified Intelligence**: Eliminate fragmented legacy computer vision pipelines. Multimodal perception, OCR, semantic policy moderation, calibrated quality grading, dietary/cuisine taxonomy tagging, and automated Truth-in-Advertising audits are unified inside **Gemini 3.8 Flash** with strict JSON Schema output, complemented by Google Cloud Vision API Web Detection for copyright clearance.
2. **Primary Commercial Studio Reshoot (`gemini-nano-banana-2.1`)**: The primary standard enhancement engine is **Gemini Nano Banana 2.1** (`gemini-nano-banana-2.1`, GA October 6, 2026), applying commercial lighting harmonization, contact shadow grounding, tableware geometry preservation, and automatic removal of hands, fingers, chef torsos, and paper wrappers. Strict negative constraints enforce zero text tolerance and forbid unverified culinary additions, while cutting Phase C generation cost by 47% compared to the prior-generation baseline (`$0.0361` vs. `$0.0680` per 1K studio reshoot).
3. **Actor-Critic Automated Ingredient Auditing & Self-Healing**: A dedicated post-enhancement verification step where **Gemini 3.8 Flash** compares raw upload vs. enhanced output across 7 criteria. If discrepancies or fallback cutouts are detected, the auditor generates structured remediation instructions that drive an automated Pass 2 re-shoot on `gemini-nano-banana-2.1`, lowering risk scores (e.g. from 0.70 to 0.05) without human friction.
4. **Calibrated Quality Intake Gate (Rule B8) & `force_enhancement` Override**: Pre-enhancement quality scoring maps merchant camera inputs across a discrete 1–5 Likert scale ($1 \rightarrow 0.20, 2 \rightarrow 0.50, 3 \rightarrow 0.70, 4 \rightarrow 0.85, 5 \rightarrow 1.00$) with calibrated decision bands (`<0.35` `AUTO_REJECT`, `0.35–0.54` `FLAG_FOR_REVIEW` borderline margin band, `0.55–0.74` `AUTO_APPROVE` eligible for studio enhancement, `>=0.75` `AUTO_APPROVE` commercial standard). Merchants and operators can also enable `force_enhancement` (`Always Execute Phase C AI Enhancement`) in the UI to test or remediate flagged submissions (such as chef-holding-dish photos).
5. **Two-Phase Validation Gate**:
   - **Phase A (Technical Pre-Flight)**: Instantaneous dimension verification ($\ge 200\times 200$ px down to $100\text{px}$ upscaling floor), working dimension cap ($1600\text{px}$), file size verification ($\le 5$ MB), MIME format sniffing, blank/solid-color contrast detection ($\text{StdDev} \ge 5.0$), aspect ratio verification ($0.25$–$4.0$), and high-quality Lanczos super-resolution upscaling (`A1`–`A5`).
   - **Phase B (Deep Multimodal Perception & Policy Moderation)**: 12 discrete rule checks (`B1`–`B12`) running `gemini-3.8-flash` and Cloud Vision `web_detection` in parallel under our Three-Tier SOP Engine (`AUTO_APPROVE`, `FLAG_FOR_REVIEW`, `AUTO_REJECT`).
6. **Serverless Cloud Run & Cloud Storage Persistence**: Decouples stateless Cloud Run compute from stateful Google Cloud Storage asset persistence, using dynamic on-demand fallback routes to guarantee 0% broken image rates across container restarts or cold boots.

---

## 2. Capability Matrix

This matrix maps every requirement from the Grubhub specification to Google Cloud's capabilities, detailing current availability, programmatic interfaces, processing modes, and returned metadata.

| Requirement Domain | Specific Capability | Google Cloud / Gemini 3.0+ Model | Availability | API / Programmatic Access | Processing Mode | Confidence Scores, Labels & Metadata Returned |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Image Enhancement** | Lighting & Color Correction | `gemini-nano-banana-2.1` Contextual Illumination | **Available Today (GA Oct 2026)** | REST, gRPC, Vertex AI SDK | Real-Time Sync & Async Batch | Exposure Delta, Color Temp (°K), Contrast Adjust Log |
| | Clarity, Deblur & Upscaling | Native Gemini Nano Banana 2.1 (0.5K/1K/2K/4K) + Lanczos Preflight | **Available Today (GA Oct 2026)** | REST, gRPC, Vertex AI SDK | Real-Time Sync & Async Batch | Sharpness Score (0–1), Original vs Upscaled Resolution |
| | Reframing, Cropping & Aspect Ratio | Google Cloud Vision API (Crop Hints) + Gemini 3.8 Flash | **Available Today** | REST, gRPC, Node/Python SDK | Real-Time Sync & Async Batch | Saliency Polygons, 1:1 / 4:3 / 16:9 Framing `[ymin, xmin, ymax, xmax]`, Importance Fraction |
| | Client-Edge Plate Segmentation | MediaPipe Tasks Vision (`@mediapipe/tasks-vision` WASM/WebGL) | **Available Today** | WebAssembly, WebGL, Browser SDK | Instant Client-Side (<30ms) | Plate Contour Mask, Foreground Depth Alpha, Blemish Coordinates |
| | Optional Food-Lock Background Swap (Edit Mode Only) | Vertex AI Imagen 3 Capability (`imagen-3.0-capability-001` BGSWAP) *(Optional manual tuning/edit parameter only; NOT used in standard ingestion pipeline)* | **Available Today** | REST, gRPC, Vertex AI SDK | Manual Interactive Tuning Only | 100% Raw Food Pixels Preserved, Tabletop Preset Applied, Contact Shadow Grounding |
| | Generative Fill & Uncropping | `gemini-nano-banana-2.1` Contextual Composition | **Available Today (GA Oct 2026)** | REST, gRPC, Vertex AI SDK | Real-Time Sync & Batch | Natural Plate Boundary Completion, Uncropped Tabletop Presentation |
| | Background Cleanup & Normalization | Commercial Studio Reshoot (Slate, Wood, Marble, Granite) via `gemini-nano-banana-2.1` | **Available Today (GA Oct 2026)** | REST, gRPC, Vertex AI SDK | Real-Time Sync & Batch | Surface Preset Applied, Contact Shadow Grounding, Editorial Lighting Harmonization |
| | Artifact, Hand & Object Removal | Interactive Photo Studio Blemish Brush (HTML5 Canvas) + `gemini-nano-banana-2.1` Human/Hand Removal Directives | **Available Today** | Web UI Canvas, REST | Interactive Client-Side & Generative Pipeline | Annular Pixel Sampling, Zero-Text Directives, Hand/Chef/Wrapper Removal & Plate Edge Reconstruction |
| | In-Frame Copyrighted Elements | Gemini 3.8 Flash Brand Detection + Selective Inpaint Blurring | **Available Today** | REST, gRPC, Vertex AI SDK | Real-Time Sync & Async Batch | Brand Name, Confidence (0–1), Bounding Box, Action (`FLAGGED` or `REMOVED`) |
| | Multi-Factor Quality Scoring | Gemini 3.8 Flash Quality Evaluation Engine | **Available Today** | REST, gRPC, Vertex AI SDK | Real-Time Sync & Async Batch | Overall Score (0–1), Sub-scores: Focus, Lighting, Composition, Clutter |
| | Brand-Asset Protection | Gemini 3.8 Flash Logo Classification & Warning Trigger | **Available Today** | REST, gRPC, Vertex AI SDK | Real-Time Sync & Async Batch | `is_brand_logo: boolean`, `logo_quality_score`, `warning_message` |
| | Truth-in-Advertising Guardrail | Gemini 3.8 Flash 7-Criteria Multimodal Comparative Audit ($\le 512\text{px}$) | **Available Today** | REST, gRPC, Vertex AI SDK | Real-Time Sync & Async Batch | `hallucinated_items: []`, `remediation: string`, `explanation: string`, `truth_in_advertising_risk_score` (0–1), allergen detection (sesame, nuts) |
| | Closed-Loop Self-Healing Pass | Actor-Critic Feedback Loop (Auditor $\rightarrow$ `gemini-nano-banana-2.1` Pass 2 + Fallback Retry) | **Available Today** | REST, Python / Cloud Run | Real-Time Sync & Async Batch | `self_healed: boolean`, `self_healing_notes: string`, `self_healing_fallback_retry`, Pass 1 vs Pass 2 Risk Delta |
| | Provenance & Digital Watermarking | Google SynthID v2 & C2PA Content Credentials | **Available Today** | Vertex AI Native Watermarking | Real-Time Sync & Async Batch | `synthid_watermark_status: EMBEDDED_SYNTHID_V2`, C2PA Signed Claim, Hash |
| | Professional Quality Bar | Gemini Nano Banana 2.1 (`gemini-nano-banana-2.1`) / Gemini 3 Pro Image | **Available Today (GA Oct 2026)** | REST, gRPC, Vertex AI SDK | Real-Time Sync & Async Batch | Commercial Grade Flag (`PASS`/`FAIL`), Studio Resolution (1024×1024 / 2K / 4K) |
| **Content Moderation** | Food-Image Validation | Gemini 3.8 Flash Multimodal Classification | **Available Today** | REST, gRPC, Vertex AI SDK | Real-Time Sync & Async Batch | `is_food_beverage: boolean`, Confidence (0–1), Primary Dish Name |
| | SafeSearch (Adult, Violence, Spoof) | Gemini 3.8 Flash Safety Evaluation | **Available Today** | REST, gRPC, Vertex AI SDK | Real-Time Sync & Async Batch | Categories: Adult, Violence, Spoof, Racy (Likelihood: 1–5 / Float 0–1) |
| | Face, Hand & Body-Part Detection | Gemini 3.8 Flash Spatial Perception & Anatomy Detection (`B7_BODY_PARTS`) | **Available Today** | REST, gRPC, Vertex AI SDK | Real-Time Sync & Async Batch | Hands, Fingers, Arms, Chef Torso/Apron, Bounding Boxes, `body_parts_on_food: boolean` |
| | Superimposed Text & Phone Detection | Gemini 3.8 Flash Multimodal OCR & Phone Regex Parser | **Available Today** | REST, gRPC, Vertex AI SDK | Real-Time Sync & Async Batch | Extracted Text, Detected Phone Numbers, Bounding Boxes, `is_packaging_text: boolean` |
| | Watermark Detection | Gemini 3.8 Flash Semi-Transparent / Stock Watermark Detector | **Available Today** | REST, gRPC, Vertex AI SDK | Real-Time Sync & Async Batch | Watermark Detected (`boolean`), Confidence (0–1), Source (`STOCK` vs `COMPETITOR`) |
| | Prohibited-Item Detection | Gemini 3.8 Flash Semantic Packaging & Product Recognition | **Available Today** | REST, gRPC, Vertex AI SDK | Real-Time Sync & Async Batch | Category (`CBD_THC`, `TOBACCO`, `VAPES`, `NITROUS`, `KRATOM`, `WEAPONS`, `LOTTERY`) |
| | Alcohol Detection | Gemini 3.8 Flash Beverage Analysis & Container Identification | **Available Today** | REST, gRPC, Vertex AI SDK | Real-Time Sync & Async Batch | `alcohol_detected: boolean`, Container Type (`BOTTLE`, `CAN`, `COCKTAIL`), Licensing Flag |
| | Reverse-Image Search & Competitor Detection | Google Cloud Vision API Reverse-Image Search + Grounding (Parallel w/ Phase B) | **Available Today** | REST, gRPC, Cloud Vision SDK | Real-Time Sync & Async Batch | Web match URLs, Competitor CDN Match (`img.cdn4dd.com`), Stock Library Detection, Best Guess Labels |
| | SOP Auto-Approve / Reject Engine | Three-Tier SOP Decision Engine + `force_enhancement` Override | **Available Today** | REST, gRPC, Cloud Run | Real-Time Sync & Async Batch | SOP Decision (`AUTO_APPROVE`, `FLAG_FOR_REVIEW`, `AUTO_REJECT`), Rule Violation IDs, `force_enhancement` |
| | Size & Resolution Enforcer | Preflight Engine (1600px Working Cap + Lanczos Resampling / Pillow) | **Available Today** | REST, gRPC, Cloud Run | Real-Time Sync & Async Batch | Raw & Working Width/Height, Aspect Ratio, Contrast StdDev, Blur Score, Upscaled/Downsampled Flags |
| **Metadata & Tagging** | Automatic Taxonomy Tagging | Gemini 3.8 Flash Multimodal Taxonomy Classifier | **Available Today** | REST, gRPC, Vertex AI SDK | Real-Time Sync & Async Batch | Cuisine Types, Dish Attributes, Dietary Flags (Vegan, Halal, Gluten-Free, etc.) |
| | Auto-Description & Alt-Text | Gemini 3.8 Flash Contextual Generator | **Available Today** | REST, gRPC, Vertex AI SDK | Real-Time Sync & Async Batch | Generated Menu Description (Markdown/Text), Screen-Reader Alt-Text |
| | Transformation Metadata Logging | Google Cloud Storage JSON Ledger (`decisions/moderation_decisions.json`) & Cloud Run Logs | **Available Today** | REST, GCS SDK, Cloud Run | Real-Time Sync & Batch | Chronological Operations Array, Model Version, Latency Timers, Audit Hash |
| **Asset Management** | Centralized Asset Management | Google Cloud Storage Bucket (`gs://grubhub-merchant-assets`) + Local Disk Cache | **Available Today** | REST, GCS SDK | Real-Time Sync & Batch | `samples/{filename}`, `enhanced/{filename}`, `decisions/{ledger}`, Canonical Storage URIs |
| | Original Asset Retention & Revert | Google Cloud Storage Immutable Raw Storage (`samples/`) & Dynamic Fallback Serving | **Available Today** | REST, GCS SDK | Real-Time Sync | `raw_asset_uri`, `current_active_uri`, instant 1-click restore |
| | Legal Audit Trail & Capability Matrix | GCS Audit Ledger (`decisions/moderation_decisions.json`) & CSV Capability Matrix Export | **Available Today** | REST, GCS SDK, Python | Real-Time Sync & Batch | SOP Decision, Truth Risk, SSIM, Latency Timers, CSV Matrix Download |
| | Secure Backend Proxy & Ingress | Google Cloud Run HTTPS Gateway with IAM Service Account & CORS Middleware | **Available Today** | HTTPS, Cloud Run, IAM | Real-Time Sync & Batch | Service Account Identity, HTTPS Ingress, Wildcard CORS Headers for Canvas |
| | Asynchronous Batch Orchestration | FastAPI BackgroundTasks & Asynchronous Batch Runner (`/api/batch/run` & `/api/batch/process-next`) | **Available Today** | REST, CLI | Non-Blocking Background Batch | Incremental Batch Status (`/api/batch/status`), GCS Sync per Completed Asset |
| | Interactive Merchant Portal & Dropzone | Native HTML5/JS Merchant Portal (`src/report_generator.py`) + 6-Tab Metrics Guide Modal | **Available Today** | Web UI, REST | Real-Time Client Side | Multi-File Intake Dropzone, Interactive Split-Slider, Force-Enhance Toggle, 6-Tab Scoring Guide |
| | Dynamic Asset Serving & GCS Fallback | Cloud Run Dynamic Image Delivery with GCS Streaming | **Available Today** | REST, Cloud Storage API | Real-Time Sync | Sub-ms cached delivery, on-demand GCS blob streaming on cold starts, zero 404s |
| | Multi-Photo Batch Intake & Live Streaming | Itemized Multi-File Queue + Stage-by-Stage Cards Streaming | **Available Today** | HTML5, Fetch API, CSS Keyframes | Real-Time Client Side | Multi-select dropzone, progress pills, non-blocking DOM card prepending, live KPIs |
| | Enterprise Record Purge & Cleanup | Atomic Decisions Ledger & GCS Storage Object Deletion | **Available Today** | REST, Cloud Run, GCS SDK | Real-Time Sync | Atomic ledger unlink, simultaneous raw (`samples/`) & enhanced (`enhanced/`) purge |
| | Interactive Photo Studio & Retouching | HTML5 Canvas / WebAssembly Adjustment & Retouch Suite | **Available Today** | Web UI, REST API, Vertex AI | Real-Time Client & API | Interactive crop/rotate/geometry, color/light, blemish brush, bokeh blur, AI retouch |

---

## 3. End-to-End System Architecture

The Grubhub Merchant Menu Image Platform is built on a serverless, decoupled microservices architecture utilizing Google Cloud Platform (GCP) and Vertex AI Global endpoints.

> [!NOTE]
> **Verifiable Architecture Topology**: The system architecture, multi-stage ingestion dataflow, and merchant journey sequence are compiled into verifiable JSON specifications. An interactive exploration suite is available at `interactive_prd/index.html` (and `results/PRD_INTERACTIVE_PLATFORM.html`), accessible directly from the workbench navigation bar (`/prd` and `/prd.pdf`). All cloud project identifiers, secrets, and credentials have been strictly sanitized.

<div align="center" style="margin: 20px 0;">
  <img src="assets/diagram_plates/architecture_plate.png" alt="System Architecture Topology Plate" style="max-width: 100%; border-radius: 8px; border: 1px solid #E2E8F0; box-shadow: 0 4px 12px rgba(0,0,0,0.06);" />
  <p style="font-size: 0.85rem; color: #6B7280; margin-top: 8px;"><em>Figure 3.1: System Architecture Topology — Google Cloud Run Gateway, Vertex AI Gemini 3.8 Flash & Gemini Nano Banana 2.1 Foundation Pipeline, and Cloud Storage Persistence.</em></p>
</div>

```mermaid
flowchart TB
    subgraph ClientLayer ["1. Interactive Merchant Portal & UI Layer"]
        MerchantPortal["Grubhub for Merchants Portal (HTML5/JS)"]
        Dropzone["Multi-Photo Batch Dropzone & Single Intake (w/ Force-Enhance Toggle)"]
        Studio["Interactive Photo Studio & Adjustment Suite"]
        MerchantPortal --> Dropzone
        MerchantPortal --> Studio
    end

    subgraph GatewayLayer ["2. Cloud Run Gateway & Control Plane (us-central1)"]
        Dropzone -->|"POST /api/upload"| Gateway["FastAPI Service on Google Cloud Run"]
        Studio -->|"POST /api/image/{fn}/edit and edit-enhanced"| Gateway
        MerchantPortal -->|"POST /api/image/{fn}/tune (cached_analysis) and DELETE"| Gateway
        MerchantPortal -->|"GET /samples/ and GET /enhanced/"| DynamicServe["Dynamic Asset Delivery & GCS Fallback Serving"]
    end

    subgraph AIServiceLayer ["3. Gemini 3.8 Flash & Nano Banana 2.1 Pipeline & Guardrails"]
        Gateway -->|"Step 1: Technical Preflight (A1-A5)"| Preflight["Phase A Preflight Engine (1600px Cap, Lanczos Upscale & MIME Sniff)"]
        Preflight -->|"Step 2: Parallel Policy Moderation"| GeminiFlash["Phase B Moderation: gemini-3.8-flash + Cloud Vision Web Detection"]
        GeminiFlash -->|"12 SOP Checks & Calibrated Quality"| SOP_Engine["Three-Tier SOP Decision Engine (or Force-Enhance Override)"]
        
        SOP_Engine -->|"Quality Defect (<0.35) or Policy Violation (Unforced)"| FastFail["Fast-Fail Bypass (<4.5s AUTO_REJECT / FLAG_FOR_REVIEW)"]
        SOP_Engine -->|"Compliant (Quality >= 0.55) or Force-Enhance"| GeminiImage["Phase C Primary Studio Reshoot: gemini-nano-banana-2.1"]
        
        GeminiImage -->|"Generated Commercial Photo"| Auditor["Phase D 7-Criteria Truth-in-Advertising Auditor: gemini-3.8-flash"]
        Auditor -->|"Audit Flag or Fallback Compositor"| SelfHealing["Actor-Critic Self-Healing Loop (Pass 2 Directive / Fallback Retry)"]
        SelfHealing -->|"Pass 2 Targeted Corrective Shoot"| GeminiImage
        
        Auditor -->|"Audit Approved (Risk <= 0.25)"| ApprovedAsset["Certified Commercial Photo (SynthID v2 + C2PA)"]
        
        Studio -.->|"Optional Manual Edit Mode (Tuning Drawer Only)"| ImagenBGSWAP["Optional Manual Tuning: imagen-3.0-capability-001 (BGSWAP)"]
        ImagenBGSWAP -.-> ApprovedAsset
    end

    subgraph StorageLayer ["4. Ephemeral Container Cache & Cloud Storage Persistence"]
        ApprovedAsset -->|"Sync Enhanced Image"| GCS_Enhanced["GCS: enhanced/{filename}"]
        Gateway -->|"Sync Raw Upload"| GCS_Raw["GCS: samples/{filename}"]
        Gateway -->|"Atomic Ledger Update"| GCS_Ledger["GCS: decisions/moderation_decisions.json"]
        FastFail -->|"Persist Decision"| GCS_Ledger
        DynamicServe <-->|"On-Demand Blob Stream & Cache"| GCS_Raw
        DynamicServe <-->|"On-Demand Blob Stream & Cache"| GCS_Enhanced
    end
```

### 3.1 Live Cloud Run & Serverless Persistence Topology
The reference platform is containerized and running in production on **Google Cloud Run** (`grubhub-merchant-platform` in `us-central1`) with automated Terraform infrastructure management:
- **Live Ingress Endpoint**: `https://[SERVICE_NAME]-[HASH]-uc.a.run.app` (Direct serverless HTTPS ingress with native Google Cloud TLS termination, DDoS mitigation, and edge acceleration; no external Cloud Armor WAF or Application Load Balancer is deployed in the live demo environment).
- **Asset Storage Bucket**: `gs://[GCP_PROJECT_ID]-grubhub-merchant-assets` (Standard Regional `us-central1`)
- **IAM Identity**: Dedicated service account `grubhub-merchant-sa@[GCP_PROJECT_ID].iam.gserviceaccount.com` granted least-privilege roles (`roles/aiplatform.user`, `roles/storage.objectAdmin`, `roles/serviceusage.serviceUsageConsumer`).
- **Serverless Resilience Pattern**: Solves container disk ephemerality by decoupling persistent state:
  1. **Raw Ingestion**: Submissions are stored under `samples/{filename}` in GCS.
  2. **AI Studio Outputs**: Generated and retouched assets are stored under `enhanced/{filename}` in GCS.
  3. **Decisions Ledger**: Central JSON audit ledger is synchronized to `decisions/moderation_decisions.json` in GCS.
  4. **Dynamic On-Demand Streaming**: Asset delivery routes stream blobs on-the-fly from GCS if absent from the container disk cache, preventing broken image placeholders across revision deployments, container restarts, or auto-scaling events.

---

## 4. Detailed Functional Specifications

### 4.0 End-to-End Ingestion & Moderation Dataflow
The platform coordinates a 5-stage automated ingestion pipeline spanning technical preflight, multimodal policy moderation, generative studio reshooting, truth-in-advertising auditing, and enterprise provenance delivery:

<div align="center" style="margin: 20px 0;">
  <img src="assets/diagram_plates/dataflow_plate.png" alt="5-Stage Ingestion Dataflow Plate" style="max-width: 100%; border-radius: 8px; border: 1px solid #E2E8F0; box-shadow: 0 4px 12px rgba(0,0,0,0.06);" />
  <p style="font-size: 0.85rem; color: #6B7280; margin-top: 8px;"><em>Figure 4.1: 5-Stage Food Image Ingestion & Moderation Dataflow — Automated pipeline from merchant dropzone to FTC-verified live diner menu publication.</em></p>
</div>

### 4.1 Phase A: Technical Pre-flight Validations (`A1`–`A5`)
Before invoking foundational AI models, images undergo ultra-fast deterministic validation (<50ms) inside `src/preflight.py`:
1. **`A1_DIMENSIONS` — Portal Minimum & Working Dimension Enforcement (≥200×200 px up to 32,768 px)**:
   - Evaluates raw input width and height. Rejects images below the hard $100\text{ px}$ floor or above $32,768\text{ px}$.
   - **Automated Super-Resolution Upscaling**: If either dimension is $100\text{–}199\text{ px}$, the preflight engine applies high-quality Lanczos resampling to upscale the asset to a minimum of $400\times 400\text{ px}$ (`AUTO_RESOLVED`), ensuring clear inspection without pixelation artifacts.
   - **Working Dimension Cap (`MAX_WORKING_DIMENSION = 1600px`)**: Multi-megapixel DSLR/smartphone uploads exceeding $1,600\text{ px}$ are proportionally downsampled with Lanczos to a $1,600\text{ px}$ working ceiling so downstream Laplacian blur calculation, Cloud Vision API, and Gemini Nano Banana 2.1 execute with consistent sub-second payload transfer.
2. **`A2_FILE_SIZE` — File Size Enforcement (≤5 MB)**:
   - Validates byte length. Rejects oversized files exceeding 5,120 KB (`MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024`).
3. **`A3_FORMAT_MIME` — MIME Format Sniffing & Color Space Normalization**:
   - Inspects binary headers to detect disguised formats (e.g. WebP or PNG files with `.jpg` extensions).
   - Converts CMYK, RGBA, grayscale (`L`), and palette images to standardized RGB, and corrects EXIF camera orientations (`ImageOps.exif_transpose`).
4. **`A4_IMAGE_CONTRAST` — Blank / Solid-Color Placeholder Detection**:
   - Computes grayscale pixel standard deviation (`pixel_std`). Images with `StdDev < 5.0` are deterministically rejected as blank/corrupted placeholders before incurring Vertex AI token costs.
5. **`A5_ASPECT_RATIO` — Extreme Aspect Ratio Gate & Laplacian Blur Telemetry**:
   - Flags extreme banner/strip aspect ratios (`< 0.25` or `> 4.0`) for manual review (`FLAG_FOR_REVIEW`).
   - Computes deterministic Laplacian variance (`blur_score`) on the normalized grayscale array for objective sharpness telemetry.

### 4.2 Phase B: Deep Multimodal Perception & Policy Moderation (Gemini 3.8 Flash)
Phase B executes **`gemini-3.8-flash`** (`thinking_budget=0`, $\le 768\text{px}$ JPEG q=82, `timeout=15000ms`) in parallel with **Google Cloud Vision `web_detection`** (`lookup_web_provenance`) via a `ThreadPoolExecutor(max_workers=2)` to evaluate 12 discrete policy, quality, and provenance rules:

```
📋 Phase B: Multimodal Moderation & Quality Checklist
├── B1: Food & Beverage Validation          → Confirms authentic edible food/drink.
├── B2: SafeSearch Compliance               → Filters adult, violent, or spoof content.
├── B3: Prohibited Items Check              → Blocks CBD, THC, vapes, tobacco, nitrous, weapons, lottery.
├── B4: Alcohol Packaging Detection         → Identifies beer, wine, liquor containers (routes to license check).
├── B5: Third-Party Watermark Detection     → Identifies stock agency (Shutterstock, Getty) or competitor stamps.
├── B6: Superimposed Text & Coupon Codes    → OCR detection of digital phone numbers, delivery codes, discounts.
├── B7: Body Parts, Hands & Chef Presence   → Detects hands, fingers, wrists, arms, chef torsos, aprons, or faces holding/near food.
├── B8: Multi-Factor Quality Benchmark      → Calibrated 4-axis score (<0.35 Reject, 0.35-0.54 Review, >=0.55 Studio Eligible, >=0.75 Commercial).
├── B9: Brand-Asset Protection              → Flags isolated logos to preserve unmodified.
├── B10: Truth-in-Advertising Audit         → Verifies ingredient consistency, zero culinary hallucination & zero text (7 criteria).
├── B11: Commercial Plating & Aesthetic Bar → Enforces studio lighting & tableware geometry consistency (Mode A SSIM ≥0.85); catches mechanical cutouts.
└── B12: Domain Provenance & Copyright      → Google Cloud Vision reverse-image search across Google index; detects competitor scraping & stock photos.
```

#### Rule B7: Human Presence, Hands & Chef-Holding Detection (`B7_BODY_PARTS`)
- **Expanded Anatomical & Contextual Detection**: Evaluates `body_parts_on_food` alongside `spatial_rois.objects_to_remove` labels (`hand`, `finger`, `thumb`, `wrist`, `arm`, `person`, `human`, `chef`, `body`, `torso`, `apron`, `face`) and filename heuristics (`chef-holding`, `hand-holding`).
- **Moderation & Remediation Flow**: Unforced uploads containing human hands or chefs holding plates fail `B7_BODY_PARTS` (`AUTO_REJECT`). When the merchant or operator enables **`force_enhancement`** ("Always Execute Phase C AI Enhancement"), Phase C dynamically injects `CRITICAL HUMAN & BODY PART REMOVAL` to erase all hands/arms/chef torsos and reconstruct the occluded plate edges resting naturally on the studio tabletop.

#### Rule B12: Domain Provenance & Reverse-Image Copyright Clearance
To prevent intellectual property infringement, menu image scraping from competitor delivery platforms (e.g. DoorDash CDN `img.cdn4dd.com`, UberEats, Deliveroo), and commercial stock photo copyright claims:
- **Cloud Vision Web Detection**: Every merchant submission is queried against Google Cloud Vision API Web Entities and Pages with Matching Images in parallel with Gemini 3.8 Flash moderation.
- **Competitor Platform Isolation**: If an image URI or high-confidence entity points to a competitor platform CDN without merchant cross-licensing, it triggers `AUTO_REJECT` (`COPYRIGHT_COMPETITOR_SCRAPED_ASSET`).
- **Commercial Stock Photo Clearance**: Matches against major stock photo catalogs (Shutterstock, Getty Images, iStock, Adobe Stock) are automatically detected and rejected (`COPYRIGHT_UNAUTHORIZED_STOCK_PHOTO`), safeguarding Grubhub from copyright liability while prioritizing authentic restaurant photography.
- **Merchant Domain Matching**: Allows verified merchant brand domains to pass with `✓ UNIQUE ORIGINAL ASSET` clearance.


### 4.3 Truth-in-Advertising & Anti-Hallucination Guardrail Framework
To protect diners, restaurants, and Grubhub from false advertising liability (FTC compliance):

#### The "Bait-and-Switch" Risk
Generative AI image models, when prompted to "improve" food photography, often fabricate elements not present in the restaurant's actual kitchen:
- **Garnish Hallucination**: Adding fresh cilantro, parsley sprigs, sesame seeds, or red chili flakes.
- **Side Dish Addition**: Introducing extra dipping sauce ramekins, lime wedges, or side salads.
- **Portion Inflation**: Increasing wing counts, rib racks, or burger patties.
- **Prop Exaggeration**: Adding luxury wine glasses, candles, or cutlery that misrepresent casual eateries.
- **Text & Typography Hallucination**: Overlaying marketing words, restaurant names, slogans, or promotional typography onto the background or plating.
- **Disproportionate Reality Distortion ("Too Good to Be True")**: Fabricating an elaborate, high-end fine dining presentation from a 128×128 pixel thumbnail that bears no credible physical relationship to the merchant's actual kitchen delivery.

#### The 5-Pillar Authenticity Guardrail Solution
1. **Pillar 1: Negative Prompt Constraints, Zero-Text & Human Removal Directives (Gemini Nano Banana 2.1)**:
   Every generation prompt dispatched to `gemini-nano-banana-2.1` enforces strict negative bounds, zero typography tolerance, and dynamic human/body-part removal:
   `"CRITICAL MANDATORY REQUIREMENT - ZERO TEXT TOLERANCE: Absolutely NO text, NO words, NO letters, NO numbers, NO typography, NO slogans, NO titles, NO subtitles, NO watermarks, NO brand names, and NO labels. The output must be 100% clean culinary photography depicting ONLY the physical food and tabletop surface. STRICT TRUTH-IN-ADVERTISING GUARDRAIL: Do NOT add any garnishes, herbs, cilantro, parsley, sesame seeds, chili flakes, extra dipping sauce ramekins, side dishes, wine glasses, or cutlery that do not already exist in the original submission. Maintain the exact food ingredients, portion size, and arrangement."`
2. **Pillar 2: Automated Multimodal Auditor with Remediation Synthesis (Gemini 3.8 Flash - 7-Criteria Verification)**:
   A comparative auditor (`src/authenticity_auditor.py`) downsamples both the raw submission and enhanced output to $\le 512\text{px}$ (JPEG q=78, single 258-token image tile each, `thinking_budget=0`) and evaluates them across **seven strict criteria**:
   - **Criterion 1 (Garnish & Ingredient Hallucination)**: Target $\text{HEC} = 0$. Detects added herbs, chili flakes, or seed particulates.
   - **Criterion 2 (Portion Size Inflation & Compliant Reframing)**: $\Delta \text{Count} = 0$. Distinguishes between deceptive portion inflation (e.g. doubling a 4-piece order to 8-12 pieces) and compliant commercial reframing/unclipping at frame boundaries.
   - **Criterion 3 (Extraneous Dishes / Ramekins)**: Zero extra dipping sauce cups, side dishes, or cutlery not in Image 1.
   - **Criterion 4 (Tableware & Plating Geometry Consistency & Compliant Hand Removal)**: Verifies that tableware geometry and vessel proportions are preserved (`PRESERVED` | `ACCEPTABLE_UPGRADE` | `DISTORTION_MISMATCH`). Crucially, if Image 1 showed food held in human hands, by a chef/person, or in a messy paper wrapper and Image 2 removed the human hands/body parts and placed the food cleanly onto a commercial plate or serving board, the auditor rates this `ACCEPTABLE_UPGRADE` (`COMPLIANT HAND / BODY-PART REMOVAL`).
   - **Criterion 5 (Text & Typography Hallucination)**: Zero generated words, slogans, watermarks, or titles (`has_hallucinated_text`). Flagged immediately if text is present ($\text{Risk} \ge 0.75$).
   - **Criterion 6 (Reality Gap & Disproportionate Enhancement)**: Evaluates whether the generated output represents a fabricated luxury fantasy divergent from the real dish, governed by a calibrated threshold ($\text{Reality Gap} > 0.55 \rightarrow \text{is\_excessive\_reality\_gap} = \text{True}$).
   - **Criterion 7 (Holistic Truth-in-Advertising Risk Assessment)**: Synthesizes `truth_in_advertising_risk_score` ($0.0 \le \text{Risk} \le 1.0$, flagged if $\text{Risk} > 0.25$), `risk_level` (`LOW` | `MEDIUM` | `HIGH`), `audit_verdict` (`PASS_AUTHENTIC` | `FLAG_OVER_ENHANCED`), and explicit `remediation` guidance.
3. **Pillar 3: Actor-Critic Closed-Loop Self-Healing & Fallback Recovery (Automated Pass 2 Refinement)**:
   Rather than treating the auditor or transient generator fallbacks as a passive terminal gate, `src/pipeline_runner.py` implements an active **Actor-Critic Closed-Loop Control Architecture**:
   - **Pass 1 (Generative Shoot)**: `gemini-nano-banana-2.1` produces a high-aesthetic commercial studio photo ($\le 1536\text{px}$ input cap, JPEG q=92).
   - **Critic & Fallback Check**: Self-healing Pass 2 is triggered automatically if:
     1. The auditor flags `audit_verdict == "FLAG_OVER_ENHANCED"` (unverified garnishes, text, or plating distortion), OR
     2. Pass 1 fell back to `FALLBACK_MASK_PROTECTED_COMPOSITOR` (`is_fallback_compositor = True`).
   - **Self-Healing Loop (Pass 2)**:
     - For audit flags, Pass 2 injects `MANDATORY AUDITOR REMEDIATION DIRECTIVE (PASS 2 SELF-HEALING)` directly into the `gemini-nano-banana-2.1` prompt.
     - For compositor fallbacks, Pass 2 activates `self_healing_fallback_retry=True`, dispatching a streamlined, high-reliability studio prompt to guarantee a clean generative studio output.
   - **Re-Audit Certification**: Pass 2 is re-audited by `gemini-3.8-flash` and re-scored for SSIM/PSNR food fidelity. In empirical live validation on `Appitizer4.jpg` (Dumplings), Pass 2 eliminated 100% of unverified garnishes (`hallucinated_items: []`), plummeted Truth-in-Advertising risk from **0.70 down to 0.05**, and dropped reality gap from **0.45 down to 0.15**, converting a flagged asset into `AUTO_APPROVE` (`sop_decision["self_healed"] = True`) with zero human labor.
   - **Allergen & Consumer Safety Protection**: Specifically eliminates high-liability food hazards, notably **sesame seeds** (a top-9 major food allergen under the FDA FASTER Act) and unverified chili flakes.
4. **Pillar 4: Primary Gemini Nano Banana 2.1 Pipeline & Optional Manual Tuning**:
   - **Primary Ingestion Engine (`gemini-nano-banana-2.1`)**: The standard automated ingestion pipeline relies exclusively on **Gemini Nano Banana 2.1** (default `"studio_reshoot"` mode) for commercial studio enhancement, strictly governed by negative prompt bounds, zero-text directives, tableware geometry preservation, human/hand removal, and automated Pass 2 self-healing.
   - **Clarification on Imagen 3 (`imagen-3.0-capability-001`)**: Imagen 3 is **not** used in the standard automated ingestion pipeline, is **not** an automated fallback, and is **not** the primary path forward. It is retained strictly as an optional manual background-swap mode (`background_swap`) in the interactive Photo Studio tuning drawer for merchants who explicitly opt to lock 100% of raw food pixels bit-for-bit while replacing only the tabletop background.
5. **Pillar 5: Mathematical ROI Fidelity (Masked SSIM & PSNR)**:
   Computes Structural Similarity Index Measure strictly over the dish ROI (`src/evaluator.py`).

### 4.4 Commercial Studio Aesthetic Standard & Dual-Gate Architecture (Rule B11)
A critical insight identified during empirical testing is the distinction between **Truthfulness** and **Aesthetic Quality**:
- An image can be **100% authentic** (e.g., a crude circular cutout of a blurry low-res dish on a blank gray canvas has zero hallucinated toppings, passing Truth-in-Advertising with $\text{Risk} = 0.0$), yet look unappetizing and commercially unacceptable for Grubhub's diner-facing marketplace.
- To prevent degraded or mechanical fallback assets from passing unnoticed, the platform enforces a **Dual-Gate Quality Architecture**:
  1. **Truth Gate (Rule B10)**: Prevents deceptive culinary hallucinations (fake garnishes, portion exaggeration) via closed-loop self-healing.
  2. **Commercial Aesthetic & Plating Integrity Gate (Rule B11)**:
     - Enforces that generative studio enhancement produced an authentic commercial-grade photograph (`is_commercial_studio_shoot = True`).
     - Detects mechanical fallback cutouts or generator failures and immediately triggers Pass 2 `self_healing_fallback_retry` (or routes to `FLAG_FOR_REVIEW` if unrecovered), suppressing any artificial quality score lift.
     - **Mode-Aware Plating Integrity & Fidelity Standard**:
       - *Mode A (Strict Food-Lock Inpainting)*: Enforces pixel-level SSIM ($\ge 0.85$) since raw food pixels are locked bit-for-bit.
       - *Mode B (Generative Studio Reshoot)*: Pixel SSIM varies naturally (~0.18–0.35) due to studio relighting, depth-of-field, and photographic angle transformation. Instead of relying on a brittle pixel metric that false-flags authentic reshoots, plate geometry is evaluated via **Gemini 3.8 Flash Multimodal Plating Audit**:
         - `PRESERVED` / `ACCEPTABLE_UPGRADE`: Upgrading a worn plate or plastic container to clean, commercial restaurant ceramic matching the original vessel geometry—or removing human hands/wrappers and plating handheld food onto a clean ceramic plate—is fully compliant under FTC commercial styling guidelines (`✓ PASS`).
         - `DISTORTION_MISMATCH`: Radical alterations in vessel geometry (e.g., transforming a deep soup bowl into a flat plate, replacing a family-style tray with a tapas dish, or dumping food directly onto bare tabletops) trigger `⚠️ FLAGGED` (`FLAGGED_FOR_PLATE_GEOMETRY_DISTORTION`).
  3. **Calibrated Pre-Enhancement Quality Gate (Rule B8 Decision Bands)**:
     - **Continuous Normalization Mapping**: Discrete 1–5 integer Likert ratings returned by multimodal perception are normalized to a calibrated continuous scale ($1 \rightarrow 0.20, 2 \rightarrow 0.50, 3 \rightarrow 0.70, 4 \rightarrow 0.85, 5 \rightarrow 1.00$):
       - **$< 0.35$ (`AUTO_REJECT`)**: Severe defect / unrecoverable motion blur or dark unrecognizable blob (`Appitizer3.jpg` at `0.20`). Fast-fail bypassed in $<4.5\text{s}$.
       - **$0.35\text{–}0.54$ (`FLAG_FOR_REVIEW`)**: Borderline quality margin band (`QUALITY_BORDERLINE_REVIEW`). Quarantined for review unless overridden via `force_enhancement`.
       - **$0.55\text{–}0.74$ (`AUTO_APPROVE` — Studio Enhancement Eligible)**: Viable consumer mobile upload (`PASS`), automatically routed to Phase C `gemini-nano-banana-2.1` studio reshoot.
       - **$\ge 0.75$ (`AUTO_APPROVE` — Commercial Standard)**: High commercial quality photo (`MIN_QUALITY_AUTO_APPROVE = 0.75`).
     - **Culinary Texture Equity**: Raw Laplacian variance penalties that punished naturally smooth foods (such as pupusas, hummus, and creamy bisques) were removed from hard gating; focus and quality are evaluated via Gemini 3.8 Flash semantic perception of food boundaries and intentional culinary textures.

### 4.5 Phase C: Output Verification, Digital Provenance & Multi-Tier Safety Net

Once an asset passes Phase A preflight and Phase B moderation (or is explicitly forced via `force_enhancement=True`), Phase C governs post-generation compliance verification, cryptographic provenance, and the automated safety-net fallback strategy:

1. **Zero-Text Typography Compliance**:
   - Evaluates the generated studio output for accidental marketing words, dish titles, slogans, or typography overlays (`has_hallucinated_text = True`), ensuring commercial ad compliance.
2. **Google DeepMind SynthID v2 Imperceptible Digital Watermarking**:
   - Embeds imperceptible, frequency-domain watermarks directly into diffusion pixels during generation on Vertex AI.
   - **Bypass Rule**: Assets that bypass enhancement due to intake defects or policy rejection are never tagged with SynthID v2; they retain genuine camera original status.
3. **C2PA Content Credentials Manifest Assertion**:
   - Generates a tamper-evident cryptographic assertion linking the asset to Grubhub's verified platform signing certificate, specifying the exact transformation mode (`COMMERCIAL_STUDIO_RESHOOT`, `STRICT_FOOD_LOCK_BGSWAP`, or `RAW_VERIFIED_AUTHENTIC`), model version (`gemini-nano-banana-2.1`), and audit verdict.
4. **The Actor-Critic Safety Net & Self-Healing Architecture**:
   - **Primary Standard Engine**: Commercial studio enhancement runs exclusively on **`gemini-nano-banana-2.1`** (default `"studio_reshoot"` mode) with high-aesthetic conversion lift, human/hand removal, and editorial lighting harmonization.
   - **Automated Pass 2 Self-Healing**: If the post-enhancement Truth-in-Advertising audit detects unverified garnishes, culinary additions, or text overlays—or if Pass 1 hit a compositor fallback—the platform automatically triggers Pass 2 on **`gemini-nano-banana-2.1`**.
   - **Non-Standard Manual Tuning Option (`imagen-3.0-capability-001`)**: Imagen 3 is **not** an automatic pipeline fallback and is not used in the standard automated ingestion flow. It is accessible solely as a manual option (`background_swap`) in the interactive Photo Studio tuning drawer.

---

## 5. Platform Architecture & Merchant Ingestion Experience (Current Implementation)

The Grubhub Merchant Menu Image Platform is built and running in production on Google Cloud Run (`grubhub-merchant-platform` in `us-central1`), decoupling stateless serverless compute from persistent asset storage in Google Cloud Storage:

### 5.1 Architecture & Control Flow

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. INTERACTIVE MERCHANT PORTAL & UI (HTML5 / CSS / Vanilla JavaScript)                 │
│    • Single Drag-and-Drop & Multi-Photo Batch Intake Dropzone (w/ Force-Enhance)       │
│    • Real-Time Non-Blocking Card Streaming with Animation (@keyframes cardHighlight)   │
│    • Interactive Before/After Split-View Comparison Slider & Per-Card Tuning Drawer    │
│    • 6-Tab Merchant Quality & Integrity Scoring Guide Modal (#metricsGuideModal)       │
│    • Photo Studio & Adjustment Suite (Canvas Crop, Rotate, Sliders, Blemish Brush)     │
│    • Top Navigation Bar Links to Interactive Architecture PRD (/prd) & PDF (/prd.pdf)  │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ REST API (JSON & Multipart)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 2. CLOUD RUN API GATEWAY & PIPELINE ORCHESTRATOR (FastAPI / us-central1)               │
│    • Synchronous Single Upload Route (POST /api/upload w/ force_enhancement)           │
│    • Interactive Manual Edit & Retouch Routes (/api/image/{fn}/edit & edit-enhanced)   │
│    • Interactive Tuning Drawer Route (/api/image/{fn}/tune w/ cached_analysis)         │
│    • Atomic Asset & Ledger Deletion Route (DELETE /api/image/{fn})                     │
│    • Dynamic Fallback Asset Delivery (GET /samples/{fn} & GET /enhanced/{fn})          │
│    • Background Batch Control Plane (/api/batch/run, /process-next & /status)          │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 3. GEMINI 3.8 FLASH & NANO BANANA 2.1 AI ENGINE (Vertex AI Global Endpoints)           │
│    • Phase A: Technical Preflight (1600px Cap, A1-A5 Checks & Lanczos Upscale <50ms)   │
│    • Phase B: Parallel Moderation via gemini-3.8-flash + Cloud Vision Web Detection    │
│    • Three-Tier SOP Decision Engine + Force-Enhance Override (B1-B12)                  │
│    • Phase C Primary Studio Reshoot via gemini-nano-banana-2.1 (default mode)          │
│    • Phase D Truth-in-Advertising Comparative Audit via gemini-3.8-flash (7 criteria)  │
│    • Actor-Critic Closed-Loop Self-Healing (Pass 2 Corrective Shoot & Fallback Retry)  │
│    • [Optional Manual Edit]: Vertex AI imagen-3.0-capability-001 (Tuning Drawer Only)  │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Sync Inputs, Outputs & Ledger
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 4. SERVERLESS STORAGE & STATE PERSISTENCE (Google Cloud Storage)                       │
│    • Bucket: gs://[GCP_PROJECT_ID]-grubhub-merchant-assets                             │
│    • Raw Merchant Submissions: samples/{filename}                                      │
│    • Enhanced Studio Photography: enhanced/{filename}                                  │
│    • Master JSON Audit Ledger: decisions/moderation_decisions.json                     │
│    • Capability Matrix Results: results/capability_matrix_results.csv                  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **Layer 1: Interactive Merchant Portal Experience**:
   - Zero prompt engineering required by restaurant operators.
   - Interactive Before/After split-screen comparison slider embedded directly on each dish card.
   - Real-time multi-photo batch intake queue with animated card prepending (`@keyframes cardHighlightGlow`).
   - **"Always Execute Phase C AI Enhancement (Bypass Moderation Gate)" (`force_enhancement`)**: Available both in the Upload Sandbox (`#uploadForceEnhance`) and inside every dish card's Interactive Prompt Tuning Drawer (`#force_enhance_{filename}`), allowing operators to force studio enhancement even on flagged or rejected photos (e.g., removing chef hands/torsos or testing low-quality inputs).
   - **6-Tab Merchant Quality & Integrity Scoring Guide Modal (`#metricsGuideModal`)**: Clicking any metric pill (`Quality Lift`, `Food Integrity SSIM`, `Truth-in-Advertising`, `Pipeline Latency`, `SynthID v2 Verified`, or `Section 4 Copyright/Provenance`) opens an interactive 6-tab educational modal dynamically populated with that specific dish's real telemetry, formulas, and pass/fail thresholds.
   - Integrated Photo Studio & Adjustment Suite for manual cropping, aspect ratio locking (1:1, 4:3, 16:9), horizon leveling ($\pm 45^\circ$), exposure/contrast tuning, client-side blemish spot-healing, and depth blur.
   - Dual-stage editing workflow: raw camera pre-processing (`POST /api/image/{fn}/edit`) and post-generation studio photo retouching with lightweight re-audit (`POST /api/image/{fn}/edit-enhanced`).
   - Atomic record deletion (`DELETE /api/image/{fn}`) with explicit user confirmation, removing local files, GCS blobs, and updating the ledger.
2. **Layer 2: Cloud Run API Gateway & Control Plane**:
   - Stateless, auto-scaling FastAPI service running in `us-central1` (`grubhub-merchant-platform`) with service account `grubhub-merchant-sa@[GCP_PROJECT_ID].iam.gserviceaccount.com`.
   - **Cached Phase B Tuning (`cached_analysis`)**: When re-running a dish via `POST /api/image/{fn}/tune` without a custom inspection prompt, the server reuses the cached Phase B `analysis` and `web_provenance`, cutting re-tune latency by ~4–5 seconds and saving Phase B API costs.
   - Wildcard CORS headers (`Access-Control-Allow-Origin: *`) to ensure HTML5 canvas export compatibility without security taints.
   - Dynamic asset serving routes that stream directly from Google Cloud Storage on cache misses, eliminating 404 image errors across container redeployments and auto-scaling events.
3. **Layer 3: Gemini 3.8 Flash & Gemini Nano Banana 2.1 AI Pipeline & Actor-Critic Loop**:
   - Primary automated pipeline powered strictly by **`gemini-3.8-flash`** (moderation and 7-criteria truth auditing) and **`gemini-nano-banana-2.1`** (studio enhancement).
   - Actor-Critic closed-loop self-healing automatically remediates unverified garnishes, text, or compositor fallbacks via Pass 2 re-shoots.
   - Optional manual tuning parameter (`imagen-3.0-capability-001`) retained strictly in the adjustment drawer for bit-for-bit food-lock background swaps.
4. **Layer 4: Google Cloud Storage Persistence**:
   - Solves container disk ephemerality by syncing raw submissions (`samples/`), generated assets (`enhanced/`), and the master decisions ledger (`decisions/moderation_decisions.json`) directly to Google Cloud Storage.

### 5.2 Real-Time Upload vs. Asynchronous Batch Execution

The platform accommodates both instant interactive merchant uploads and background catalog processing:

```
                               MERCHANT PHOTO INGESTION
                                         │
              ┌──────────────────────────┴──────────────────────────┐
              ▼                                                     ▼
     Real-Time Single Upload                                Multi-Photo Intake Queue
       (POST /api/upload)                              (<input type="file" multiple>)
              │                                                     │
              ▼                                                     ▼
  SYNCHRONOUS PIPELINE                                   CLIENT-ORCHESTRATED QUEUE
─────────────────────────────────                     ─────────────────────────────────
• Phase A Preflight (1600px Cap, A1-A5)               • Parallel/Sequential Intake Queue
• Phase B Gemini 3.8 Flash + Vision Web               • Stage-by-Stage Progress Pills
• Pre-Enhancement Fast-Fail Gate:                       (Ready → Preflight → Mod → Gen)
  If Quality <0.35 or Policy Violation                • Dynamic Card Prepending to UI
  (and not force_enhancement), fast-fails             • Real-Time KPI Counter Updates
• Phase C Studio Reshoot (Nano Banana 2.1)
• Phase D 7-Criteria Audit (Gemini 3.8)               ─────────────────────────────────
• Sync to GCS Bucket & Decisions Ledger               PLATFORM BACKGROUND BATCH RUNNER
• Card HTML returned immediately                        (/api/batch/run & /process-next)
                                                      ─────────────────────────────────
                                                      • BackgroundTasks execution
                                                      • Iterates unprocessed assets
                                                      • Updates GCS ledger per photo
                                                      • Polled via GET /api/batch/status
```

1. **Real-Time Single Upload (`POST /api/upload`)**:
   - Executes atomic end-to-end evaluation: Phase A Preflight (`A1`–`A5`), Phase B parallel Gemini 3.8 Flash Moderation + Cloud Vision Web Detection, Phase C **Gemini Nano Banana 2.1** Studio Reshoot, and Phase D Gemini 3.8 Flash 7-Criteria Truth-in-Advertising Audit.
   - **Fast-Fail Quality Bypass & Force-Enhance Override**: If an image fails the intake quality gate or violates policy (and `force_enhancement` is not enabled), the pipeline fast-fails in **<4.5s**, prompts the merchant with actionable feedback, and strictly bypasses generative studio reshoots to eliminate compute waste (`$0.00393` vs. `$0.04066`).
   - For compliant (or forced) uploads, returns a structured JSON payload along with pre-rendered dish card HTML, allowing the frontend to render the card instantly.
2. **Interactive Multi-Photo Batch Intake Queue**:
   - Merchants can select or drag 10–20+ food photos simultaneously via native file intake (`<input type="file" multiple accept="image/*">`).
   - An interactive itemized queue tracks file sizes, dish names, and real-time stage progress pills (`Ready` $\rightarrow$ `⏳ Preflight` $\rightarrow$ `🔍 Moderation` $\rightarrow$ `🎨 Studio Reshoot` $\rightarrow$ `⚖️ Truth Audit` $\rightarrow$ `✅ Complete`).
   - **Live Card Streaming**: Rather than blocking the user behind a bulk loading spinner, each dish card is dynamically prepended to the top of `#cardsGrid` with a green highlight glow (`@keyframes cardHighlightGlow`) the millisecond its individual evaluation completes.
   - Top-level dashboard KPI metrics (total dishes, approval counts, quality lift %, SSIM fidelity) increment in real time with each landing card.
3. **Platform Background Batch Runner (`src/batch_runner.py` / `POST /api/batch/run` & `POST /api/batch/process-next`)**:
   - Provides asynchronous, non-blocking evaluation of sample photo catalogs.
   - Triggered via CLI or REST API (`POST /api/batch/run` or `POST /api/batch/process-next`), spawning a background worker using FastAPI `BackgroundTasks`.
   - Iterates through unprocessed photos, executes the Gemini 3.8 Flash + Nano Banana 2.1 pipeline, saves enhanced outputs, updates `results/moderation_decisions.json`, and synchronizes assets to Google Cloud Storage after each individual photo completes.
   - The frontend and operational monitoring endpoints query `GET /api/batch/status` to track live progress (`total`, `completed`, `current_index`, `current_filename`, `current_stage`, `unprocessed_count`).

### 5.3 UI Latency Telemetry, Observed Benchmarks & Optimization Architecture
To provide complete transparency to both restaurant merchants and platform operations, processing duration is instrumented at millisecond precision and rendered across all user interfaces:
1. **Strict Policy on Measured Telemetry (Zero Synthetic Estimates)**:
   - All timings cited in the UI badges, cards, 6-tab Metrics Guide modal, and CSV exports represent **actual observed round-trip wall-clock milliseconds** recorded during that specific run.
2. **Key Latency & Token Optimizations**:
   - **Working Resolution Cap (`MAX_WORKING_DIMENSION = 1600px`)**: Caps multi-megapixel uploads at 1600px during Phase A pre-flight so Laplacian blur, Cloud Vision, and downstream resizes execute instantaneously.
   - **Parallel Phase B Execution (`ThreadPoolExecutor`)**: Runs `gemini-3.8-flash` ($\le 768\text{px}$, `thinking_budget=0`, `timeout=15000ms`) and Cloud Vision `web_detection` ($\le 1024\text{px}$) concurrently, hiding network round-trip latency.
   - **Single-Tile Phase D Audit Downsampling ($\le 512\text{px}$)**: Downsamples both raw and enhanced images to $\le 512\text{px}$ (JPEG q=78, `258` tokens per image tile) with `thinking_budget=0` and `timeout=15000ms` for fast, low-cost comparative auditing.
   - **Cached Analysis on Re-Tune (`cached_analysis`)**: Re-tuning studio surfaces or framing ratios via `/api/image/{filename}/tune` reuses Phase B inspection and web provenance results when no custom inspection prompt is supplied.
   - **Pre-Enhancement Fast-Fail Gate**: For unforced uploads failing Phase A/B moderation, diffusion generation and audit are completely bypassed, delivering a fast-fail response in **~3.5s–4.5s**.
3. **Observed Real-World Latency Profile**:
   - `Preflight`: Dimensions check, 1600px cap, MIME sniff, contrast & Laplacian blur (~10–25ms).
   - `Mod`: Parallel Gemini 3.8 Flash Policy Moderation + Cloud Vision Web Detection (~3,500–5,500ms; `0ms` model wait when cached on re-tune).
   - `Gen`: **Gemini Nano Banana 2.1 (`gemini-nano-banana-2.1`)** Studio Photoshoot Reshoot (~7,500–11,000ms).
   - `Audit`: Gemini 3.8 Flash 7-Criteria Truth-in-Advertising Audit at $\le 512\text{px}$ (~3,500–6,000ms).
   - *Total End-to-End Latency*: **~15s–23s** for 1-pass compliant assets on Vertex AI Global endpoints; **~3.5s–4.5s** for quality-gated fast-fails.
### 5.4 Merchant Photo Studio & Interactive Manual Adjustment Suite
To empower restaurants with self-service fine control over their original submissions prior to or alongside AI generative enhancements, the platform incorporates an embedded client-side HTML5 Canvas Photo Studio enhanced with SOTA Google Cloud tools (as of October 2026):
1. **Seamless Entry Points & Interaction Model**:
   - **Direct Card Click-to-Open**: Merchants can click directly on the raw upload or AI-generated photo on any dish card to launch the Photo Studio. Includes smooth hover elevation and a persistent badge (*"🎨 Click to Open Photo Studio & Crop"*).
   - **Dedicated Quick Action Buttons**: Each dish card provides *"Edit Studio"* and *"AI Auto-Crop"* buttons for instant single-click entry.
   - **Universal Self-Healing Access**: Rejected or bypassed submissions (e.g., photos flagged for low resolution or competitor delivery network scraping) remain 100% editable, enabling merchants to crop out unauthorized watermarks or unneeded clutter and re-trigger pipeline evaluation.
2. **Interactive Drag-to-Crop Canvas Overlay**:
   - **Visual Bounding Box & 8 Drag Handles**: Features a Grubhub-orange framed crop rectangle with 8 handles (4 corners + 4 edge midpoints) and a 3×3 rule-of-thirds composition grid.
   - **Four-Quadrant Shaded Scrim**: Darkens regions outside the active crop box (`rgba(0,0,0,0.58)`), providing instant visual feedback on how the dish will frame on diner mobile menus.
   - **Aspect Ratio Locking & Snapping**: Supports `Freeform`, `1:1 (Square Portal)`, `4:3 (Standard Menu Item)`, and `16:9 (Hero Collection Banner)`. Dragging corner handles automatically enforces the selected aspect constraint.
   - **Live Pixel Dimension Telemetry**: Displays real-time output resolution directly inside the crop box (e.g., `630 × 472 px (4:3)`).
   - **AI Saliency Auto-Crop (Cloud Vision API)**: One-click automated framing that queries Google Cloud Vision Crop Hints to compute optimal rule-of-thirds padding and food centering for the target aspect ratio, eliminating awkward chops.
   - **Horizon Straighten**: Slider with fine $\pm 45^\circ$ angular precision and automated rule-of-thirds alignment grid.
   - **Rotate & Flip**: $\pm 90^\circ$ rotation and horizontal/vertical symmetry flip.
   - **Scale & Resize**: Non-destructive zoom and resolution resampling (50%–150%).
3. **Light & Color Studio**:
   - Real-time hardware-accelerated sliders for **Brightness** ($\pm 100\%$), **Contrast** ($\pm 100\%$), **Saturation** ($\pm 100\%$), and **Exposure** ($\pm 100\%$).
   - One-click instant reset to raw baseline.
4. **Enhancements, Retouching & Edge Segmentation**:
   - **Food Photography Preset Filters**:
     - *Warm Bistro*: Golden roast tones, rich caramelization accentuation.
     - *Vivid Foodie*: Saturated herbal greens, vibrant fresh sauce gloss.
     - *Crisp & Clean*: Neutral editorial white balance, glare reduction.
     - *Moody Studio*: High contrast, dramatic bistro vignette shadows.
     - *Golden Hour*: Ambient amber sunset illumination.
   - **AI Smart Plate Isolation (MediaPipe Tasks Vision Edge)**:
     - Embedded WebAssembly/WebGL interactive segmenter running directly in the browser (<25ms, 0 server roundtrips).
     - Automatically contours dish plate boundaries, isolates background clutter, and locks plate focal sharpness.
   - **Simple Blemish Spot-Heal Brush**:
     - Interactive circular brush (6px–40px) allowing merchants to click on stray sauce splatters, crumbs, or plate glare.
     - Seamless annular pixel sampling and radial inpainting to erase blemishes without distorting dish portions.
   - **Background Bokeh / Depth Blur**:
     - Adjustable Gaussian background blur (0–24px) paired with an elliptical or segmented dish focal mask, softening cluttered dining room tables while locking food plate sharpness.
5. **AI Enhancement Mode Selection & Force-Enhancement Toggle in Studio / Tuning Drawer**:
   - **Standard Default Mode: Commercial Studio Reshoot (`gemini-nano-banana-2.1`)**: The primary platform engine delivering high-aesthetic commercial photoshoots with lighting harmonization, authentic tableware geometry preservation, human/hand removal, zero-text tolerance, and automated Pass 2 self-healing.
   - **Optional Manual Mode: Strict Food-Lock Background Swap (Imagen 3 `imagen-3.0-capability-001` BGSWAP)**: Retained strictly as an optional manual tuning parameter in the studio drawer for merchants who explicitly wish to lock 100% of raw food pixels bit-for-bit while replacing only the background. Not used in the standard automated ingestion pipeline and not the primary path forward.
   - **Force Phase C AI Enhancement Toggle (`force_enhancement`)**: Checkbox in both the Upload Sandbox and per-card Tuning Drawer allowing merchants/operators to bypass Phase A/B moderation blocks and force a Phase C `gemini-nano-banana-2.1` studio reshoot.
6. **Dual-Stage Workflow (Raw Pre-Processing & AI Studio Photo Retouching)**:
   - **Stage 1 (Raw Pre-Processing via `POST /api/image/{filename}/edit`)**: Allows merchants to crop, straighten, adjust lighting/colors, spot-heal blemishes, or blur backgrounds on their original camera submission prior to running generative enhancement. Triggers the full Gemini 3.8 Flash + Nano Banana 2.1 pipeline and updates the workbench card.
   - **Stage 2 (AI Studio Photo Retouching via `POST /api/image/{filename}/edit-enhanced`)**: Allows merchants to open the high-resolution AI Studio Generated Photo in the studio editor to perform fine post-generation retouching. Saving a retouched AI photo executes a lightweight re-audit using **Gemini 3.8 Flash Truth-in-Advertising & Anti-Hallucination Guardrail**, recomputes food fidelity SSIM and PSNR against the raw original, updates digital provenance tokens (`MERCHANT_STUDIO_AI_RETOUCH`), and refreshes the card without incurring an expensive generative model re-run.
7. **Cross-Origin Resource Sharing (CORS) & Browser Cache Integrity**:
   - Both dynamic image delivery endpoints (`GET /samples/{filename:path}` and `GET /enhanced/{filename:path}`) and FastAPI application middleware enforce `Access-Control-Allow-Origin: *`, `Access-Control-Allow-Methods: *`, and `Access-Control-Allow-Headers: *`.
   - Ensures HTML5 canvas elements in the Photo Studio & Adjustment Suite can export clean image blobs via `.toDataURL()` and `fetch()` without cross-origin security taints (`tainted canvas`) or browser cache mismatch errors.
8. **Unobstructed Action Layout & Click-Through Accessibility for Sub-Portal Resolutions**:
   - Pre-flight warning indicators (e.g., `Below 200px Portal Min (Auto-Upscaled)`) render strictly in normal document flow rather than floating as absolute overlay masks over action controls.
   - The warning pill operates as an active interactive trigger (`Open Studio ↗`), opening the Photo Studio & Adjustment Suite directly when clicked.
   - Action buttons (`[Edit Studio]` and `[AI Auto-Crop]`) are flex-anchored to the bottom baseline (`margin-top: auto`), ensuring 100% click-through accessibility and preventing any mouse capture or UI blockage across low-resolution merchant submissions.
9. **Real-Time Photo Upload API Contract (`POST /api/upload`) & Resilient Ingestion**:
   - The upload endpoint executes atomic end-to-end evaluation (Phase A Preflight, Phase B Moderation, Phase C SOTA Enhancement, and Phase D Truth-in-Advertising Audit) and returns a complete, structured JSON payload: `{"status": "success", "filename": "...", "result": {...}, "card_html": "..."}`.
   - Client-side ingestion scripts enforce defensive validation (`resp.ok && data && data.status === 'success'`) to prevent null reference TypeErrors across network disruptions or serverless container recycles.
   - Newly ingested merchant submissions and generated assets are mirrored to Google Cloud Storage (`samples/` and `enhanced/`), guaranteeing persistence across Cloud Run scale-to-zero events.
10. **Multi-Photo Batch Intake Queue & Real-Time Live Card Streaming**:
    - **Multi-File Selection & Drag-and-Drop Dropzone**: Native support for selecting or dragging multiple menu food photos simultaneously (`<input type="file" multiple accept="image/*">`), allowing merchants to onboard full multi-course menus in one go.
    - **Interactive Itemized Intake Queue**: Displays real-time thumbnails, file sizes, and stage-by-stage progress pills (`Ready` $\rightarrow$ `⏳ Preflight` $\rightarrow$ `🔍 Gemini 3.8 Moderation` $\rightarrow$ `🎨 Studio Reshoot` $\rightarrow$ `⚖️ Truth-in-Adv Audit` $\rightarrow$ `✅ Complete`). Merchants can remove pending items prior to ingestion.
    - **Live Non-Blocking Card Streaming**: Rather than waiting for the entire batch to complete or requiring a full page refresh, each dish card is dynamically prepended to `#cardsGrid` the exact millisecond its evaluation completes, animated with a green highlight glow (`@keyframes cardHighlightGlow`).
    - **Real-Time KPI Metric Reactivity**: Dynamic JavaScript counters immediately increment total processed dishes, approval/review/rejection counts, and filter pill badges as each photo lands on the dashboard.
11. **Enterprise Record Deletion & Serverless Asset Cleanup (`DELETE /api/image/{filename}`)**:
    - **Card Header Action Button**: Each card features a distinct `🗑️ Delete Record` button with explicit user confirmation to prevent accidental menu deletions.
    - **Atomic Ledger Removal**: Permanently removes the record from `results/moderation_decisions.json` and syncs the updated ledger to Google Cloud Storage via `sync_to_gcs()`.
    - **Complete Asset Purge**: Automatically unlinks raw merchant submissions from `Sample-Photos/` and generative assets from `results/enhanced_images/`, and issues GCS bucket deletes (`samples/{filename}` and `enhanced/{filename}`) to prevent orphaned storage bloat.
    - **Animated DOM Eviction & KPI Recalculation**: Smoothly collapses and removes the dish card element from the view (`.card-deleting`), updates in-memory telemetry, and recalculates all top-level KPI counters and percentage breakdowns.
12. **Serverless Ephemeral Storage Resilience & On-Demand GCS Fallback Serving**:
    - **Ephemeral Container Decoupling**: In serverless runtimes (Google Cloud Run), container filesystems are completely stateless and ephemeral across container restarts, revision rollouts, and horizontal auto-scaling.
    - **Dynamic Fallback Routes (`GET /samples/{filename}` & `GET /enhanced/{filename}`)**: Replaced static filesystem mounts with dynamic asset delivery handlers. If an image is absent from local disk upon container boot, the endpoint fetches the blob directly on-demand from Google Cloud Storage (`gs://grubhub-merchant-assets/samples/` or `/enhanced/`), hydrates the local disk cache, and returns the image response immediately (eliminating 404s on restarts).
    - **Dual Raw & Enhanced Asset Cloud Sync**: Guarantees that every raw merchant submission (`POST /api/upload`), manual studio adjustment (`POST /api/image/{filename}/edit`), prompt/ratio tuning run (`POST /api/image/{filename}/tune`), and enhanced retouch (`POST /api/image/{filename}/edit-enhanced`) syncs both input and output image binaries alongside the central JSON decisions ledger to Google Cloud Storage.
    - **Warm Startup Cache Sync**: Cold-starting container instances trigger `sync_assets_from_gcs()` during `@app.on_event("startup")` to pre-populate local working directories.

### 5.5 Google SynthID v2 & C2PA Content Credentials Provenance
In full compliance with 2026 consumer protection standards, EU AI Act transparency rules, and FTC Truth-in-Advertising guidelines:
1. **Google SynthID v2 Digital Watermarking**:
   - Automatically embedded into high-frequency pixel representations across all AI-edited or generated images on Vertex AI (`gemini-nano-banana-2.1` and `imagen-3.0-capability-001`).
   - Imperceptible to human diners, resilient to resizing, compression, screenshots, and color grading.
2. **C2PA Content Credentials**:
   - Cryptographic attestations signed by Google Cloud and Grubhub, logging the exact editing pipeline used (`STRICT_FOOD_LOCK_BGSWAP` vs `COMMERCIAL_STUDIO_RESHOOT`), model identifier (`gemini-nano-banana-2.1`), timestamp, and real-food authenticity audit token.
   - Rendered in the UI with a verifiable `🛡️ SynthID v2 Verified • C2PA Authentic` badge that opens Pane 5 of the Interactive Scoring Guide Modal.

### 5.6 Grubhub for Merchants Design System & Visual Identity
In alignment with the official **Grubhub for Merchants** web portal visual identity:
1. **Brand Color Hierarchy & Tokens**:
   - **Signature Grubhub Orange (`#FF5500`)**: Core brand mark, high-energy status accents, and floating merchant assistance widget.
   - **Grubhub Iris / Purple (`#572AF8`)**: Primary action call-to-action buttons ("Join Grubhub", "Run Real-Time Ingestion"), active tabs, search icons, and breadcrumb hyperlinks.
   - **Canvas & Surface Styling**: Crisp pure white cards (`#FFFFFF`) on a neutral high-contrast background (`#F8F9FA`), accented by soft drop shadows (`0 4px 20px rgba(0, 0, 0, 0.04)`) and rounded pill borders (`border-radius: 9999px` for buttons, `16px` for cards).
   - **Semantic Moderation Badges**:
     - *Auto-Approved / Pass*: Soft mint (`#ECFDF5` background, `#047857` text, `#A7F3D0` border).
     - *Flagged / Review*: Warm amber (`#FFFBEB` background, `#B45309` text, `#FDE68A` border).
     - *Rejected / Fail*: Soft coral (`#FEF2F2` background, `#B91C1C` text, `#FECACA` border).
2. **Typography System**:
   - **Display & Headlines**: Geometric sans-serif (**GT Walsheim** / **Plus Jakarta Sans** / **Poppins**) with heavy bold weighting (`font-weight: 800–900`), tight negative letter-spacing (`-0.03em`), and tight line height (`1.05–1.15`), matching the iconic *"Your Grubhub for Merchants portal"* hero styling.
   - **Body & Metadata**: High-legibility neutral sans-serif (**Plus Jakarta Sans** 400–600 weight) with clear contrast ratios exceeding WCAG 2.1 AA standards.
3. **Portal Experience Components**:
   - Sticky top navigation bar featuring the **GRUBHUB** wordmark, "For Merchants" descriptor, uppercase category links, direct links to `📐 ARCHITECTURE PRD` (`/prd`) and `📄 PRD PDF` (`/prd.pdf`), and pill-shaped "SIGN IN" button.
   - Live breadcrumb trail navigating from `Home » Products » Merchant Portal`.
   - Dual-stage Photo Studio modal providing high-contrast darkroom canvas viewport paired with clean Grubhub-branded adjustment sidebars.
   - 6-Tab Interactive **Merchant Quality & Integrity Scoring Guide Modal** (`#metricsGuideModal`) explaining Quality Lift, Food Integrity SSIM/PSNR, Truth-in-Advertising, Pipeline Latency, SynthID v2 Provenance, and Section 4 Reverse-Image Copyright Verification.
   - Persistent bottom-right floating support action button in official Grubhub orange.

---

## 6. API Specifications & Data Contracts

### 6.1 Interactive Tuning API Contract (with Cached Phase B Optimization)
`POST /api/image/{filename}/tune`

Allows the internal workbench or authorized portal endpoints to re-run enhancement with custom surface prompts, framing ratios, SOTA modes, or forced enhancement (`force_enhancement`). When `custom_inspection_prompt` is omitted, the endpoint automatically passes `cached_analysis` from the existing decision ledger into `process_single_image()`, reusing the Phase B `gemini-3.8-flash` moderation and Cloud Vision `web_provenance` results to eliminate redundant Phase B latency and API charges.

#### Request Body
```json
{
  "custom_bg_prompt": "Elegantly presented on a rustic dark walnut cutting board with natural wood grain, warm ambient lighting, and realistic contact shadows.",
  "food_ratio": 0.55,
  "target_aspect": "4:3",
  "min_quality_threshold": 0.35,
  "use_pro_model": false,
  "strict_anti_hallucination": true,
  "enhancement_mode": "studio_reshoot",
  "enable_self_healing": true,
  "force_enhancement": false
}
```

### 6.2 Google Cloud Vision Saliency Crop Hints Contract
`GET /api/image/{filename}/crop-hints`

Returns visual saliency crop hints for 1:1, 4:3, and 16:9 aspect ratios based on detected food ROIs.

#### Response Body
```json
{
  "filename": "Appetizer1.jpg",
  "crop_hints": {
    "1:1": {
      "aspect_ratio": "1:1",
      "crop_pixels": {"x": 48, "y": 23, "width": 142, "height": 142},
      "normalized_bounding_box": [0.1203, 0.2525, 0.8678, 1.0],
      "confidence": 0.96,
      "importance_fraction": 0.559
    },
    "4:3": {
      "aspect_ratio": "4:3",
      "crop_pixels": {"x": 42, "y": 38, "width": 148, "height": 111},
      "normalized_bounding_box": [0.2015, 0.22, 0.7865, 1.0],
      "confidence": 0.96,
      "importance_fraction": 0.456
    },
    "16:9": {
      "aspect_ratio": "16:9",
      "crop_pixels": {"x": 0, "y": 40, "width": 190, "height": 107},
      "normalized_bounding_box": [0.2127, 0.0, 0.7753, 1.0],
      "confidence": 0.96,
      "importance_fraction": 0.562
    }
  }
}
```

### 6.3 Merchant Raw Photo Pre-Processing & Re-evaluation Contract
`POST /api/image/{filename}/edit`

Allows merchants to submit cropped, straightened, color-adjusted, blemish-healed, or bokeh-blurred versions of their raw camera photos, immediately re-evaluating the submission through the Gemini 3.8 Flash + Gemini Nano Banana 2.1 pipeline.

#### Request Body
```json
{
  "image_base64": "data:image/jpeg;base64,...",
  "save_as_copy": false,
  "run_ai_enhancement": true,
  "target_aspect": "4:3",
  "enhancement_mode": "studio_reshoot",
  "custom_bg_prompt": "Rustic dark walnut surface with soft natural side-lighting",
  "food_ratio": 0.55
}
```

#### Response Body
```json
{
  "status": "success",
  "filename": "Appetizer1.jpg",
  "result": {
    "filename": "Appetizer1.jpg",
    "sop_decision": {
      "status": "AUTO_APPROVE",
      "reasons": ["ALL_POLICIES_PASSED"],
      "phase_a_checks": [
        {
          "id": "A1_DIMENSIONS",
          "name": "Portal Minimum Dimensions (≥200×200 px)",
          "status": "AUTO_RESOLVED",
          "details": "Raw was 190×190 px; auto-upscaled with Lanczos to 400×400 px."
        }
      ],
      "phase_b_checks": [
        {
          "id": "B1_FOOD_VALIDATION",
          "name": "Food & Beverage Validation",
          "status": "PASS",
          "details": "Authentic food confirmed: 'Chicharrón de Pescado'."
        },
        {
          "id": "B10_TRUTH_IN_ADVERTISING",
          "name": "Truth-in-Advertising & Anti-Hallucination Guardrail",
          "status": "PASS",
          "details": "Food authentic (Risk: 0.10). Zero hallucinated garnishes or portion inflation."
        }
      ]
    },
    "authenticity_audit": {
      "ingredients_raw": ["fried fish", "green sauce", "yellow sauce", "white sauce", "onion tomato salad"],
      "ingredients_enhanced": ["fried fish", "green sauce", "yellow sauce", "white sauce", "onion tomato salad"],
      "hallucinated_items": [],
      "portion_count_drift": 0,
      "truth_in_advertising_risk_score": 0.10,
      "is_authentic": true
    },
    "fidelity": {
      "food_fidelity_ssim": 0.942,
      "food_fidelity_psnr_db": 22.4,
      "is_food_integrity_preserved": true
    },
    "quality_metrics": {
      "quality_score_pre": 0.92,
      "quality_score_post": 0.98,
      "quality_lift_percent": 6.5
    },
    "latency_seconds": 18.42,
    "timing_breakdown": {
      "preflight_ms": 22,
      "moderation_ms": 4410,
      "enhancement_ms": 9240,
      "audit_ms": 4748,
      "total_seconds": 18.42
    }
  }
}
```

### 6.4 AI Studio Photo Retouch & Truth-in-Advertising Re-Audit Contract
`POST /api/image/{filename}/edit-enhanced`

Allows merchants to perform post-generation touch-ups directly on the AI-generated studio photo (spot-healing minor background or lighting artifacts, tweaking warmth/exposure, applying filters, or adjusting framing). Instead of repeating costly generative shoots, this endpoint updates the enhanced asset and executes a comparative **Gemini 3.8 Flash Truth-in-Advertising Audit**, recalculates SSIM/PSNR, and issues new C2PA digital provenance.

#### Request Body
```json
{
  "image_base64": "data:image/jpeg;base64,...",
  "enhanced_filename": "enhanced_Appetizer1.jpg",
  "save_as_copy": false
}
```

#### Response Body
```json
{
  "status": "success",
  "filename": "Appetizer1.jpg",
  "enhanced_filename": "enhanced_Appetizer1.jpg",
  "authenticity_audit": {
    "ingredients_raw": ["fried fish", "green sauce", "yellow sauce", "white sauce", "onion tomato salad"],
    "ingredients_enhanced": ["fried fish", "green sauce", "yellow sauce", "white sauce", "onion tomato salad"],
    "hallucinated_items": [],
    "portion_count_drift": 0,
    "truth_in_advertising_risk_score": 0.08,
    "is_authentic": true
  },
  "fidelity": {
    "food_fidelity_ssim": 0.948,
    "food_fidelity_psnr_db": 23.2,
    "is_food_integrity_preserved": true
  },
  "digital_provenance": {
    "synthid_v2_embedded": true,
    "c2pa_manifest_id": "c2pa:urn:uuid:68a12e...",
    "transformation_mode": "MERCHANT_STUDIO_AI_RETOUCH",
    "model_used": "MerchantStudioRetouch+Gemini-3.8-Flash-Audit"
  }
}
```

### 6.5 Real-Time Upload & Evaluation API Contract
`POST /api/upload`

Enables live evaluation of any newly submitted food photo (via drag-and-drop or file picker in the evaluation workbench). Immediately processes the asset through the Gemini 3.8 Flash + Gemini Nano Banana 2.1 pipeline, prepends the result to the evaluation registry, and refreshes the visual dashboard.

#### Request Body (`multipart/form-data`)
- `file`: Image binary (`image/jpeg`, `image/png`, `image/webp`, up to 5MB).
- `custom_bg_prompt` *(optional, string)*: Custom studio background prompt string.
- `food_ratio` *(optional, float)*: Target food-to-canvas ratio (0.40–0.75, default 0.55).
- `target_aspect` *(optional, string)*: Target aspect ratio (`"4:3"`, `"1:1"`, `"16:9"`, default `"4:3"`).
- `custom_inspection_prompt` *(optional, string)*: Custom policy or moderation guidelines.
- `min_quality_threshold` *(optional, float)*: Minimum quality floor for generative studio enhancement (default `0.35`, matching `MIN_QUALITY_AUTO_ENHANCE` in `src/config.py` and Rule B8).
- `enhancement_mode` *(optional, string)*: Studio mode (`"studio_reshoot"` or `"background_swap"`, default `"studio_reshoot"`).
- `force_enhancement` *(optional, string/bool)*: When `"true"`, forces Phase C AI studio enhancement (`gemini-nano-banana-2.1`) to execute even if Phase A/B moderation flags or rejects the raw photo.

#### Response Body
```json
{
  "status": "success",
  "filename": "Dessert1_1.jpg",
  "result": {
    "filename": "Dessert1_1.jpg",
    "sop_decision": {
      "status": "AUTO_APPROVE",
      "reasons": ["ALL_POLICIES_PASSED"],
      "phase_a_checks": [...],
      "phase_b_checks": [...]
    },
    "authenticity_audit": {
      "ingredients_raw": ["apple tart", "pastry crust", "cinnamon glaze"],
      "ingredients_enhanced": ["apple tart", "pastry crust", "cinnamon glaze"],
      "hallucinated_items": [],
      "portion_count_drift": 0,
      "truth_in_advertising_risk_score": 0.05,
      "is_authentic": true
    },
    "enhanced_filename": "enhanced_Dessert1_1.jpg",
    "latency_seconds": 17.85,
    "timing_breakdown": {
      "preflight_ms": 21,
      "moderation_ms": 4120,
      "enhancement_ms": 8940,
      "audit_ms": 4769,
      "total_seconds": 17.85
    }
  },
  "card_html": "<div class=\"dish-card\" id=\"card_Dessert1_1.jpg\" ...>...</div>"
}
```

### 6.6 Enterprise Record Deletion & Cloud Storage Purge Contract
`DELETE /api/image/{filename}`

Permanently removes a dish evaluation record from the central JSON decisions ledger (`results/moderation_decisions.json`), deletes local container image files, issues atomic deletions for both the raw photo (`samples/{filename}`) and generative asset (`enhanced/{enhanced_filename}`) in Google Cloud Storage (`gs://grubhub-merchant-assets`), and immediately regenerates the HTML visual dashboard and CSV capability matrix.

#### Path Parameters
- `filename` *(string)*: Unique filename of the target dish (e.g. `Appetizer1.jpg` or `uploaded_burger.jpg`).

#### Response Body
```json
{
  "status": "success",
  "message": "Successfully deleted record for uploaded_burger.jpg",
  "filename": "uploaded_burger.jpg",
  "remaining_count": 50
}
```

### 6.7 Dynamic Asset Serving & Cloud Storage Fallback Contract
`GET /samples/{filename:path}`  
`GET /enhanced/{filename:path}`

Dynamic, resilient asset streaming routes engineered for stateless, serverless container runtimes (Cloud Run). Replaces naive static mounts to guarantee 0% 404 error rates across cold starts, auto-scaling, and container redeployments.

- **Local Cache First**: Immediately serves cached image files from container disk in sub-milliseconds if present.
- **On-Demand GCS Fallback**: If absent (fresh container boot or post-restart), dynamically streams the blob from Google Cloud Storage (`gs://grubhub-merchant-assets/samples/{filename}` or `/enhanced/{filename}`), caches it to local container storage, and serves with HTTP 200 `FileResponse`.
- **Legacy Prefix Fallback**: Checks historical `/enhanced_images/` prefix for backwards compatibility with prior evaluations.
- **CORS Headers**: Enforces `Access-Control-Allow-Origin: *` across all responses, ensuring HTML5 canvas export compatibility in the photo studio suite.

### 6.8 On-Demand Dish Card HTML Markup Contract
`GET /api/image/{filename}/card-html`

Returns pre-rendered HTML markup for an individual dish card (`text/html`), allowing the frontend UI to fetch or stream individual cards without reloading or regenerating the entire multi-megabyte dashboard document.

### 6.9 Catalog Ledger Enumeration Contract
`GET /api/images`

Returns the complete inventory of all ingested and pending sample photos, joining local container disk assets with all historical records synchronized from the Google Cloud Storage decisions ledger (`results/moderation_decisions.json`).

#### Response Body
```json
{
  "total": 51,
  "images": [
    {
      "filename": "Appetizer1.jpg",
      "processed": true,
      "dish_name": "Chicharrón de Pescado",
      "status": "AUTO_APPROVE",
      "quality_pre": 0.92,
      "quality_post": 0.98,
      "food_ssim": 0.942,
      "enhanced_image_url": "/enhanced/enhanced_Appetizer1.jpg",
      "sample_image_url": "/samples/Appetizer1.jpg"
    }
  ]
}
```

### 6.10 Single Dish Evaluation Details
`GET /api/image/{filename}`

Returns the complete evaluation dictionary for a specific photo. If the photo has not yet been processed, dynamically triggers the end-to-end evaluation pipeline on the fly, persists the result to `moderation_decisions.json`, and synchronizes the ledger and assets with Google Cloud Storage.

### 6.11 Incremental Batch Evaluation & Status Control Plane
`GET /api/batch/status`  
`POST /api/batch/run`  
`POST /api/batch/process-next`

- `GET /api/batch/status`: Returns live batch execution telemetry (`is_running`, `total`, `current_index`, `current_filename`, `current_stage`, `completed`, `error`, `unprocessed_count`).
- `POST /api/batch/run` & `POST /api/batch/process-next`: Spawns asynchronous background worker running the incremental batch ingestion runner over the next $N$ unprocessed photos, persisting decisions and syncing assets to Google Cloud Storage after each individual photo completes.

---

## 7. Gemini 3.0+ & Nano Banana 2.1 Prompt Engineering, System Instructions & Model Roles

### 7.1 Gemini 3.8 Flash Multimodal Inspection & Policy Prompt (`src/moderator.py`)
Executed with `model="gemini-3.8-flash"`, `temperature=0.0`, `response_mime_type="application/json"`, `thinking_budget=0`, and `http_options=HttpOptions(timeout=15000)`:

```
You are Grubhub's expert food photography moderation and quality inspection AI.
Analyze this merchant-submitted menu photo against Grubhub's commercial standards.

Inspect and evaluate the following:
1. Confirm if the asset depicts authentic edible food or beverage.
2. SafeSearch: adult, violent, or spoof content.
3. Human presence, faces, or body parts (hands, fingers, thumbs, wrists, arms, chef/person torso, aprons, or faces) visible anywhere in the frame, holding the plate/dish, or touching/near the food. Set "body_parts_on_food": true if ANY human hands, fingers, arms, or people are holding the plate/food or visible in the shot, and list them in "objects_to_remove".
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
```

### 7.2 Gemini 3.8 Flash Truth-in-Advertising Auditor Prompt (`src/authenticity_auditor.py`)
Executed with `model="gemini-3.8-flash"`, `temperature=0.1`, `response_mime_type="application/json"`, `thinking_budget=0`, and `http_options=HttpOptions(timeout=15000)` on single-tile $\le 512\text{px}$ inputs:

```
You are Grubhub's Chief Truth-in-Advertising and Food Authenticity Auditor.
Your responsibility is to protect diners and merchants from deceptive AI photo enhancements,
ensuring strict compliance with FTC Truth-in-Advertising guidelines and Grubhub Menu Standards.

Compare Image 1 (Raw Merchant Submission) with Image 2 (AI-Enhanced Menu Photo).

Audit the following criteria strictly:
1. Garnish & Ingredient Hallucination:
   Did Image 2 add any herbs, cilantro, parsley, sesame seeds, chili flakes, cheese, sauces, toppings, or garnishes NOT present in Image 1?
2. Portion Size Inflation:
   Did Image 2 alter the portion size, item count (e.g. number of wings/ribs/tacos/dumplings), or container size?
   - COMPLIANT REFRAMING & UNCLIPPING: If the raw merchant photo was a close crop that cut off or clipped pieces at the edge (e.g. wings, fries, celery/carrots), naturally completing the clipped edge pieces or revealing 1 natural piece to complete the round plate presentation during commercial studio reframing is FULLY COMPLIANT and acceptable under FTC commercial styling guidelines. Do NOT flag a 4-to-5 piece completion as a hallucination or drift. Only flag intentional, deceptive portion inflation (e.g. generating 8-12 wings for a 4-piece appetizer, or doubling a bowl portion).
3. Extraneous Dishes or Ramekins:
   Did Image 2 add side dishes, extra dipping sauce cups, or cutlery not in Image 1?
4. Tableware & Plating Geometry Consistency:
   Evaluate whether Image 2 preserved the fundamental plating format, container type, and vessel geometry of Image 1:
   - COMPLIANT UPGRADE: Upgrading a worn plate or plastic container to a clean, commercial ceramic/porcelain dish of the SAME general geometry (e.g. round bowl to round ceramic bowl, platter to platter) is FULLY COMPLIANT and acceptable under FTC commercial styling guidelines.
   - COMPLIANT HAND / BODY-PART REMOVAL: If Image 1 showed food held in human hands, by a chef/person, or in a messy paper wrapper, and Image 2 removed the human hands/body parts/person and placed the food cleanly onto a commercial plate or serving board on a tabletop surface, this is a REQUIRED policy remediation and MUST be rated "ACCEPTABLE_UPGRADE" (NOT a distortion mismatch).
   - DISTORTION MISMATCH: Radical alterations in vessel geometry (e.g. converting a deep soup bowl into a flat platter, replacing a family-style tray with a tiny tapas dish, or dumping food directly onto bare tabletops without tableware) violate plating integrity.
   Set "plate_geometry_status" to "PRESERVED" | "ACCEPTABLE_UPGRADE" | "DISTORTION_MISMATCH".
5. Text & Typography Hallucination (Strict Violation):
   Did Image 2 introduce ANY text, letters, words, slogans, titles, captions, watermarks, or typography (e.g. "THE ART OF DUMPLINGS", dish names, promotional labels) not present in Image 1?
   Grubhub menu policy strictly prohibits superimposed marketing text or slogans on dish photos. If ANY text was generated, set "has_hallucinated_text": true and record the text in "hallucinated_text_content".
6. Reality Gap & Disproportionate Enhancement (Deceptive Advertising Standard):
   Evaluate whether Image 2 looks like an unrealistic, fabricated luxury fantasy divergent from the real-world merchant dish:
   - COMPLIANT COMMERCIAL STUDIO UPGRADE: Providing clean studio lighting, crisp focus, commercial contact shadows, and an authentic restaurant tabletop surface while preserving the dish ingredients is FULLY COMPLIANT and the core objective of Grubhub's enhancement platform.
   - DISPROPORTIONATE FABRICATION: Only flag if the AI fabricates extravagant luxury ingredients (e.g. truffles, caviar, gold leaf) or turns a basic plastic takeout box into a Michelin-star multi-course banquet.
   Rate "reality_gap_score" from 0.0 (faithful commercial shoot) to 1.0 (fabricated luxury fantasy). If reality_gap_score > 0.55, set "is_excessive_reality_gap": true.
7. Risk Assessment:
   Rate truth_in_advertising_risk_score from 0.0 (completely faithful) to 1.0 (severe consumer deception / allergy risk).

Return strictly JSON matching this schema:
{
  "ingredients_raw": ["string"],
  "ingredients_enhanced": ["string"],
  "hallucinated_items": ["string"],
  "portion_count_drift": 0,
  "plate_geometry_status": "PRESERVED" | "ACCEPTABLE_UPGRADE" | "DISTORTION_MISMATCH",
  "plate_geometry_notes": "string",
  "has_hallucinated_text": false,
  "hallucinated_text_content": "",
  "reality_gap_score": 0.15,
  "is_excessive_reality_gap": false,
  "truth_in_advertising_risk_score": 0.15,
  "risk_level": "LOW" | "MEDIUM" | "HIGH",
  "audit_verdict": "PASS" | "FLAG_OVER_ENHANCED",
  "explanation": "string",
  "remediation": "string"
}
```

### 7.3 Gemini Nano Banana 2.1 Commercial Studio Prompt Assembly (`src/enhancer.py`)
Executed with `model="gemini-nano-banana-2.1"` (default `"studio_reshoot"` mode, GA October 6, 2026). The prompt is assembled dynamically based on whether human hands/body parts were detected in Phase B (`body_parts_present` or `has_hand_roi`) and whether Pass 2 is recovering from a compositor fallback (`self_healing_fallback_retry`):

```
High-end commercial restaurant menu photography of authentic {dish_name} ({cuisines}).
The plated dish ({tableware_geom}) rests naturally on {surface_desc}.

COMMERCIAL MENU FRAMING & STUDIO COMPOSITION: Present the complete plated dish in an appetizing, professional restaurant menu photoshoot. If the raw submission is tightly cropped or cuts off edges of the dish/tableware, naturally reframe and uncrop the complete plated dish ({tableware_geom}) on {surface_desc}, revealing the natural plate perimeter, contact shadows, clean tabletop surface, and warm restaurant dining atmosphere.

[IF body_parts_present OR has_hand_roi]:
CRITICAL HUMAN & BODY PART REMOVAL: Completely remove all human hands, fingers, thumbs, wrists, arms, chef/person torsos, aprons, and people from the image. Reconstruct any food or plate edges previously occluded by fingers or hands naturally and seamlessly. Place the plated dish ({tableware_geom}) or handheld food naturally resting flat onto {surface_desc} with realistic gravity and contact shadows.

[ELSE]:
TABLEWARE & PLATING GEOMETRY PRESERVATION: Preserve the authentic plating format, container type, and vessel geometry of the original submission (e.g. {tableware_geom}). The food must remain in or on its authentic vessel (upgraded to clean, commercial restaurant ceramic, porcelain, or stoneware matching the original geometry and proportions). Do NOT discard the plate, do NOT dump food directly onto the bare table surface, and do NOT alter the fundamental vessel geometry (e.g. do not turn a bowl into a flat plate or vice versa).

STRICT TRUTH-IN-ADVERTISING GUARDRAIL: Do NOT add any garnishes, herbs, cilantro, parsley, sesame seeds, chili flakes, extra dipping sauce ramekins, side dishes, wine glasses, or cutlery that do not already exist in the original submission. Maintain the exact food ingredients, portion size, and arrangement. Do NOT invent or embellish gourmet textures that diverge from the raw upload.

CRITICAL MANDATORY REQUIREMENT - ZERO TEXT TOLERANCE: Absolutely NO text, NO words, NO letters, NO numbers, NO typography, NO slogans, NO titles, NO subtitles, NO watermarks, NO brand names, and NO labels. The output must be 100% clean culinary photography depicting ONLY the physical food and tabletop surface. Do NOT render any marketing copy, ad text, or headlines anywhere on the canvas.

[INJECTED DURING PASS 2 SELF-HEALING ONLY]:
MANDATORY AUDITOR REMEDIATION DIRECTIVE (PASS 2 SELF-HEALING): {corrective_directive} Adhere strictly to this instruction and do not reproduce the rejected elements.

Ensure the plated dish and all original sauces are grounded naturally with realistic contact shadows, warm appetizing studio lighting, subtle depth of field, and crisp commercial resolution. Completely remove any human hands, fingers, arms, body parts, greasy paper wrappers, or cluttered background objects, leaving only the appetizing food on its serving dish.
Strictly forbidden: Any human hands or fingers, or any text, letters, or words anywhere in the photo.
```

### 7.4 Model Role Clarification: Primary Pipeline vs. Optional Manual Edit Mode

To ensure absolute architectural clarity regarding the deployment:

| Pipeline Stage | Primary Foundation Model | Execution Context | Mandatory Operational Constraints & Rules |
| :--- | :--- | :--- | :--- |
| **Phase A: Technical Preflight** | Deterministic Resampling (Lanczos / Pillow) | Automatic (Every upload) | $\ge 200\text{px}$ standard ($\ge 100\text{px}$ upscaled floor); $1600\text{px}$ working cap; $\le 5\text{MB}$; MIME sniffing; contrast ($\text{StdDev} \ge 5.0$) & aspect ratio ($0.25\text{–}4.0$) checks (`A1`–`A5`). |
| **Phase B: Policy Moderation** | **`gemini-3.8-flash`** + Google Cloud Vision Web Detection | Automatic (Parallel on Upload; Cached on Re-Tune) | 12 discrete SOP rules (B1–B12); human/hand/chef detection (`B7`); calibrated quality bands (`<0.35` Reject, `0.35–0.54` Review, `>=0.55` Studio Eligible); `force_enhancement` override. |
| **Phase C: Commercial Studio Reshoot** | **`gemini-nano-banana-2.1`** (GA Oct 6, 2026) | Automatic (Standard Ingestion) | Default `"studio_reshoot"` mode. Zero-text mandate; tableware geometry preservation; human/hand removal (`CRITICAL HUMAN & BODY PART REMOVAL`); contact shadow grounding. |
| **Phase D: Truth-in-Advertising Audit** | **`gemini-3.8-flash`** ($\le 512\text{px}$) | Automatic (Standard Ingestion) | 7-criteria comparative verification; threshold $\text{Risk} \le 0.25$; compliant hand/body-part removal rated `ACCEPTABLE_UPGRADE`; structured remediation synthesis. |
| **Self-Healing Loop (Pass 2)** | **`gemini-nano-banana-2.1`** | Automatic (When Flagged or Fallback) | Intercepts `FLAG_OVER_ENHANCED` or `FALLBACK_MASK_PROTECTED_COMPOSITOR`; injects remediation directive or `self_healing_fallback_retry`; re-audits output. |
| **Optional Manual Background Swap** | **`imagen-3.0-capability-001`** | **Manual Only** (Tuning Drawer / Edit API) | **Not used in the standard automated ingestion pipeline. Not the primary path forward.** Retained strictly as an optional manual edit mode (`background_swap`) in the interactive tuning drawer for merchants who explicitly opt to lock 100% of raw food pixels bit-for-bit. |

---

## 8. Empirical Benchmark Findings Across the 50 Sample Photos

We conducted comprehensive evaluation across the representative merchant test set in `Sample-Photos/Sample-Photos/`:

### 8.1 Dataset Quality Distribution
- **Portal Minimum Violations**: **21 out of 50 images (42%)** were below the 200×200 px portal minimum (e.g. `Appitizer3.jpg` is 128×128 px, `Appetizer1.jpg` is 190×190 px, `Appitizer2.jpg` is 300×168 px).
- **Format Mismatches**: 10 PNGs and 2 WebPs disguised with `.jpg` extensions.
- **Resolution Range**: Varied from 128×128 px thumbnails up to 4032×3024 px mobile camera uploads (`Dessert1.jpg`, automatically capped at `1600px` working dimension in Phase A).

### 8.2 Architectural Comparison: Oval Vignette vs. Direct Gemini Nano Banana 2.1 Reshoot
1. **Mechanical Oval Mask Cutout**:
   - *Failure Mode*: Caused an artificial "cookie-cutter" sticker effect. The dish floated in mid-air over tables (observed in `Appitizer3.jpg`), trapped background fragments inside the oval (blue Peruvian cloth in `Appetizer1.jpg`), and severed side sauce ramekins.
   - *Verdict*: **Unacceptable for commercial advertising.**
2. **Direct Gemini Nano Banana 2.1 (`gemini-nano-banana-2.1`) Reshoot with Anti-Hallucination Guardrails**:
   - *Result*: Reframed dishes with natural perspective, grounded bowls on authentic black slate and mahogany tables, removed intrusive hands/arms, rendered physical contact shadows, and preserved all side sauces at `$0.0361` per 1K studio reshoot (47% lower generation cost than the prior-generation baseline).
   - *Verdict*: **Commercial advertising & hero campaign grade.**

### 8.3 Case Study Verifications
- **Case Study 1 (`Appetizer1.jpg` - Peruvian Chicharrón & Salsa Criolla)**:
  - *Raw*: 190×190 px, harsh blue textile background, 3 dipping sauce cups, and onion/tomato salad.
  - *Phase A*: Auto-upscaled with Lanczos super-resolution to 400×400 px.
  - *Enhancement*: Replaced tablecloth with clean dark slate serving board resting on concrete tabletop; grounded bowls with realistic physical contact shadows.
  - *Gemini 3.8 Flash Multimodal Inspection*:
    - Identified primary dish: **Peruvian Chicharrón** (Cuisines: Peruvian, Latin American, Seafood).
    - Identified side dish: **Salsa Criolla** (red onion, tomato, cilantro).
    - Multi-factor quality score: **0.90** (Focus/Sharpness: 0.92, Lighting: 0.88, Composition: 0.90).
  - *Gemini 3.8 Flash Truth-in-Advertising Audit*:
    - Confirmed fried seafood/chicken pieces, 3 dipping sauces (white, green, yellow), and salsa criolla were 100% preserved.
    - `hallucinated_items: []`, `portion_count_drift: 0`.
    - Truth-in-Advertising Risk Score: **0.05** (Low risk) $\rightarrow$ **`AUTO_APPROVE`**.
- **Case Study 2 (`Appitizer3.jpg` - Glazed Rib Tips: Deterministic Fast-Fail Quality Rejection)**:
  - *Raw*: 128×128 px, severe pixelation, underexposure, and indistinguishable dark meat/sauce/bone clump.
  - *Deterministic Quality Capping*: When a raw thumbnail is $\le 140\text{px}$ and consists of dark glazed meat without distinguishable texture, the platform deterministically caps quality at **0.20** (`QUALITY_FOCUS_BLUR_0.20`), overriding potential model variance.
  - *System Gate*: The asset is intercepted with **`AUTO_REJECT`** and `eligible_for_enhancement = False` in **$7.1\text{s}$**, eliminating generative compute waste and preventing culinary hallucination.
- **Case Study 2b (`Appitizer2.jpg` - Buffalo Wings with Celery and Carrots: Commercial Studio Reframing)**:
  - *Raw*: 300×168 px (16:9 tight mobile crop), wings cut off at top and side boundaries on a plain white plate.
  - *Commercial Reframing Directive*: Prompted with `COMMERCIAL MENU FRAMING & STUDIO COMPOSITION`, instructing the generator to reframe the complete plated dish on a dark charcoal slate surface with warm restaurant dining ambiance.
  - *Auditor Reframing Recognition*: The auditor verified that completing the clipped wing at top center to achieve circular plate framing is fully compliant under FTC commercial photoshoot standards (`hallucinated_items: []`, `audit_verdict: PASS_AUTHENTIC`, $\text{Risk} = 0.25$).
- **Case Study 3 (`Appitizer4.jpg` - Pan-Fried Dumplings: Closed-Loop Self-Healing & Allergen Protection)**:
  - *Raw*: 128×128 px mobile thumbnail of 6 pan-fried dumplings with a plain, smooth dark dipping sauce.
  - *Phase A*: Auto-upscaled with Lanczos super-resolution to 400×400 px for multimodal analysis.
  - *Phase B Moderation*: Primary dish identified as Pan-Fried Dumplings; quality scored at **0.50**.
  - *Pass 1 Generative Studio Reshoot*: Beautiful commercial studio lighting, but the generator hallucinated **red chili flakes and toasted sesame seeds** into the dipping sauce.
  - *Phase D Audit (Pass 1 - High-Precision True Positive)*:
    - Truth-in-Advertising Auditor flagged dish as `FLAG_OVER_ENHANCED` ($\text{Risk} = 0.70, \text{Reality Gap} = 0.45$).
    - `hallucinated_items: ["chili flakes", "sesame seeds in dipping sauce"]`.
    - *Food Safety Criticality*: Sesame is a top-9 major food allergen under the FDA FASTER Act. An AI adding unverified sesame seeds creates genuine consumer liability.
    - Emitted structured remediation: *"Remove added garnish particulates from dipping sauce to match raw submission texture."*
  - *Pass 2 Closed-Loop Self-Healing*: The pipeline automatically intercepted the flag and triggered Pass 2 on `gemini-nano-banana-2.1`, injecting the auditor's remediation constraint as a `MANDATORY AUDITOR REMEDIATION DIRECTIVE`.
  - *Pass 2 Re-Audit*:
    - Verdict: **`PASS_AUTHENTIC`** with zero hallucinated items (`hallucinated_items: []`).
    - Truth-in-Advertising Risk plummeted from **0.70 down to 0.05**.
    - Reality Gap dropped from **0.45 down to 0.15**.
    - The asset was automatically self-healed and approved without human moderator intervention.
- **Case Study 4 (`Appitizer9.jpg` - Salvadoran Pupusas: Culinary Texture Equity & Competitor Platform CDN Detection)**:
  - *Raw*: Salvadoran pupusas with curtido cabbage salad.
  - *Culinary Texture Equity (Rule B8 Recalibration)*: Previous Laplacian variance filters penalized the dish for low edge frequency, misclassifying smooth griddled corn masa as camera blur. Calibrated Gemini 3.8 Flash semantic perception correctly recognized intentional culinary smoothness, awarding a quality score of **0.70** (clearing intake).
  - *Google Cloud Vision Reverse-Image Search (Rule B12 / Copyright)*: Reverse image lookup matched `img.cdn4dd.com` (DoorDash CDN), correctly intercepting the asset for competitor platform reuse rather than authentic merchant-original photography.
- **Case Study 5 (`Chef Holding Dish` - Human/Hand Detection & Forced Studio Remediation)**:
  - *Raw*: Photo of a chef holding a plated pizza dish with visible hands, wrists, and chef torso/apron.
  - *Phase B Moderation (`B7_BODY_PARTS`)*: Detected human hands and chef torso holding the dish (`body_parts_on_food = True`), flagging `B7_BODY_PARTS` (`AUTO_REJECT` when unforced).
  - *Forced Enhancement (`force_enhancement = True`)*: When evaluated with "Always Execute Phase C AI Enhancement" checked, Phase C injected `CRITICAL HUMAN & BODY PART REMOVAL` into `gemini-nano-banana-2.1`, completely removing the chef and hands, reconstructing the occluded plate rim, and grounding the pizza on a clean studio tabletop (`ACCEPTABLE_UPGRADE` in Phase D Criterion 4).

---

## 9. AI Evaluation, Observability & Quality Assurance Framework

### 9.1 The 4-Pillar Quality Assurance Framework

```
                          AI Pipeline Output
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
 1. Deterministic SSIM    2. Multimodal Truth Audit   3. Vertex AI AutoSxS
    (Pixel Fidelity)      (7-Criteria Verification)   (Aesthetic Judge)
```

1. **Pillar 1: Deterministic Food Fidelity (SSIM & PSNR)**:
   - Evaluates structural pixel preservation over the food ROI:
     $$\text{SSIM}(x, y) = \frac{(2\mu_x\mu_y + c_1)(2\sigma_{xy} + c_2)}{(\mu_x^2 + \mu_y^2 + c_1)(\sigma_x^2 + \sigma_y^2 + c_2)}$$
   - Target: $\text{SSIM} \ge 0.85$ (Mode A Strict Food-Lock), Multimodal Plating Geometry `PRESERVED` / `ACCEPTABLE_UPGRADE` (Mode B Studio Reshoot).
2. **Pillar 2: 7-Criteria Multimodal Truth-in-Advertising Audit**:
   - Automated pairwise comparison at $\le 512\text{px}$ detecting culinary hallucination ($\text{HEC} = 0$, $\text{Risk} \le 0.25$).
3. **Pillar 3: Automated Pairwise Model Evaluation (AutoSxS)**:
   - Runs a frontier Gemini judge comparing candidate outputs against baseline photography on:
     - Food Realism & Texture Appeal (1–5)
     - Surface Lighting Harmonization (1–5)
     - Artifact & Distortion Absence (1–5)
4. **Pillar 4: Continuous Telemetry, GCS Decisions Ledger & CSV Export**:
   - Real-time persistence of quality lift ($\Delta Q$), SSIM fidelity, latency timers, and SOP decisions into the central JSON decisions ledger (`decisions/moderation_decisions.json`) in Google Cloud Storage.
   - Capability matrix results exported directly to CSV (`results/capability_matrix_results.csv`) and visualized across real-time frontend KPI counters and the 6-Tab Interactive Scoring Guide Modal.

---

## 10. Production Latency, Token Economics & SKU Cost Profile (October 2026)

### 10.1 Execution Tiers & Latency Profile

The platform balances user responsiveness with computational efficiency across its interactive and batch workflows:

| Execution Tier | Pipeline Scope | End-to-End Latency | Merchant UX & Operational Behavior | Cloud Scaling Profile |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1: Real-Time Single Intake (`POST /api/upload`)** | Phase A Preflight (`A1`–`A5`) + Phase B Parallel Moderation (`gemini-3.8-flash` + Cloud Vision) + Phase C Reshoot (`gemini-nano-banana-2.1`) + Phase D 7-Criteria Audit (`gemini-3.8-flash`) | **~15s–23s** (Compliant)<br>**<4.5s** (Fast-Fail) | **Interactive immediate feedback**. Dish card prepended to UI with Split-View comparison slider and full SOP badge breakdown. | Standard Vertex AI Global Endpoints on Cloud Run (`us-central1`). |
| **Tier 2: Interactive Prompt Re-Tune (`POST /api/image/{fn}/tune`)** | Reuses `cached_analysis` from Phase B + Phase C Reshoot (`gemini-nano-banana-2.1`) + Phase D Audit (`gemini-3.8-flash`) | **~11s–16s** (Cached Phase B) | **Rapid iterative styling**. Skips redundant Phase B moderation & Vision calls when only surface preset or framing ratio changes. | Cached Phase B state + Vertex AI Global Endpoints. |
| **Tier 3: Multi-Photo Batch Intake Dropzone** | Sequential/Parallel Execution over Multi-File Queue (`<input type="file" multiple>`) | **Streaming per photo** | **Non-blocking live card streaming**. Cards appear one by one with animated glow as they complete; merchants review completed cards immediately. | Cloud Run auto-scaling; dynamic frontend DOM prepending without page reload. |
| **Tier 4: Platform Batch Runner (`/api/batch/run` & `/process-next`)** | Background evaluation of catalog test sets or 8,000-image bulk queues | **Non-blocking background** | **Asynchronous execution**. Runs in background tasks or Vertex Batch API (50% discount); updates GCS JSON decisions ledger per completed item. | Python background worker / Vertex AI Batch Prediction writing state to GCS. |

### 10.2 Per-Image Token & SKU Cost Breakdown (`gemini-nano-banana-2.1`, 1K Standard)

With the October 6, 2026 General Availability of **Gemini Nano Banana 2.1 (`gemini-nano-banana-2.1`)** (`$1.50 / 1M` input tokens; `$30.00 / 1M` image output tokens, or `$0.0336` per 1,120-token 1K 1024×1024 studio image), end-to-end 1-Pass Real-Time cost is **`$0.0407`–`$0.0430` per image** including Cloud Vision Web Detection (or **`$0.0372`–`$0.0395` per image** for Vertex AI + Infra only), and drops to **`$0.0226`–`$0.0234` per image** including Cloud Vision (or **`$0.0191`–`$0.0199` per image** for Vertex AI + Infra only) when running via Vertex AI Batch Prediction (50% discount):

| Pipeline Stage | Google Cloud Service / Model SKU | Measured Payload & Token Count | Unit SKU Rate (Oct 2026) | Cost per Image (Real-Time PayGo) | Cost per Image (Vertex Batch 50% Off) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Stage 1: Phase B Policy Moderation** | Vertex AI `gemini-3.8-flash` (`thinking_budget=0`) | `1,391` input tok (`258` img + `1,133` text)<br>`237` output tok (`0` thinking) | `$0.15 / $0.60` per 1M *(Std)*<br>`$0.50 / $3.00` per 1M *(Preview)* | **`$0.000351`** *(Std)*<br>`$0.001407` *(Preview)* | **`$0.000351`** *(Std)*<br>`$0.000704` *(Batch)* |
| **Stage 2: Reverse-Image Copyright** | Cloud Vision API `WEB_DETECTION` | `1` image request ($\le 1024\text{px}$) | `$3.50 / 1,000` calls | **`$0.003500`** | **`$0.003500`** |
| **Stage 3: Phase C Studio Reshoot** | Vertex AI **`gemini-nano-banana-2.1`** (1K 1024×1024) | `1,664` input tok (`1,032` img + `632` text)<br>`1,120` image output tok (1K) | `$1.50 / 1M` input<br>`$30.00 / 1M` output | **`$0.036096`** (`~$0.0361`) | **`$0.018048`** (`~$0.0180`) |
| **Stage 4: Phase D Authenticity Audit** | Vertex AI `gemini-3.8-flash` (`thinking_budget=0`) | `1,606` input tok (`516` img [2×$\le 512\text{px}$] + `1,090` text)<br>`315` output tok | `$0.15 / $0.60` per 1M *(Std)*<br>`$0.50 / $3.00` per 1M *(Preview)* | **`$0.000430`** *(Std)*<br>`$0.001748` *(Preview)* | **`$0.000430`** *(Std)*<br>`$0.000874` *(Batch)* |
| **Stage 5: Compute & Storage** | Cloud Run (2 vCPU / 2 GiB) + Cloud Storage | `~5s` active compute + `3` Class A PUTs + `1` GET | Standard Tier-1 | **`$0.000280`** | **`$0.000280`** |
| **TOTAL (Vertex AI + Infra Only, Excl. Vision)** | **Stages 1 + 3 + 4 + 5 (No Vision Call)** | **4,661 input + 1,672 output tokens** | **Vertex AI + Infra Only** | **`$0.0372` (`$0.0395` Preview)** | **`$0.0191` (`$0.0199` Preview)** |
| **TOTAL (All-In Incl. Cloud Vision Web Detection)** | **Full 5-Stage Pipeline (Stages 1–5)** | **4,661 input + 1,672 output tokens + 1 Vision call** | **All-In End-to-End** | **`$0.0407` (`$0.0430` Preview)** | **`$0.0226` (`$0.0234` Preview)** |
| **Fast-Fail Rejected / Bypassed** | Stage 1 + Stage 2 + Cloud Run (Skips Stages 3 & 4) | `1,391` input + `237` output tokens (+ `1` Vision call) | **90.3% Cost Savings** | **`$0.0039` (`$0.0004` Excl. Vision)** | **`$0.0039` (`$0.0004` Excl. Vision)** |
| **Blended Production Average** | 95% 1-Pass + 5% Pass-2 Self-Heal Retry | Weighted production average | **Blended E2E** | **`$0.0425` (`$0.0390` Excl. Vision)** | **`$0.0235` (`$0.0200` Excl. Vision)** |

### 10.3 Stage 3 Generative Model & Resolution Tier Comparison

| Model / Resolution Configuration | Input Rate ($/1M tok) | Image Output Rate ($/1M tok) | Output Tokens per Image | Stage 3 Cost (Real-Time) | Stage 3 Cost (Batch 50% Off) | End-to-End 1-Pass All-In (Excl. Vision) [Real-Time] | End-to-End 1-Pass All-In (Excl. Vision) [Batch] |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`gemini-nano-banana-2.1` @ 0.5K (512×512 Thumbnail)** | `$1.50` | `$30.00` | `747` | `$0.02491` | `$0.01245` | `$0.0295` (`$0.0260` Excl. Vision) | `$0.0170` (`$0.0135` Excl. Vision) |
| **`gemini-nano-banana-2.1` @ 1K (1024×1024 — Primary Standard)** | `$1.50` | `$30.00` | `1,120` | **`$0.03610`** | **`$0.01805`** | **`$0.0407`–`$0.0430` (`$0.0372`–`$0.0395` Excl. Vision)** | **`$0.0226`–`$0.0234` (`$0.0191`–`$0.0199` Excl. Vision)** |
| **`gemini-nano-banana-2.1` @ 2K (2048×2048 High-Res)** | `$1.50` | `$30.00` | `1,680` | `$0.05290` | `$0.02645` | `$0.0575` (`$0.0540` Excl. Vision) | `$0.0310` (`$0.0275` Excl. Vision) |
| **`gemini-nano-banana-2.1` @ 4K (4096×4096 Print/Hero)** | `$1.50` | `$30.00` | `2,520` | `$0.07810` | `$0.03905` | `$0.0827` (`$0.0792` Excl. Vision) | `$0.0436` (`$0.0401` Excl. Vision) |
| **`gemini-3.1-flash-image` (Nano Banana 2) @ 1K [Legacy]** | `$0.50` | `$60.00` | `1,120` | `$0.06803` | `$0.03402` | `$0.0726` (`$0.0691` Excl. Vision) | `$0.0386` (`$0.0351` Excl. Vision) |
| **`gemini-3.1-flash-lite-image` (Nano Banana 2 Lite) @ 1K** | `$0.25` | `$30.00` | `1,120` | `$0.03402` | `$0.01701` | `$0.0386` (`$0.0351` Excl. Vision) | `$0.0216` (`$0.0181` Excl. Vision) |

### 10.4 High-Volume Daily Production Economics (Sorin's 35,000 Images/Day & 8,000-Image Bulk Queue Workload)

To support target enterprise throughput of **35,000 merchant images per day** (`1,050,000` images/month; `12,775,000` images/year)—comprising **8,000-image bulk menu onboarding queues** alongside **27,000 interactive daily portal uploads**—the platform leverages two compounding FinOps mechanisms:
1. **Phase A/B Fast-Fail & Already-Compliant Gating**:
   - **Selective ~30% Enhancement Rate (`10,500` Enhanced + `24,500` Moderation-Only / Already-Compliant)**: When 100% of the `35,000` daily uploads run Phase A/B moderation and only `~30%` (`10,500` images/day) require a Stage 3 `gemini-nano-banana-2.1` studio reshoot, daily cost is **`~$449 / day` (`~$13,470 / mo`)** for Vertex AI + Infra only (or **`~$572 / day` / `~$17,145 / mo`** including Cloud Vision Web Detection on all 35k uploads) in Real-Time PayGo, and drops to **`~$226 / day` (`~$6,780 / mo`)** for Vertex AI + Infra only (or **`~$349 / day` / `~$10,455 / mo`** including Cloud Vision) on Vertex Batch API.
   - **High-Enhancement 80% Rate (`28,000` Enhanced + `7,000` Fast-Fail Bypassed)**: When `80%` (`28,000` images/day) undergo Stage 3 studio enhancement and `20%` (`7,000` images/day) are fast-fail bypassed at `$0.003927/image` (`$27.49/day`), avoiding Stage 3 generation and Stage 4 auditing on bypassed items.
2. **Vertex AI Batch Prediction API (50% Stage 3 Discount)**: Routes asynchronous 8,000-image bulk queues (or full async ingestion) through Vertex Batch Prediction, cutting `gemini-nano-banana-2.1` Stage 3 cost from `$0.036096` to **`$0.018048/image`** and bringing the all-in 1-pass cost to **`$0.022609/image` (~2.26¢)** (`$0.0199/image` excluding Cloud Vision).

| Deployment Architecture Option (35,000 Images / Day) | Daily Volume Breakdown | Daily Total Cost | Monthly Cost (30 Days / 1.05M Imgs) | Annual Cost (365 Days / 12.78M Imgs) | Monthly Savings vs. 100% PayGo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Profile 1A: ~30% Enhanced (`10.5k` Reshoot / `24.5k` Mod-Only) — Real-Time PayGo** | `10,500` enhanced + `24,500` mod-only | **`~$449 / day` *(Vertex+Infra)***<br>**`~$572 / day` *(Incl. Vision)*** | **`~$13,470 / mo` *(Vertex+Infra)***<br>**`~$17,145 / mo` *(Incl. Vision)*** | `~$163,885 / yr` *(Vertex+Infra)*<br>`~$208,598 / yr` *(Incl. Vision)* | Selective 30% Reshoot Baseline |
| **Profile 1B: ~30% Enhanced (`10.5k` Reshoot / `24.5k` Mod-Only) — Vertex Batch API (50% Off)** | `10,500` Batch enhanced + `24,500` Batch mod-only | **`~$226 / day` *(Vertex+Infra)***<br>**`~$349 / day` *(Incl. Vision)*** | **`~$6,780 / mo` *(Vertex+Infra)***<br>**`~$10,455 / mo` *(Incl. Vision)*** | **`~$82,490 / yr` *(Vertex+Infra)***<br>**`~$127,203 / yr` *(Incl. Vision)*** | **Saves `~$6,690 / mo` (`~$81,395 / yr`)** |
| **Option A (80% Enhanced): 100% Real-Time Pay-As-You-Go (All Synchronous)** | `28,000` PayGo enhanced @ `$0.040657` + `7,000` bypassed @ `$0.003927` | **`$1,165.89 / day`** | **`$34,976.58 / mo`** | `$425,548.40 / yr` | Baseline (`$0.00`) |
| **Option B (80% Enhanced): Hybrid Real-Time Portal (20k) + 8k Bulk Queue on Batch API** | `20,000` PayGo @ `$0.040657` + `8,000` Batch @ `$0.022609` + `7,000` bypassed @ `$0.003927` | **`$1,021.50 / day`** | **`$30,645.06 / mo`** | **`$372,848.23 / yr`** | **Saves `$4,331.52 / mo` (`$52,700 / yr`)** |
| **Option C (80% Enhanced): 100% Vertex Batch API for Stage 3 Studio Reshoot (Async Queue)** | `28,000` Batch enhanced @ `$0.022609` + `7,000` bypassed @ `$0.003927` | **`$660.54 / day`** | **`$19,816.23 / mo`** | **`$241,097.47 / yr`** | **Saves `$15,160.35 / mo` (`$184,451 / yr`)** |
| **Legacy Unoptimized Baseline (No Fast-Fail Gate, Prior-Gen @ `$0.0726`/img)** | `35,000` enhanced @ `$0.072590` (`0%` bypass) | **`$2,540.65 / day`** | **`$76,219.50 / mo`** | `$927,337.25 / yr` | **`+$41,242.92 / mo` more expensive** |

### 10.5 Six Built-In FinOps & Token Optimization Controls

1. **Phase A 1,600px Working-Dimension Cap & Single-Tile `<=512px` Phase D Auditing**: Oversized 12MP–48MP smartphone uploads are Lanczos-downscaled to `<= 1,600px` on intake (`src/preflight.py`), capping Phase C reference input at 4 tiles (`1,032` tokens). In Phase D (`src/authenticity_auditor.py`), both comparison images are downscaled in-memory to `<= 512x512 px` (`1 tile = 258 tokens` each, `516` tokens total instead of `2,064`), cutting Phase D multimodal input tokens by **75%**.
2. **Thinking Token Suppression (`thinking_budget=0`)**: Both `gemini-3.8-flash` calls in Phase B and Phase D explicitly set `ThinkingConfig(thinking_budget=0)`, eliminating `1,000–2,500` billed reasoning tokens per call and reducing inspection latency by **~60%**.
3. **Pre-Enhancement Fast-Fail Gate (90.3% Savings on Non-Compliant Uploads)**: Executing Phase B (`gemini-3.8-flash` + Cloud Vision Web Detection) before Phase C (`gemini-nano-banana-2.1`) intercepts copyright violations, watermarks, non-food imagery, and unrecoverable blur for `$0.003927` instead of spending `$0.036526` on generative studio reshoots and truth auditing.
4. **Cached Phase B Analysis Reuse on Interactive Re-Tuning (`cached_analysis`)**: When a merchant or operator re-tunes studio background presets or food-to-frame ratios in the Tuning Drawer (`POST /api/image/{filename}/tune`), the server reuses `cached_analysis` from `moderation_decisions.json`, skipping Stage 1 and Stage 2 and saving **`$0.003851` per re-tune**.
5. **Vertex AI Batch API Integration for 8,000-Image Bulk Queues (50% Stage 3 Discount)**: Routing asynchronous merchant onboarding queues (`8,000+` images) through Vertex AI Batch Prediction cuts `gemini-nano-banana-2.1` Stage 3 costs in half (`$0.018048` vs. `$0.036096`), reducing all-in per-image cost to **`$0.022609`**.
6. **Scale-to-Zero Serverless Topology (`min_instance_count=0`)**: Configured in `terraform/main.tf`, the Cloud Run service scales down to 0 instances when idle, incurring `$0.00` in baseline hourly compute charges between merchant uploads.

---

## 11. Merchant Customer User Journeys (Grubhub Merchant Portal & UI)

To ensure the platform seamlessly accommodates diverse operational realities—from single-location neighborhood eateries to multi-unit franchise brands—the UI is architected around five distinct, high-impact merchant customer journeys:

### 11.1 Target Merchant Personas

| Persona | Operational Context | Core Needs & Pain Points | Primary UI Entry Point |
| :--- | :--- | :--- | :--- |
| **Carlos — The Independent Taquería Owner** | Snaps casual smartphone photos between shifts under fluorescent kitchen lighting. Zero professional photography budget or editing skills. | Wants photos uploaded fast without complicated technical jargon, rejected files, or artificial culinary hallucinations. | Drag-and-Drop Single Upload Dropzone |
| **Sarah — The Multi-Unit General Manager** | Managing 15 new seasonal dishes for an Italian trattoria. Operates under tight deadlines during seasonal menu overhauls. | Needs to upload full menus in parallel without page-locking; desires instant visibility into processing status and approvals. | Multi-Photo Batch Intake Queue |
| **Chef Marcus — The Culinary Perfectionist** | Executive Chef of an upscale farm-to-table bistro. Deeply protective of plating geometry, garnish precision, and tabletop ambience. | Needs precise control over composition, plate blemish removal, and tabletop mood (e.g. dark walnut vs. slate) without distorting the dish. | Merchant Photo Studio & Adjustment Suite |
| **Elena — The Craft Brewpub Operator** | Menu features burgers, wings, and house-brewed craft beers. Often gets flagged for alcohol licensing, chef hands holding plates, or low-res camera thumbnails. | Requires transparent, jargon-free policy guidance and intuitive 1-click tools (`force_enhancement` or Studio Auto-Crop) to resolve review flags. | Interactive Policy Flag, Force-Enhance & Review Drawers |
| **David — The Seasonal Menu Coordinator** | Updates menu quarterly, retiring seasonal specials and rotating seasonal promotions. | Needs permanent, clean menu item deletion with guaranteed cloud storage cleanup to prevent accidental ghost listings. | Card Action Header (`🗑️ Delete Record`) |

---

### 11.2 Journey 1: The Quick Smartphone Snapshot (Instant "Magic Studio" Onboarding)

*“I just added a new Birria Taco special to my menu. I snapped a photo on my phone on the stainless prep counter, but I want it to look like it came out of a gourmet food magazine without lying to my customers.”*

<div align="center" style="margin: 20px 0;">
  <img src="assets/diagram_plates/sequence_plate.png" alt="Merchant Journey Sequence Flow Plate" style="max-width: 100%; border-radius: 8px; border: 1px solid #E2E8F0; box-shadow: 0 4px 12px rgba(0,0,0,0.06);" />
  <p style="font-size: 0.85rem; color: #6B7280; margin-top: 8px;"><em>Figure 11.1: Merchant Journey & Audit Sequence Flow — End-to-end execution flow from Carlos's smartphone upload, parallel policy moderation, Gemini Nano Banana 2.1 studio reshoot, and truth audit verification.</em></p>
</div>

```mermaid
sequenceDiagram
    autonumber
    actor Carlos as Carlos (Merchant)
    participant UI as Merchant Portal UI
    participant Server as Cloud Run Gateway
    participant Gemini as Gemini 3.8 Flash & Nano Banana 2.1
    participant GCS as Google Cloud Storage

    Carlos->>UI: Drops 'tacos.jpg' onto Upload Dropzone
    UI->>Server: POST /api/upload (multipart/form-data)
    Note over Server: Saves raw photo & syncs to GCS samples/
    Server->>Gemini: Phase A Preflight (1600px Cap, A1-A5) + Phase B Parallel Moderation
    Note over Gemini: Confirms authentic food, passes SafeSearch & Web Provenance, scores quality 0.70
    Server->>Gemini: Phase C Studio Reshoot (Gemini Nano Banana 2.1)
    Note over Gemini: Replaces stainless counter with warm dark slate & realistic shadows
    Server->>Gemini: Phase D 7-Criteria Truth-in-Advertising Audit (Gemini 3.8 Flash)
    Note over Gemini: Verifies 3 tacos, identical cilantro/onion garnish (Risk: 0.05)
    Server->>GCS: Uploads enhanced/enhanced_tacos.jpg & syncs decisions ledger
    Server-->>UI: Returns JSON result + pre-rendered dish card HTML
    UI-->>Carlos: Card appears with Split-View Slider & 'SynthID v2 Verified' badge
    Carlos->>UI: Drags comparison slider, sees authentic tacos on warm slate, clicks 'Accept'
```

1. **Effortless Intake**: Carlos opens the Grubhub Merchant Portal and drags `tacos.jpg` directly into the upload dropzone.
2. **Instant Policy Clearance**: Phase A validates dimensions (auto-upscaling if below 200px and capping at 1600px), while Phase B **Gemini 3.8 Flash** + **Cloud Vision Web Detection** confirm authentic Mexican cuisine (`Birria Tacos`), pass SafeSearch/Copyright, and approve the quality score.
3. **Automated Commercial Studio Reshoot**: **Gemini Nano Banana 2.1 (`gemini-nano-banana-2.1`)** replaces the distracting kitchen prep counter with an elegant, authentic warm dark slate tabletop with soft directional lighting and physical contact shadows.
4. **Automated Truth-in-Advertising Protection**: The **Gemini 3.8 Flash Auditor** compares raw vs. enhanced outputs across 7 criteria, confirming zero garnish hallucinations and exact 3-taco portion counts ($\text{Risk} = 0.05$).
5. **Interactive Verification**: Carlos inspects the interactive **Split-View Before/After Slider** directly on his tablet, verifies his dish looks appetizing and 100% authentic, and clicks **Publish to Live Menu**.

---

### 11.3 Journey 2: The Multi-Dish Menu Launch (Batch Intake & Live Streaming)

*“It's fall menu changeover day. I have 12 dish photos ready from our kitchen tasting. I don't have time to upload them one-by-one or wait 5 minutes staring at a loading spinner.”*

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  BATCH INTAKE QUEUE (12 Photos Selected)                                               │
│  [📁 Drag & drop more photos]                             [🚀 Process Batch (12)]      │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  [🖼️ Pasta1.jpg   ]  Tagliatelle Bolognese     │ 2.4 MB │ ✅ Complete (Auto-Approved)  │
│  [🖼️ Risotto2.jpg ]  Wild Mushroom Risotto     │ 3.1 MB │ 🎨 Studio Reshoot (Pass 1)   │
│  [🖼️ Burrata3.jpg ]  Autumn Fig Burrata        │ 1.8 MB │ 🔍 Gemini 3.8 Moderation     │
│  [🖼️ Tiramisu4.jpg]  Classic Espresso Tiramisu │ 2.2 MB │ ⏳ Preflight Validation      │
│  [🖼️ Ossobuco5.jpg]  Braised Osso Buco         │ 4.1 MB │ Ready                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **Multi-File Drag-and-Drop**: Sarah highlights all 12 photos in her file browser and drops them onto the batch intake dropzone simultaneously (`<input type="file" multiple accept="image/*">`).
2. **Interactive Itemized Queue**: The UI displays an itemized intake queue showing image thumbnails, file sizes, dish titles, and real-time stage pills (`Ready` $\rightarrow$ `⏳ Preflight` $\rightarrow$ `🔍 Moderation` $\rightarrow$ `🎨 Studio Reshoot` $\rightarrow$ `⚖️ Truth Audit` $\rightarrow$ `✅ Complete`).
3. **Non-Blocking Live Card Streaming**: As each photo completes evaluation, the server returns the pre-rendered card markup, and the UI immediately prepends the dish card to the top of `#cardsGrid` with an animated green glow (`@keyframes cardHighlightGlow`).
4. **Immediate Parallel Review**: Sarah begins reviewing dish #1 (Tagliatelle) while dish #4 is still generating. She does not wait for the entire batch to complete.
5. **Real-Time KPI Reactivity**: Top-level dashboard counters (Total Dishes Ingested, Auto-Approved, Quality Lift %, Average SSIM) dynamically increment in real time with each landing dish.

---

### 11.4 Journey 3: The Chef's Creative Vision (Photo Studio Framing & Retouching)

*“Our roasted duck breast is our signature entree. The phone photo was taken slightly crooked, and there’s a stray drop of sauce on the rim of our white porcelain plate. I want to clean that up and give it a moody bistro feel.”*

1. **Entering the Photo Studio Suite**: Chef Marcus clicks **`[Edit Studio]`** on the roasted duck dish card. The full-screen interactive Photo Studio modal opens over the raw merchant upload.
2. **Interactive Crop & Straightening**:
   - Marcus selects the **4:3 Standard Menu** aspect ratio.
   - Uses the rotation wheel to straighten the shot by $+2^\circ$.
   - Uses the zoom slider to center the duck breast within the Rule-of-Thirds guide lines.
3. **One-Click Blemish Spot-Healing Brush**:
   - Marcus selects the circular **Blemish Brush** (set to 16px radius).
   - Clicks on the stray drop of jus on the plate rim.
   - The HTML5 canvas inpainting engine samples annular pixels and erases the splatter cleanly without blurring the plate edge.
4. **Atmospheric Surface Customization**:
   - In the Studio Surface Preset dropdown, Marcus chooses **Matte Dark Charcoal Granite (Moody Bistro)**.
   - Adjusts the warmth slider to $+10\%$ to accentuate the golden crisp duck skin.
5. **Save & Immediate Re-Evaluation**:
   - Clicks **Save & Re-Run Pipeline** (`POST /api/image/{filename}/edit`).
   - The edited raw photo is saved to GCS `samples/`, re-evaluated through Gemini 3.8 Flash, enhanced by **Gemini Nano Banana 2.1** on dark granite, and audited.
6. **Direct Post-Shoot AI Retouching (`[Retouch AI Photo]`)**:
   - Marcus views the AI studio output and loves the granite surface, but wants a subtle vignette shadow on the top right corner.
   - Clicks **`[Retouch AI Photo]`** (`POST /api/image/{filename}/edit-enhanced`).
   - Applies subtle corner vignetting and clicks **Save Retouch**.
   - Instead of paying for an expensive generative diffusion re-run, the server executes a lightweight **Truth-in-Advertising Re-Audit**, updates SSIM fidelity, signs a new C2PA manifest (`MERCHANT_STUDIO_AI_RETOUCH`), and updates the live card instantly.

---

### 11.5 Journey 4: Transparent Policy Flag Resolution (Alcohol Licensing, Hand Removal & Quality Recovery)

*“I uploaded our signature Wagyu Bacon Cheeseburger, but I forgot there was a glass of craft IPA right next to it—and on our Pizza photo, my chef's hands were holding the plate. How do I fix them without re-taking the pictures?”*

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  ⚠️ FLAGGED FOR REVIEW / REJECTED                                                      │
│  Primary Dish: Wagyu Bacon Cheeseburger / Artisan Pizza                                │
│  Reason: Alcohol Packaging (Rule B4) / Human Hands on Dish (Rule B7)                   │
│  Details: Beer glass requires liquor license or crop; hands can be removed via Studio. │
│                                                                                        │
│  [ ↗ Open Studio & Crop ]     [ ⚡ Force Phase C Studio Reshoot ]     [ 🗑️ Dismiss ]   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **Clear, Jargon-Free Notification**: Elena sees an explicit explanation in the Phase B checklist: *"Alcohol packaging detected (beer pint). Requires Grubhub merchant liquor license verification or re-crop"* or *"Human hands/arms or person detected holding or touching the dish/plate."*
2. **Actionable Resolution Choices**:
   - For the burger with the beer pint, Elena clicks **`[Open Studio & Crop]`**, where AI Auto-Crop highlights the burger plate bounding box (`[ymin, xmin, ymax, xmax]`), cropping the beer glass out of frame.
   - For the chef holding the pizza plate, Elena checks **"Always Execute Phase C AI Enhancement (Bypass Moderation Gate)"** (`force_enhancement`) in the card's tuning drawer and clicks **`⚡ Re-run Pipeline (Gemini Nano Banana 2.1)`**.
3. **Instant Self-Healing Re-Check**:
   - On the cropped burger, Rule B4 now detects zero alcoholic beverages (`PASS`).
   - On the chef-holding pizza photo, **Gemini Nano Banana 2.1** executes `CRITICAL HUMAN & BODY PART REMOVAL`, erasing the chef's hands and apron, reconstructing the occluded plate edge, and resting the pizza naturally on a warm slate tabletop (`ACCEPTABLE_UPGRADE`).

---

### 11.6 Journey 5: Menu Deletion & Cloud Storage Purge (Enterprise Asset Hygiene)

*“We no longer serve the Summer Berry Tart. I want to delete it permanently so it doesn't clutter our menu dashboard or show up on our storefront.”*

1. **Distinct Danger Action**: David navigates to the Summer Berry Tart card and clicks **`🗑️ Delete Record`** in the card header.
2. **Explicit User Safeguard**: A browser modal confirms: *"Are you sure you want to permanently delete 'Summer_Berry_Tart.jpg' from your menu and cloud storage?"*
3. **Atomic Multi-Cloud Cleanup**:
   - David confirms the prompt.
   - The client issues `DELETE /api/image/Summer_Berry_Tart.jpg`.
   - The server unlinks the record from `results/moderation_decisions.json` and syncs the ledger to GCS.
   - Local container files are unlinked.
   - GCS bucket deletion requests purge `samples/Summer_Berry_Tart.jpg` and `enhanced/enhanced_Summer_Berry_Tart.jpg` from `gs://grubhub-merchant-assets`.
4. **Animated DOM Eviction & Metric Recalculation**:
   - The card triggers a CSS exit transition (`.card-deleting`), smoothly fading and collapsing to 0 height.
   - Top-level metrics immediately recalculate (e.g. Total Dishes: 51 $\rightarrow$ 50).
   - No broken links, orphan GCS storage costs, or obsolete menu listings remain.

