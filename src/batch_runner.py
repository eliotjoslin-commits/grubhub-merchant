"""Batch Evaluation Runner executing across sample photos with live progress tracking and incremental ingestion."""

import json
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.config import SAMPLE_PHOTOS_DIR, REPORT_FILE, DECISIONS_FILE, CSV_REPORT_FILE, OUTPUT_DIR, ENHANCED_DIR
from src.pipeline_runner import process_single_image
from src.report_generator import generate_reports
from src.gcs_storage import sync_from_gcs, sync_to_gcs, upload_file_to_gcs

BATCH_STATUS: Dict[str, Any] = {
    "is_running": False,
    "total": 0,
    "current_index": 0,
    "current_filename": "",
    "current_stage": "Idle",
    "completed": [],
    "error": None
}

def load_existing_decisions() -> Dict[str, Any]:
    """Loads all decisions from JSON ledger keyed by filename."""
    sync_from_gcs(DECISIONS_FILE)
    if DECISIONS_FILE.exists():
        try:
            with open(DECISIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {item["filename"]: item for item in data if "filename" in item}
        except Exception:
            return {}
    return {}

def save_all_decisions(decisions_dict: Dict[str, Any]):
    """Saves updated decisions to JSON and regenerates HTML and CSV reports."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    items = list(decisions_dict.values())
    with open(DECISIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)
    sync_to_gcs(DECISIONS_FILE)
    generate_reports(items)

def get_unprocessed_images() -> List[Path]:
    """Returns sample photos that have not yet been evaluated."""
    if not SAMPLE_PHOTOS_DIR.exists():
        return []
    all_files = sorted([f for f in SAMPLE_PHOTOS_DIR.iterdir() if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp')])
    existing = load_existing_decisions()
    return [f for f in all_files if f.name not in existing]

def run_batch(
    limit: Optional[int] = None,
    specific_image: Optional[str] = None,
    process_unprocessed_only: bool = True
) -> List[Dict[str, Any]]:
    """
    Processes images from Sample-Photos incrementally and updates all deliverables.
    Preserves all existing decisions rather than overwriting.
    """
    global BATCH_STATUS

    if not SAMPLE_PHOTOS_DIR.exists():
        BATCH_STATUS["error"] = f"Sample photos directory not found at {SAMPLE_PHOTOS_DIR}"
        return []

    all_files = sorted([f for f in SAMPLE_PHOTOS_DIR.iterdir() if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp')])
    existing_decisions = load_existing_decisions()

    if specific_image:
        targets = [f for f in all_files if specific_image.lower() in f.name.lower()]
        if not targets:
            BATCH_STATUS["error"] = f"Image '{specific_image}' not found in {SAMPLE_PHOTOS_DIR}"
            return []
    elif process_unprocessed_only:
        unprocessed = [f for f in all_files if f.name not in existing_decisions]
        if unprocessed:
            targets = unprocessed[:limit] if limit else unprocessed
        else:
            targets = all_files[:limit] if limit else all_files
    elif limit:
        targets = all_files[:limit]
    else:
        targets = all_files

    BATCH_STATUS["is_running"] = True
    BATCH_STATUS["total"] = len(targets)
    BATCH_STATUS["current_index"] = 0
    BATCH_STATUS["current_filename"] = ""
    BATCH_STATUS["current_stage"] = "Initializing batch..."
    BATCH_STATUS["completed"] = []
    BATCH_STATUS["error"] = None

    print(f"\n=======================================================")
    print(f"GRUBHUB MENU IMAGE PLATFORM - INCREMENTAL BATCH RUNNER")
    print(f"Target Images: {len(targets)} | Existing Ingested: {len(existing_decisions)}")
    print(f"=======================================================\n")

    new_results = []
    start_batch = time.time()

    try:
        for idx, img_path in enumerate(targets, 1):
            BATCH_STATUS["current_index"] = idx
            BATCH_STATUS["current_filename"] = img_path.name
            BATCH_STATUS["current_stage"] = f"Processing {img_path.name} ({idx}/{len(targets)})..."

            print(f"[{idx}/{len(targets)}] Ingesting {img_path.name}...")
            try:
                res = process_single_image(img_path)
                new_results.append(res)
                existing_decisions[img_path.name] = res

                # Upload raw image and enhanced asset to GCS
                upload_file_to_gcs(img_path, f"samples/{img_path.name}")
                if res.get("enhanced_filename"):
                    enh_path = ENHANCED_DIR / res["enhanced_filename"]
                    if enh_path.exists():
                        upload_file_to_gcs(enh_path, f"enhanced/{res['enhanced_filename']}")

                # Incrementally save after each photo so progress is immediately persistent
                save_all_decisions(existing_decisions)

                sop = res.get("sop_decision", {})
                quality = res.get("quality_metrics", {})
                audit = res.get("authenticity_audit", {})

                summary_item = {
                    "filename": img_path.name,
                    "dish_name": res.get("analysis", {}).get("primary_dish_name", "Dish"),
                    "status": sop.get("status"),
                    "quality_lift": quality.get("quality_lift_percent", 0),
                    "is_authentic": audit.get("is_authentic", True),
                    "latency": res.get("latency_seconds", 0)
                }
                BATCH_STATUS["completed"].append(summary_item)

                print(f"    ↳ Decision: {sop.get('status')} | Quality: {quality.get('quality_score_pre'):.2f} → {quality.get('quality_score_post'):.2f} (+{quality.get('quality_lift_percent')}%) | Latency: {res.get('latency_seconds')}s")
            except Exception as e:
                print(f"    ❌ Error processing {img_path.name}: {e}")
                BATCH_STATUS["completed"].append({
                    "filename": img_path.name,
                    "dish_name": img_path.stem,
                    "status": "ERROR",
                    "error": str(e)
                })

        total_batch_time = round(time.time() - start_batch, 2)
        print(f"\n✅ Finished processing batch of {len(new_results)} images in {total_batch_time}s")
        BATCH_STATUS["current_stage"] = f"Complete! Ingested {len(new_results)} new photos."
    except Exception as e:
        BATCH_STATUS["error"] = str(e)
        BATCH_STATUS["current_stage"] = f"Error: {str(e)}"
    finally:
        BATCH_STATUS["is_running"] = False

    return new_results

def main():
    parser = argparse.ArgumentParser(description="Grubhub Menu Image Platform - Batch Evaluator")
    parser.add_argument("--all", action="store_true", help="Process all sample photos")
    parser.add_argument("--limit", type=int, default=None, help="Process next N images (e.g. --limit 5)")
    parser.add_argument("--image", type=str, default=None, help="Process a specific image by name")
    parser.add_argument("--force-reprocess", action="store_true", help="Reprocess even if already in ledger")

    args = parser.parse_args()
    if not args.all and not args.limit and not args.image:
        args.limit = 5

    run_batch(
        limit=args.limit if not args.all else None,
        specific_image=args.image,
        process_unprocessed_only=not args.force_reprocess
    )

if __name__ == "__main__":
    main()
