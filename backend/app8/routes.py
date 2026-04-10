"""
app8/routes.py — Skin Cancer (Melanoma) Detection
Analyzes dermoscopy images to classify benign vs. malignant lesions.
"""
import base64
import io
import os
import json
import numpy as np
import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file
from utils.helpers import login_required, save_prediction
from utils.report_generator import generate_detailed_report
from utils.dicom_utils import is_dicom_file, parse_dicom
from utils.ensemble import load_ensemble_models, ensemble_predict
from app2.models import db

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms, models
from PIL import Image

LOW_CONFIDENCE_THRESHOLD = 0.65

bp = Blueprint('app8', __name__, template_folder='templates')

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "skin_cancer_resnet18.pth")
IMG_SIZE = 224
CLASS_NAMES = ['Benign', 'Malignant']

_model = None


def _load_model():
    global _model
    if _model is not None:
        return _model
    try:
        from utils.model_downloader import ensure_model
        ensure_model(MODEL_PATH, 'skin_cancer_resnet18.pth')
    except Exception:
        pass
    if not os.path.isfile(MODEL_PATH):
        raise FileNotFoundError(
            f"Skin cancer model not found: {MODEL_PATH}. "
            "Set MODEL_URL_SKIN env variable on Render to a direct download URL."
        )
    m = models.resnet18(weights=None)
    m.fc = nn.Linear(m.fc.in_features, len(CLASS_NAMES))
    state = torch.load(MODEL_PATH, map_location=DEVICE)
    if isinstance(state, dict) and 'model_state_dict' in state:
        m.load_state_dict(state['model_state_dict'])
    else:
        m.load_state_dict(state)
    m = m.to(DEVICE)
    m.eval()
    _model = m
    return _model


eval_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


# ── Grad-CAM ──
class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.activations = None
        self.gradients = None
        target_layer.register_forward_hook(self._fwd)
        target_layer.register_full_backward_hook(self._bwd)

    def _fwd(self, m, i, o):
        self.activations = o.detach()

    def _bwd(self, m, gi, go):
        g = go[0] if isinstance(go, tuple) else go
        if g is not None:
            self.gradients = g.detach()

    def __call__(self, inp, class_idx=None):
        if inp.dim() == 3:
            inp = inp.unsqueeze(0)
        inp = inp.clone().detach().requires_grad_(True).to(DEVICE)
        out = self.model(inp)
        if class_idx is None:
            class_idx = out.argmax(dim=1).item()
        self.model.zero_grad()
        out[:, class_idx].sum().backward(retain_graph=True)
        if self.gradients is None or self.activations is None:
            raise RuntimeError("Grad-CAM hooks failed")
        grads = self.gradients[0].cpu().numpy()
        acts = self.activations[0].cpu().numpy()
        weights = np.mean(grads, axis=(1, 2))
        cam = np.zeros(acts.shape[1:], dtype=np.float32)
        for i, w in enumerate(weights):
            cam += w * acts[i]
        cam = np.maximum(cam, 0)
        if cam.max() > 0:
            cam /= (cam.max() + 1e-8)
        cam = cv2.resize(cam, (inp.shape[3], inp.shape[2]))
        return cam


def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=120)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return b64


