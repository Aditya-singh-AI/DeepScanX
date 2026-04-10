"""
utils/model_downloader.py — Auto-download model weights at build/runtime.

On Render, models are downloaded during `build.sh` using the Hugging Face Hub.
Locally, models are expected to already exist in their app directories.
"""
import os
import sys

# Repository on Hugging Face that stores all model weights
HF_REPO_ID = os.getenv("HF_MODEL_REPO", "Aditya-singh-AI/DeepScanX-Models")

# Map: (app_directory_basename, local_filename) → filename in HF repo
MODEL_REGISTRY = {
    "resnet18_model_001.pth": "resnet18_model_001.pth",                           # app3 lung/colon
    "breast_cancer_cnn_model_updated.pth": "breast_cancer_cnn_model_updated.pth",  # app4 breast
    "lung_cancer_prediction_20250821_150505.pth": "lung_cancer_prediction_20250821_150505.pth",  # app5 brain
    "skin_cancer_resnet18.pth": "skin_cancer_resnet18.pth",                        # app8 skin
    "chest_xray_resnet18.pth": "chest_xray_resnet18.pth",                          # app9 chest
    "diabetic_retinopathy_resnet18.pth": "diabetic_retinopathy_resnet18.pth",      # app10 retinopathy
}


def ensure_model(local_path: str, filename: str = None) -> str:
    """
    Ensure a model file exists at local_path.
    If it doesn't exist, try downloading from Hugging Face Hub.
    Returns local_path unconditionally.
    """
    if os.path.isfile(local_path):
        return local_path

    fname = filename or os.path.basename(local_path)
    hf_filename = MODEL_REGISTRY.get(fname)

    if not hf_filename:
        print(f"[ModelDownloader] WARNING: '{fname}' has no HF mapping. Skipping download.", flush=True)
        return local_path

    print(f"[ModelDownloader] '{fname}' not found at {local_path}. Downloading from HF ...", flush=True)

    try:
        from huggingface_hub import hf_hub_download
        downloaded_path = hf_hub_download(
            repo_id=HF_REPO_ID,
            filename=hf_filename,
            local_dir=os.path.dirname(local_path),
            local_dir_use_symlinks=False,
        )
        # hf_hub_download may put it in a subfolder; move if needed
        if downloaded_path != local_path and os.path.isfile(downloaded_path):
            import shutil
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            shutil.move(downloaded_path, local_path)
        size_mb = os.path.getsize(local_path) / 1_048_576
        print(f"[ModelDownloader] ✓ Downloaded '{fname}' ({size_mb:.1f} MB)", flush=True)
    except ImportError:
        print(
            f"[ModelDownloader] huggingface_hub not installed. Cannot download '{fname}'.",
            file=sys.stderr, flush=True
        )
    except Exception as exc:
        print(f"[ModelDownloader] ERROR downloading '{fname}': {exc}", file=sys.stderr, flush=True)
        if os.path.exists(local_path) and os.path.getsize(local_path) == 0:
            os.remove(local_path)

    return local_path


def download_all_models(base_dir: str):
    """Download all registered models. Called by build.sh at deploy time."""
    app_model_dirs = {
        "resnet18_model_001.pth": os.path.join(base_dir, "app3"),
        "breast_cancer_cnn_model_updated.pth": os.path.join(base_dir, "app4"),
        "lung_cancer_prediction_20250821_150505.pth": os.path.join(base_dir, "app5"),
        "skin_cancer_resnet18.pth": os.path.join(base_dir, "app8"),
        "chest_xray_resnet18.pth": os.path.join(base_dir, "app9"),
        "diabetic_retinopathy_resnet18.pth": os.path.join(base_dir, "app10"),
    }

    for fname, app_dir in app_model_dirs.items():
        local_path = os.path.join(app_dir, fname)
        ensure_model(local_path, fname)


if __name__ == "__main__":
    # Can be called directly: python -m utils.model_downloader
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"[ModelDownloader] Downloading all models to: {backend_dir}", flush=True)
    download_all_models(backend_dir)
    print("[ModelDownloader] Done.", flush=True)
