"""
app11/routes.py — Whole Slide Image (WSI) Viewer
High-resolution pathology image viewer with click-to-analyze AI patches.
Uses OpenSeadragon (client-side) with PIL-based tiling (server-side).
"""
import base64
import io
import os
import math
import json
import numpy as np
import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file
from utils.helpers import login_required, save_prediction
from app2.models import db

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms, models
from PIL import Image

bp = Blueprint('app11', __name__, template_folder='templates')

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
TILES_DIR = os.path.join(os.path.dirname(__file__), 'tiles')
IMG_SIZE = 224
TILE_SIZE = 256

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TILES_DIR, exist_ok=True)

eval_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def generate_dzi_tiles(image_path: str, output_dir: str, tile_size: int = 256):
    """
    Generate Deep Zoom Image (DZI) tiles from a large image using PIL.
    Returns the DZI XML descriptor string and the image dimensions.
    """
    img = Image.open(image_path).convert('RGB')
    width, height = img.size

    # Calculate number of levels
    max_dim = max(width, height)
    max_level = math.ceil(math.log2(max_dim)) + 1

    tiles_root = os.path.join(output_dir, 'tiles_files')
    os.makedirs(tiles_root, exist_ok=True)

    for level in range(max_level + 1):
        level_dir = os.path.join(tiles_root, str(level))
        os.makedirs(level_dir, exist_ok=True)

        scale = 2 ** (max_level - level)
        level_w = max(1, width // scale)
        level_h = max(1, height // scale)

        level_img = img.resize((level_w, level_h), Image.Resampling.LANCZOS)

        cols = math.ceil(level_w / tile_size)
        rows = math.ceil(level_h / tile_size)

        for col in range(cols):
            for row in range(rows):
                x = col * tile_size
                y = row * tile_size
                x2 = min(x + tile_size, level_w)
                y2 = min(y + tile_size, level_h)
                tile = level_img.crop((x, y, x2, y2))
                tile.save(os.path.join(level_dir, f"{col}_{row}.jpeg"), "JPEG", quality=85)

    dzi_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Image xmlns="http://schemas.microsoft.com/deepzoom/2008"
       Format="jpeg" Overlap="0" TileSize="{tile_size}">
  <Size Width="{width}" Height="{height}"/>
</Image>"""

    dzi_path = os.path.join(output_dir, 'tiles.dzi')
    with open(dzi_path, 'w') as f:
        f.write(dzi_xml)

    return dzi_xml, width, height


@bp.route('/')
@login_required
def page():
    # List uploaded slides
    slides = []
    if os.path.isdir(UPLOAD_DIR):
        for f in os.listdir(UPLOAD_DIR):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp')):
                slides.append(f)
    return render_template('wsi_viewer.html', slides=slides)


@bp.route('/upload', methods=['POST'])
@login_required
def upload_slide():
    file = request.files.get('slide') or request.files.get('wsi_file')
    if not file or file.filename == '':
        return jsonify({"error": "No file uploaded"}), 400

    filename = file.filename
    save_path = os.path.join(UPLOAD_DIR, filename)
    file.save(save_path)

    # Generate tiles
    slide_name = os.path.splitext(filename)[0]
    slide_tiles_dir = os.path.join(TILES_DIR, slide_name)
    os.makedirs(slide_tiles_dir, exist_ok=True)

    try:
        generate_dzi_tiles(save_path, slide_tiles_dir, TILE_SIZE)
        dzi_url = f"/app11/tiles/{slide_name}/tiles.dzi"
        return jsonify({"dzi_url": dzi_url, "filename": filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/view/<filename>')
@login_required
def view_slide(filename):
    slide_name = os.path.splitext(filename)[0]
    tiles_base = f"/app11/tiles/{slide_name}"
    return render_template('wsi_viewer.html', viewing=True, filename=filename,
                           tiles_base=tiles_base, slide_name=slide_name)


@bp.route('/tiles/<slide_name>/tiles.dzi')
@login_required
def serve_dzi(slide_name):
    dzi_path = os.path.join(TILES_DIR, slide_name, 'tiles.dzi')
    if not os.path.isfile(dzi_path):
        return "DZI not found", 404
    return send_file(dzi_path, mimetype='application/xml')


@bp.route('/tiles/<slide_name>/tiles_files/<int:level>/<path:tile_name>')
@login_required
def serve_tile(slide_name, level, tile_name):
    tile_path = os.path.join(TILES_DIR, slide_name, 'tiles_files', str(level), tile_name)
    if not os.path.isfile(tile_path):
        return "Tile not found", 404
    return send_file(tile_path, mimetype='image/jpeg')


@bp.route('/analyze_patch', methods=['POST'])
@login_required
def analyze_patch():
    """
    Analyze a specific patch from the slide.
    Receives: filename, x, y, patch_size (in original image coordinates)
    Returns: prediction result as JSON
    """
    data = request.get_json()
    filename = data.get('filename')
    x = int(data.get('x', 0))
    y = int(data.get('y', 0))
    patch_size = int(data.get('patch_size', 224))

    image_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.isfile(image_path):
        return jsonify({"error": "Image not found"}), 404

    try:
        img = Image.open(image_path).convert('RGB')
        w, h = img.size

        # Clamp coordinates
        x = max(0, min(x, w - patch_size))
        y = max(0, min(y, h - patch_size))

        patch = img.crop((x, y, x + patch_size, y + patch_size))

        # Use lung/colon model (app3) as default analyzer
        # In production, user would choose which model
        from app3.routes import _load_model as load_app3_model, classes as app3_classes
        model, gradcam = load_app3_model()

        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        input_tensor = transform(patch.resize((224, 224))).unsqueeze(0).to(DEVICE)

        with torch.no_grad():
            out = model(input_tensor)
            probs = F.softmax(out, dim=1)[0]
            pred_idx = int(probs.argmax().item())
            confidence = float(probs[pred_idx].item())
            pred_class = app3_classes[pred_idx]

        probs_np = probs.cpu().numpy()

        # Generate Grad-CAM for patch
        cam = gradcam(input_tensor, pred_idx)
        cam_resized = cv2.resize(cam, (patch_size, patch_size))
        heatmap = cv2.applyColorMap(np.uint8(255 * cam_resized), cv2.COLORMAP_JET)
        heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
        heatmap_pil = Image.fromarray(heatmap)
        buf = io.BytesIO()
        heatmap_pil.save(buf, format='PNG')
        heatmap_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        return jsonify({
            "predicted_class": pred_class,
            "confidence": confidence,
            "probabilities": {app3_classes[i]: float(probs_np[i]) for i in range(len(app3_classes))},
            "heatmap": f"data:image/png;base64,{heatmap_b64}",
            "patch_coords": {"x": x, "y": y, "size": patch_size},
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
