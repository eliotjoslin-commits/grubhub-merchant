"""Google Cloud Storage (GCS) adapter for serverless asset persistence and decisions ledger.
Seamlessly synchronizes local container files with GCS when running on Cloud Run.
Gracefully no-ops when running locally without GCS credentials.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from src.config import GCP_PROJECT

GCS_BUCKET_NAME = os.getenv("GCS_ASSETS_BUCKET", f"{GCP_PROJECT}-grubhub-merchant-assets")
ENABLE_GCS = os.getenv("ENABLE_GCS_STORAGE", "false").lower() == "true"

_storage_client = None

def get_storage_client():
    global _storage_client
    if _storage_client is None:
        try:
            from google.cloud import storage
            from google.api_core.client_options import ClientOptions
            valid_proj = GCP_PROJECT if (GCP_PROJECT and GCP_PROJECT != "your-gcp-project-id") else None
            client_opts = ClientOptions(quota_project_id=valid_proj) if valid_proj else None
            _storage_client = storage.Client(
                project=valid_proj,
                client_options=client_opts
            )
        except Exception as e:
            print(f"⚠️ GCS Client initialization skipped: {e}")
            return None
    return _storage_client

def sync_from_gcs(local_decisions_path: Path):
    """Downloads latest moderation_decisions.json from GCS if available."""
    if not ENABLE_GCS or not GCS_BUCKET_NAME:
        return
    client = get_storage_client()
    if not client:
        return
    try:
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob("decisions/moderation_decisions.json")
        if blob.exists():
            local_decisions_path.parent.mkdir(parents=True, exist_ok=True)
            blob.download_to_filename(str(local_decisions_path))
            print(f"📥 Synced moderation_decisions.json from gs://{GCS_BUCKET_NAME}")
        else:
            # Seed initial decisions to GCS on first launch
            if local_decisions_path.exists():
                blob.upload_from_filename(str(local_decisions_path))
                print(f"📤 Seeded initial moderation_decisions.json to gs://{GCS_BUCKET_NAME}")
    except Exception as e:
        print(f"⚠️ Warning: GCS sync error (continuing with local cache): {e}")

def sync_to_gcs(local_decisions_path: Path):
    """Uploads updated moderation_decisions.json to GCS."""
    if not ENABLE_GCS or not GCS_BUCKET_NAME:
        return
    client = get_storage_client()
    if not client:
        return
    try:
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob("decisions/moderation_decisions.json")
        blob.upload_from_filename(str(local_decisions_path))
    except Exception as e:
        print(f"⚠️ Warning: Failed to sync decisions to GCS: {e}")

def upload_file_to_gcs(local_path: Path, gcs_subpath: str):
    """Uploads a dish image or enhanced asset to GCS."""
    if not ENABLE_GCS or not GCS_BUCKET_NAME:
        return
    client = get_storage_client()
    if not client:
        return
    try:
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(gcs_subpath)
        blob.upload_from_filename(str(local_path))
    except Exception as e:
        print(f"⚠️ Warning: Failed to upload {local_path.name} to GCS: {e}")

def delete_file_from_gcs(gcs_subpath: str):
    """Deletes an asset from GCS if it exists."""
    if not ENABLE_GCS or not GCS_BUCKET_NAME:
        return
    client = get_storage_client()
    if not client:
        return
    try:
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(gcs_subpath)
        if blob.exists():
            blob.delete()
            print(f"🗑️ Deleted gs://{GCS_BUCKET_NAME}/{gcs_subpath}")
    except Exception as e:
        print(f"⚠️ Warning: Failed to delete {gcs_subpath} from GCS: {e}")

def download_file_from_gcs(gcs_subpath: str, local_path: Path) -> bool:
    """Downloads an asset from GCS to local disk if it exists. Returns True if downloaded."""
    if not ENABLE_GCS or not GCS_BUCKET_NAME:
        return False
    client = get_storage_client()
    if not client:
        return False
    try:
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(gcs_subpath)
        if blob.exists():
            local_path.parent.mkdir(parents=True, exist_ok=True)
            blob.download_to_filename(str(local_path))
            print(f"📥 Downloaded gs://{GCS_BUCKET_NAME}/{gcs_subpath} to local cache ({local_path.name})")
            return True
        return False
    except Exception as e:
        print(f"⚠️ Warning: Failed to download {gcs_subpath} from GCS: {e}")
        return False

def sync_assets_from_gcs(samples_dir: Path, enhanced_dir: Path):
    """Synchronizes all decisions, raw sample images, and enhanced images from GCS.
    Ensures that newly spawned serverless containers have all assets on local disk."""
    if not ENABLE_GCS or not GCS_BUCKET_NAME:
        return
    client = get_storage_client()
    if not client:
        return
    try:
        bucket = client.bucket(GCS_BUCKET_NAME)
        print(f"🔄 Syncing persistent assets from gs://{GCS_BUCKET_NAME}...")

        samples_dir.mkdir(parents=True, exist_ok=True)
        enhanced_dir.mkdir(parents=True, exist_ok=True)

        # 1. Sync all blobs in samples/
        sample_blobs = list(client.list_blobs(bucket, prefix="samples/"))
        downloaded_samples = 0
        for b in sample_blobs:
            filename = os.path.basename(b.name)
            if not filename:
                continue
            dest = samples_dir / filename
            if not dest.exists():
                b.download_to_filename(str(dest))
                downloaded_samples += 1

        # 2. Sync all blobs in enhanced/
        enh_blobs = list(client.list_blobs(bucket, prefix="enhanced/"))
        downloaded_enh = 0
        for b in enh_blobs:
            filename = os.path.basename(b.name)
            if not filename:
                continue
            dest = enhanced_dir / filename
            if not dest.exists():
                b.download_to_filename(str(dest))
                downloaded_enh += 1

        print(f"✅ GCS asset sync complete: {downloaded_samples} new samples, {downloaded_enh} new enhanced images.")
    except Exception as e:
        print(f"⚠️ Warning during GCS asset sync: {e}")
