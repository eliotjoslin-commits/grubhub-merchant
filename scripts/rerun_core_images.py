"""Reruns the 6 core benchmark images through the latest pipeline with self-healing,
updates local decisions and reports, and synchronizes to GCS and Cloud Run."""

import os
import json
import time
from pathlib import Path

from src.config import GCP_PROJECT, SAMPLE_PHOTOS_DIR, DECISIONS_FILE, ENHANCED_DIR

# Ensure GCS environment variables are set for sync
os.environ.setdefault("ENABLE_GCS_STORAGE", "true")
os.environ.setdefault("GCS_ASSETS_BUCKET", f"{GCP_PROJECT}-grubhub-merchant-assets")

from src.server import load_all_decisions, save_decisions_list, generate_reports
from src.pipeline_runner import process_single_image
from src.gcs_storage import sync_to_gcs, upload_file_to_gcs

CORE_IMAGES = [
    "Appetizer1.jpg",
    "Appitizer2.jpg",
    "Appitizer3.jpg",
    "Appitizer4.jpg",
    "Appitizer5.jpg",
    "Appitizer9.jpg",
]

def main():
    print("=" * 70)
    print("🚀 RERUNNING 6 CORE TEST IMAGES (Self-Healing & Calibrated Intake)")
    print("=" * 70)

    decisions = load_all_decisions()
    results_summary = []

    for idx, filename in enumerate(CORE_IMAGES, 1):
        img_path = SAMPLE_PHOTOS_DIR / filename
        if not img_path.exists():
            print(f"[{idx}/6] ⚠️ File not found: {filename}")
            continue

        print(f"\n[{idx}/6] Processing {filename}...")
        t0 = time.time()
        result = process_single_image(
            image_path=img_path,
            min_quality_threshold=0.35,
            enable_self_healing=True,
            enhancement_mode="studio_reshoot"
        )
        elapsed = time.time() - t0

        decisions[filename] = result
        sop = result.get("sop_decision", {})
        status = sop.get("status")
        reasons = sop.get("reasons", [])
        self_healed = sop.get("self_healed", False)
        audit = result.get("authenticity_audit", {})
        dish_name = result.get("analysis", {}).get("primary_dish_name", "Dish")

        results_summary.append({
            "filename": filename,
            "dish_name": dish_name,
            "status": status,
            "reasons": reasons,
            "self_healed": self_healed,
            "audit_verdict": audit.get("audit_verdict"),
            "risk_score": audit.get("truth_in_advertising_risk_score"),
            "elapsed_s": round(elapsed, 1)
        })

        print(f"  ✓ Finished in {elapsed:.1f}s | Status: {status} | Self-Healed: {self_healed}")

    # 1. Save updated decisions locally and regenerate HTML/CSV reports
    print("\n💾 Saving decisions and regenerating reports...")
    save_decisions_list(decisions)
    generate_reports(list(decisions.values()))

    # 2. Sync decisions ledger to GCS
    print("\n☁️ Syncing decisions ledger to GCS bucket...")
    sync_to_gcs(DECISIONS_FILE)

    # 3. Upload enhanced images to GCS
    print("☁️ Syncing enhanced images to GCS bucket...")
    for filename in CORE_IMAGES:
        enh_path = ENHANCED_DIR / f"enhanced_{Path(filename).stem}.jpg"
        if enh_path.exists():
            upload_file_to_gcs(enh_path, f"enhanced/{enh_path.name}")
            print(f"  ✓ Uploaded {enh_path.name} to GCS")

    print("\n" + "=" * 70)
    print("📊 FINAL EXECUTION SUMMARY")
    print("=" * 70)
    for r in results_summary:
        sh_str = "YES (Pass 2)" if r["self_healed"] else "No"
        print(f"• {r['filename']:15} | {r['status']:16} | Dish: {r['dish_name'][:25]:25} | Risk: {r['risk_score']} | Self-Healed: {sh_str} | Time: {r['elapsed_s']}s")
    print("=" * 70)

if __name__ == "__main__":
    main()
