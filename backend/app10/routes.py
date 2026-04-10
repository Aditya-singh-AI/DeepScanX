"""
app10/routes.py — Diabetic Retinopathy Screening
Fundus image analysis for eye disease severity classification.
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

bp = Blueprint('app10', __name__, template_folder='templates')

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "diabetic_retinopathy_resnet18.pth")
IMG_SIZE = 224
CLASS_NAMES = ['No DR', 'Mild', 'Moderate', 'Severe', 'Proliferative DR']

SEVERITY_INFO = {
    'No DR': {
        'status': 'No Diabetic Retinopathy',
        'level': 0,
        'color': '#27ae60',
        'explanation': (
            "No signs of diabetic retinopathy detected. The retinal vasculature appears normal "
            "without microaneurysms, hemorrhages, or exudates. Routine annual screening is recommended "
            "for diabetic patients."
        ),
    },
    'Mild': {
        'status': 'Mild Non-Proliferative DR',
        'level': 1,
        'color': '#f1c40f',
        'explanation': (
            "Mild non-proliferative diabetic retinopathy detected. Early signs such as microaneurysms "
            "may be present. Close monitoring with follow-up in 6-12 months is recommended. "
            "Blood sugar control is essential."
        ),
    },
    'Moderate': {
        'status': 'Moderate Non-Proliferative DR',
        'level': 2,
        'color': '#e67e22',
        'explanation': (
            "Moderate non-proliferative diabetic retinopathy detected. Multiple microaneurysms, "
            "dot-blot hemorrhages, or hard exudates may be present. Referral to an ophthalmologist "
            "within 3-6 months is recommended."
        ),
    },
    'Severe': {
        'status': 'Severe Non-Proliferative DR',
        'level': 3,
        'color': '#e74c3c',
        'explanation': (
            "Severe non-proliferative diabetic retinopathy detected. Extensive hemorrhages, venous "
            "beading, or intraretinal microvascular abnormalities are likely present. Urgent referral "
            "to a retina specialist within 2-4 weeks is recommended."
        ),
    },
    'Proliferative DR': {
        'status': 'Proliferative Diabetic Retinopathy',
        'level': 4,
        'color': '#8b0000',
        'explanation': (
            "Proliferative diabetic retinopathy detected — the most advanced stage. "
            "Neovascularization (new abnormal blood vessels) may lead to vitreous hemorrhage or "
            "retinal detachment. Immediate referral for laser photocoagulation or anti-VEGF therapy "
            "is critical."
        ),
    },
}

_model = None


def _load_model():
    global _model
    if _model is not None:
        return _model
    try:
        from utils.model_downloader import ensure_model
        ensure_model(MODEL_PATH, 'diabetic_retinopathy_resnet18.pth')
    except Exception:
        pass
    if not os.path.isfile(MODEL_PATH):
        raise FileNotFoundError(
            f"Retinopathy model not found: {MODEL_PATH}. "
            "Upload models to HF Hub and redeploy."
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

            if is_dicom_file(file.filename):
                raw_image = parse_dicom(file.stream)
            else:
                raw_image = Image.open(file.stream).convert('RGB')

            input_tensor = eval_transform(raw_image).unsqueeze(0).to(DEVICE)

            with torch.no_grad():
                output = model(input_tensor)
                probs = F.softmax(output, dim=1)[0]
                pred_idx = int(probs.argmax().item())
                confidence = float(probs[pred_idx].item())
                pred_class = CLASS_NAMES[pred_idx]

            probs_np = probs.cpu().numpy()
            info = SEVERITY_INFO.get(pred_class, SEVERITY_INFO['No DR'])
            cancer_status = info['status']
            explanation = info['explanation']

            # Grad-CAM
            cam = gradcam(input_tensor, pred_idx)
            processed_np = input_tensor.squeeze(0).permute(1, 2, 0).cpu().numpy()
            processed_np = processed_np * np.array([0.229, 0.224, 0.225]) + np.array([0.485, 0.456, 0.406])
            processed_np = np.clip(processed_np, 0, 1)

            cam_resized = cv2.resize(cam, (raw_image.size[0], raw_image.size[1]))
            heatmap = cv2.applyColorMap(np.uint8(255 * cam_resized), cv2.COLORMAP_JET)
            heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB) / 255.0
            overlay = 0.5 * np.array(raw_image) / 255.0 + 0.5 * heatmap
            overlay = np.clip(overlay, 0, 1)

            fig, axes = plt.subplots(1, 3, figsize=(18, 6))
            axes[0].imshow(raw_image)
            axes[0].set_title(f"Fundus Image\n{pred_class} ({confidence*100:.1f}%)")
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
            fig2 = plt.figure(figsize=(10, 5))
            severity_colors = [SEVERITY_INFO[c]['color'] for c in CLASS_NAMES]
            sns.barplot(x=CLASS_NAMES, y=probs_np, palette=severity_colors)
            plt.ylim(0, 1)
            plt.title(f"DR Severity Distribution (Predicted: {pred_class})")
            plt.ylabel("Probability")
            plt.xticks(rotation=15)
            plt.grid(axis='y', alpha=0.3)
            prob_plot_b64 = fig_to_base64(fig2)

            # Ensemble
            ensemble_results = None
            if request.form.get('ensemble') == 'true':
                models_dict = load_ensemble_models('diabetic_retinopathy', len(CLASS_NAMES), os.path.dirname(__file__))
                if models_dict:
                    ensemble_results = ensemble_predict(input_tensor, models_dict, CLASS_NAMES)

            report = {
                'filename': file.filename,
                'predicted_class': pred_class,
                'confidence': str(confidence),
                'cancer_status': cancer_status,
                'severity_level': info['level'],
                'severity_color': info['color'],
                'prob_plot': f'data:image/png;base64,{prob_plot_b64}',
                'results_plot': f'data:image/png;base64,{results_plot_b64}',
                'explanation': explanation,
                'low_confidence': confidence < LOW_CONFIDENCE_THRESHOLD,
                'probabilities': [(CLASS_NAMES[i], float(probs_np[i])) for i in range(len(CLASS_NAMES))],
                'ensemble_results': ensemble_results,
            }
            save_prediction(request.user['_id'], 'diabetic_retinopathy', report, patient_id=patient_id)
            return render_template('diabetic_retinopathy.html', report=report)

        except Exception as e:
            flash(f'Error processing image: {str(e)}')
            return redirect(request.url)

    patients = list(db.patients.find({"doctor_id": request.user['_id']}).sort("name", 1))
    return render_template('diabetic_retinopathy.html', patients=patients)


@bp.route('/download_report', methods=['POST'])
@login_required
def download_report():
    data = {
        'predicted_class': request.form.get('predicted_class', ''),
        'confidence': request.form.get('confidence', ''),
        'cancer_status': request.form.get('cancer_status', ''),
        'filename': request.form.get('filename', 'fundus_image'),
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
    pdf_bytes = generate_detailed_report(data, 'Diabetic Retinopathy Screening')
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name='deepscanx_diabetic_retinopathy_report.pdf'
    )