@bp.route('/', methods=['GET', 'POST'])
@login_required
def page():
    if request.method == 'POST':
        if 'images' not in request.files:
            flash('No file uploaded')
            return redirect(request.url)

        file = request.files['images']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)

        patient_id = request.form.get('patient_id', '').strip() or None

        try:
            model = _load_model()
            gradcam = GradCAM(model, model.layer4[-1])

            # ── Load image (DICOM or standard) ──
            if is_dicom_file(file.filename):
                raw_image = parse_dicom(file.stream)
            else:
                raw_image = Image.open(file.stream).convert('RGB')

            input_tensor = eval_transform(raw_image).unsqueeze(0).to(DEVICE)

            # ── Inference ──
            with torch.no_grad():
                output = model(input_tensor)
                probs = F.softmax(output, dim=1)[0]
                pred_idx = int(probs.argmax().item())
                confidence = float(probs[pred_idx].item())
                pred_class = CLASS_NAMES[pred_idx]

            probs_np = probs.cpu().numpy()
            cancer_status = "Malignant (Suspicious)" if pred_class == 'Malignant' else "Benign (Non-cancerous)"

            # ── Grad-CAM ──
            cam = gradcam(input_tensor, pred_idx)
            processed_np = input_tensor.squeeze(0).permute(1, 2, 0).cpu().numpy()
            processed_np = processed_np * np.array([0.229, 0.224, 0.225]) + np.array([0.485, 0.456, 0.406])
            processed_np = np.clip(processed_np, 0, 1)

            cam_resized = cv2.resize(cam, (raw_image.size[0], raw_image.size[1]))
            heatmap = cv2.applyColorMap(np.uint8(255 * cam_resized), cv2.COLORMAP_JET)
            heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB) / 255.0
            overlay = 0.5 * np.array(raw_image) / 255.0 + 0.5 * heatmap
            overlay = np.clip(overlay, 0, 1)

            # ── Plots ──
            fig, axes = plt.subplots(1, 3, figsize=(18, 6))
            axes[0].imshow(raw_image)
            axes[0].set_title(f"Original\n{pred_class} ({confidence*100:.1f}%)")
            axes[0].axis('off')
            axes[1].imshow(processed_np)
            axes[1].set_title("Preprocessed")
            axes[1].axis('off')
            axes[2].imshow(overlay)
            axes[2].set_title("Grad-CAM Heatmap")
            axes[2].axis('off')
            plt.tight_layout()
            results_plot_b64 = fig_to_base64(fig)

            plt.style.use("dark_background")
            fig2 = plt.figure(figsize=(8, 5))
            sns.barplot(x=CLASS_NAMES, y=probs_np, palette="RdYlGn_r")
            plt.ylim(0, 1)
            plt.title(f"Prediction Distribution (Predicted: {pred_class})")
            plt.ylabel("Probability")
            plt.grid(axis='y', alpha=0.3)
            prob_plot_b64 = fig_to_base64(fig2)

            # ── Ensemble (if requested) ──
            ensemble_results = None
            if request.form.get('ensemble') == 'true':
                models_dict = load_ensemble_models('skin_cancer', len(CLASS_NAMES), os.path.dirname(__file__))
                if models_dict:
                    ensemble_results = ensemble_predict(input_tensor, models_dict, CLASS_NAMES)

            # ── Explanation ──
            if pred_class == 'Malignant':
                explanation = (
                    f"The AI model predicts this dermoscopy image as **Malignant** with {confidence*100:.1f}% confidence. "
                    f"This suggests a suspicious lesion that may be melanoma or another form of skin cancer. "
                    f"The Grad-CAM heatmap highlights the regions the model identified as most concerning. "
                    f"Immediate referral to a dermatologist for biopsy and histopathological examination is strongly recommended."
                )
            else:
                explanation = (
                    f"The AI model predicts this dermoscopy image as **Benign** with {confidence*100:.1f}% confidence. "
                    f"The image does not show strong features associated with melanoma or malignant lesions. "
                    f"However, routine skin checks are recommended, especially for patients with risk factors. "
                    f"Consult a dermatologist if the lesion changes in size, shape, or color."
                )

            report = {
                'filename': file.filename,
                'predicted_class': pred_class,
                'confidence': str(confidence),
                'cancer_status': cancer_status,
                'prob_plot': f'data:image/png;base64,{prob_plot_b64}',
                'results_plot': f'data:image/png;base64,{results_plot_b64}',
                'explanation': explanation,
                'low_confidence': confidence < LOW_CONFIDENCE_THRESHOLD,
                'probabilities': [(CLASS_NAMES[i], float(probs_np[i])) for i in range(len(CLASS_NAMES))],
                'ensemble_results': ensemble_results,
            }
            save_prediction(request.user['_id'], 'skin_cancer', report, patient_id=patient_id)
            return render_template('skin_cancer.html', report=report)

        except Exception as e:
            flash(f'Error processing image: {str(e)}')
            return redirect(request.url)

    # GET — fetch patients for select dropdown
    patients = list(db.patients.find({"doctor_id": request.user['_id']}).sort("name", 1))
    return render_template('skin_cancer.html', patients=patients)


@bp.route('/download_report', methods=['POST'])
@login_required
def download_report():
    data = {
        'predicted_class': request.form.get('predicted_class', ''),
        'confidence': request.form.get('confidence', ''),
        'cancer_status': request.form.get('cancer_status', ''),
        'filename': request.form.get('filename', 'skin_scan'),
        'explanation_text': request.form.get('explanation_text', ''),
        'doctor_notes': request.form.get('doctor_notes', ''),
        'prob_chart_b64': request.form.get('prob_plot_b64', ''),
        'gradcam_b64': request.form.get('results_plot_b64', ''),
    }
    try:
        data['probabilities'] = json.loads(request.form.get('probabilities_json', '[]'))
    except Exception:
        data['probabilities'] = []
    try:
        data['ensemble_results'] = json.loads(request.form.get('ensemble_json', '{}')) or None
    except Exception:
        data['ensemble_results'] = None
    pdf_bytes = generate_detailed_report(data, 'Skin Cancer (Melanoma) Detection')
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name='deepscanx_skin_cancer_report.pdf'
    )
