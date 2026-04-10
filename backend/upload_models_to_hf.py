"""
Upload all .pth model files to Hugging Face Hub.

Usage:
  1. First login: huggingface-cli login
  2. Then run: python upload_models_to_hf.py

This creates/updates a public HF repo with all model weights.
"""
import os
import sys

try:
    from huggingface_hub import HfApi, create_repo
except ImportError:
    print("Install first: pip install huggingface_hub")
    sys.exit(1)

# ── Configuration ──
HF_REPO_ID = "Aditya-singh-AI/DeepScanX-Models"  # Change to your HF username

# Model files to upload
MODELS = {
    "app3/resnet18_model_001.pth": "resnet18_model_001.pth",
    "app4/breast_cancer_cnn_model_updated.pth": "breast_cancer_cnn_model_updated.pth",
    "app8/skin_cancer_resnet18.pth": "skin_cancer_resnet18.pth",
    "app9/chest_xray_resnet18.pth": "chest_xray_resnet18.pth",
}

def main():
    api = HfApi()
    
    # Create the repo if it doesn't exist
    try:
        create_repo(HF_REPO_ID, repo_type="model", exist_ok=True)
        print(f"✓ Repository {HF_REPO_ID} ready")
    except Exception as e:
        print(f"Note: {e}")
    
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    
    for local_rel, hf_filename in MODELS.items():
        local_path = os.path.join(backend_dir, local_rel)
        if not os.path.isfile(local_path):
            print(f"✗ SKIP {local_rel} — file not found")
            continue
        
        size_mb = os.path.getsize(local_path) / 1_048_576
        print(f"↑ Uploading {local_rel} ({size_mb:.1f} MB) → {HF_REPO_ID}/{hf_filename} ...", flush=True)
        
        try:
            api.upload_file(
                path_or_fileobj=local_path,
                path_in_repo=hf_filename,
                repo_id=HF_REPO_ID,
                repo_type="model",
            )
            print(f"✓ Uploaded {hf_filename}")
        except Exception as e:
            print(f"✗ ERROR uploading {hf_filename}: {e}")
    
    print(f"\nDone! Models available at: https://huggingface.co/{HF_REPO_ID}")
    print(f"\nDirect download URLs for Render env vars:")
    for _, hf_filename in MODELS.items():
        print(f"  https://huggingface.co/{HF_REPO_ID}/resolve/main/{hf_filename}")

if __name__ == "__main__":
    main()
