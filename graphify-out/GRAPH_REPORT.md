# Graph Report - .  (2026-10-09)

## Corpus Check
- Large corpus: 655 files · ~5,472,696 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder.

## Summary
- 195 nodes · 419 edges · 13 communities (12 shown, 1 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 6 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Stage 1-3 Vision Moderation & Generative Enhancer
- Platform Architecture, PRD & Dual-Basis Economics
- Batch Evaluation Runner & Interactive PRD Builder
- FastAPI Workbench GET Routes & Endpoints
- Mask-Protected Compositor & Fidelity Evaluator
- Decisions Ledger & Benchmark Re-Evaluator
- HTML Dashboard & Capability Matrix Report Generator
- Google Cloud Storage (GCS) Persistence Adapter
- 5-Stage Pipeline Orchestrator & Preflight Gate
- Real-Time Upload & Interactive Tuning Endpoints
- Merchant Canvas Retouching & Manual Adjustments
- Stage 4 Truth-in-Advertising & Hallucination Auditor
- PDF & Document Utilities (12)

## God Nodes (most connected - your core abstractions)
1. `process_single_image()` - 23 edges
2. `load_all_decisions()` - 15 edges
3. `upload_file_to_gcs()` - 14 edges
4. `enhance_menu_image()` - 12 edges
5. `inspect_image()` - 12 edges
6. `save_decisions_list()` - 12 edges
7. `edit_and_update_enhanced_image()` - 12 edges
8. `audit_truth_in_advertising()` - 11 edges
9. `run_batch()` - 11 edges
10. `generate_reports()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Phase D: 7-Criteria Authenticity Audit & Self-Healing Loop` --implemented_by--> `audit_truth_in_advertising()`  [EXTRACTED]
  PRD_MERCHANT_MENU_IMAGE_PLATFORM.md → src/authenticity_auditor.py
- `Phase C: Commercial Studio Reshoot & Handheld Removal` --implemented_by--> `enhance_menu_image()`  [EXTRACTED]
  PRD_MERCHANT_MENU_IMAGE_PLATFORM.md → src/enhancer.py
- `Phase B: Parallel 12-Rule SOP Moderation & B7/B8 Checks` --implemented_by--> `inspect_image()`  [EXTRACTED]
  PRD_MERCHANT_MENU_IMAGE_PLATFORM.md → src/moderator.py
- `Terraform: Cloud Run + GCS + Secret Manager` --configures_env_var--> `Gemini Nano Banana 2.1 (gemini-nano-banana-2.1)`  [EXTRACTED]
  terraform/main.tf → PRD_MERCHANT_MENU_IMAGE_PLATFORM.md
- `Interactive Diagram: System Architecture` --depicts--> `Gemini Nano Banana 2.1 (gemini-nano-banana-2.1)`  [EXTRACTED]
  interactive_prd/diagrams/architecture.json → PRD_MERCHANT_MENU_IMAGE_PLATFORM.md

## Import Cycles
- None detected.

## Communities (13 total, 1 thin omitted)

### Community 0 - "Stage 1-3 Vision Moderation & Generative Enhancer"
Cohesion: 0.08
Nodes (39): Truth-in-Advertising & Anti-Hallucination Auditor powered by Gemini 3.0+ models., Configuration and constants for the Grubhub Merchant Menu Image Platform.…, enhance_menu_image(), get_genai_client(), Any, Client, Image, Image enhancement engine powered by Gemini 3.0+ models with Truth-in-… (+31 more)

### Community 1 - "Platform Architecture, PRD & Dual-Basis Economics"
Cohesion: 0.13
Nodes (20): Interactive Diagram: System Architecture, Interactive Diagram: 5-Stage Ingestion Dataflow, Interactive Diagram: Merchant & Self-Healing Sequence, PRD: Merchant Menu Image Platform v5.2, README: Architecture & Quickstart, Gemini 3.8 Flash (gemini-3.8-flash), Gemini Nano Banana 2.1 (gemini-nano-banana-2.1), Imagen 3 Capability (imagen-3.0-capability-001) (+12 more)

### Community 2 - "Batch Evaluation Runner & Interactive PRD Builder"
Cohesion: 0.14
Nodes (19): BackgroundTasks, get_unprocessed_images(), load_existing_decisions(), main(), Any, Path, Batch Evaluation Runner executing across sample photos with live progress…, Loads all decisions from JSON ledger keyed by filename. (+11 more)

### Community 3 - "FastAPI Workbench GET Routes & Endpoints"
Cohesion: 0.12
Nodes (17): get, get_dashboard(), get_enhanced_image(), get_image_card_html(), get_image_crop_hints(), get_interactive_prd(), get_prd_pdf(), get_sample_image() (+9 more)

### Community 4 - "Mask-Protected Compositor & Fidelity Evaluator"
Cohesion: 0.19
Nodes (12): composite_food_onto_studio_background(), extract_food_roi(), Image, Mask-Protected Compositor module enforcing 100% real-food pixel integrity., Composites the untouched food pixels from original_img onto studio_bg,…, Extracts the food/dish bounding box in pixel coordinates., calculate_quality_lift(), evaluate_food_fidelity() (+4 more)

### Community 5 - "Decisions Ledger & Benchmark Re-Evaluator"
Cohesion: 0.24
Nodes (12): delete, main(), Reruns the 6 core benchmark images through the latest pipeline with self-…, Uploads updated moderation_decisions.json to GCS., sync_to_gcs(), delete_image_record(), get_single_image_details(), load_all_decisions() (+4 more)

### Community 6 - "HTML Dashboard & Capability Matrix Report Generator"
Cohesion: 0.23
Nodes (11): on_event, generate_html_dashboard(), generate_reports(), Any, Report Generator compiling JSON decisions, CSV capability matrix, and an…, Generates JSON, CSV, and visual HTML reports for the processed batch., Creates a standalone, interactive HTML dashboard with Before/After visual…, Renders the HTML markup for an individual dish evaluation card. (+3 more)

### Community 7 - "Google Cloud Storage (GCS) Persistence Adapter"
Cohesion: 0.26
Nodes (11): delete_file_from_gcs(), download_file_from_gcs(), get_storage_client(), Path, Google Cloud Storage (GCS) adapter for serverless asset persistence and…, Downloads an asset from GCS to local disk if it exists. Returns True if…, Synchronizes all decisions, raw sample images, and enhanced images from GCS.…, Downloads latest moderation_decisions.json from GCS if available. (+3 more)

### Community 8 - "5-Stage Pipeline Orchestrator & Preflight Gate"
Cohesion: 0.22
Nodes (10): Phase A: Deterministic Preflight & 1600px Cap (A1-A5), process_single_image(), Any, Path, Runs the entire ingestion, moderation, enhancement, and Truth-in-Advertising…, inspect_and_normalize_image(), Any, Image (+2 more)

### Community 9 - "Real-Time Upload & Interactive Tuning Endpoints"
Cohesion: 0.24
Nodes (10): post, Uploads a dish image or enhanced asset to GCS., upload_file_to_gcs(), edit_and_reevaluate_image(), Re-runs the pipeline with custom prompts or food ratio and updates the result…, Saves merchant manual adjustments (crop, straighten, rotate, resize,…, Accepts a new merchant menu photo, immediately runs real-time Phase A…, tune_image() (+2 more)

### Community 10 - "Merchant Canvas Retouching & Manual Adjustments"
Cohesion: 0.36
Nodes (7): BaseModel, edit_and_update_enhanced_image(), EditEnhancedImageRequest, EditImageRequest, FastAPI Local Workbench Server for interactive quality iteration, prompt…, Saves merchant manual retouching adjustments (crop, straighten, rotate,…, TuningRequest

### Community 11 - "Stage 4 Truth-in-Advertising & Hallucination Auditor"
Cohesion: 0.29
Nodes (7): audit_truth_in_advertising(), get_genai_client(), Any, Client, Image, Returns authenticated Vertex AI Gemini Client., Executes automated multimodal inspection using Gemini 3.0+ to detect any…

## Knowledge Gaps
- **1 isolated node(s):** `Imagen 3 Capability (imagen-3.0-capability-001)`
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `process_single_image()` connect `5-Stage Pipeline Orchestrator & Preflight Gate` to `Stage 1-3 Vision Moderation & Generative Enhancer`, `Batch Evaluation Runner & Interactive PRD Builder`, `Mask-Protected Compositor & Fidelity Evaluator`, `Decisions Ledger & Benchmark Re-Evaluator`, `Real-Time Upload & Interactive Tuning Endpoints`, `Merchant Canvas Retouching & Manual Adjustments`, `Stage 4 Truth-in-Advertising & Hallucination Auditor`?**
  _High betweenness centrality (0.223) - this node is a cross-community bridge._
- **Why does `PRD: Merchant Menu Image Platform v5.2` connect `Platform Architecture, PRD & Dual-Basis Economics` to `5-Stage Pipeline Orchestrator & Preflight Gate`?**
  _High betweenness centrality (0.131) - this node is a cross-community bridge._
- **Why does `enhance_menu_image()` connect `Stage 1-3 Vision Moderation & Generative Enhancer` to `5-Stage Pipeline Orchestrator & Preflight Gate`, `Platform Architecture, PRD & Dual-Basis Economics`, `Mask-Protected Compositor & Fidelity Evaluator`?**
  _High betweenness centrality (0.116) - this node is a cross-community bridge._
- **What connects `Imagen 3 Capability (imagen-3.0-capability-001)` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Stage 1-3 Vision Moderation & Generative Enhancer` be split into smaller, more focused modules?**
  _Cohesion score 0.0821256038647343 - nodes in this community are weakly interconnected._
- **Should `Platform Architecture, PRD & Dual-Basis Economics` be split into smaller, more focused modules?**
  _Cohesion score 0.13043478260869565 - nodes in this community are weakly interconnected._
- **Should `Batch Evaluation Runner & Interactive PRD Builder` be split into smaller, more focused modules?**
  _Cohesion score 0.14210526315789473 - nodes in this community are weakly interconnected._