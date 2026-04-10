# routes.py — Breast Cancer IDC Detection
from flask import Blueprint, render_template, redirect, url_for, request, current_app, send_file, flash
from utils.helpers import login_required, save_prediction
from utils.report_generator import generate_detailed_report
from utils.dicom_utils import is_dicom_file, parse_dicom
from utils.ensemble import load_ensemble_models, ensemble_predict
from app2.models import db, get_object_id
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms, models
from PIL import Image
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import io
import json
import base64
import os
import cv2

LOW_CONFIDENCE_THRESHOLD = 0.65

bp = Blueprint(
    'app4',
    __name__,
    template_folder='templates',
    static_folder='static'
)

# ------------------------
# ResNet-18 Model
# ------------------------
class ResNetModel(nn.Module):
    def __init__(self, num_classes=2):
        super(ResNetModel, self).__init__()
        self.resnet = models.resnet18(pretrained=False)
        num_ftrs = self.resnet.fc.in_features
        self.resnet.fc = nn.Linear(num_ftrs, num_classes)

    def forward(self, x):
        return self.resnet(x)

# ------------------------
# Grad-CAM Implementation
# ------------------------
class GradCAM:
    def __init__(self, model, target_layer=None, device='cpu'):
        self.model = model
        self.model.eval()
        self.device = device
        if target_layer is None:
            target_layer = self.model.resnet.layer4
        self.target_layer = target_layer
        self.activations = None
        self.gradients = None

        def forward_hook(module, input, output):
            self.activations = output.detach()

        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach()

        if isinstance(self.target_layer, nn.Sequential):
            module_to_hook = self.target_layer[-1]
        else:
            module_to_hook = self.target_layer

        module_to_hook.register_forward_hook(forward_hook)
        module_to_hook.register_backward_hook(backward_hook)

    def generate_cam(self, input_tensor, target_class=None):
        output = self.model(input_tensor)
        if target_class is None:
            target_class = int(output.argmax(dim=1).item())
        self.model.zero_grad()
        score = output[0, target_class]
        score.backward(retain_graph=True)

        if self.activations is None or self.gradients is None:
            raise RuntimeError("Grad-CAM hooks did not collect activations/gradients.")

        activations = self.activations[0]
        gradients = self.gradients[0]

        weights = gradients.mean(dim=(1, 2))
        cam = torch.zeros(activations.shape[1:], dtype=torch.float32).to(self.device)
        for i, w in enumerate(weights):
            cam += w * activations[i]

        cam = F.relu(cam)
        cam_np = cam.cpu().numpy()
        if cam_np.max() != 0:
            cam_np = cam_np - cam_np.min()
            cam_np = cam_np / (cam_np.max() + 1e-9)
        else:
            cam_np = np.zeros_like(cam_np)

        return cam_np

# ------------------------
# Device setup
# ------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ------------------------
# Image transforms
# ------------------------
test_transform = transforms.Compose([
    transforms.Resize((50, 50)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

# ------------------------
# Load trained model (lazy)
# ------------------------
model_path = os.path.join(os.path.dirname(__file__), 'breast_cancer_cnn_model_updated.pth')
_model = None
_gradcam = None

def _load_model():
    global _model, _gradcam
    if _model is not None:
        return _model, _gradcam
    try:
        from utils.model_downloader import ensure_model
        ensure_model(model_path, 'breast_cancer_cnn_model_updated.pth')
    except Exception:
        pass
    if not os.path.isfile(model_path):
        raise FileNotFoundError(
            f"Breast cancer model not found: {model_path}. "
            "Upload models to HF Hub and redeploy."
        )
    m = ResNetModel(num_classes=2).to(device)
    m.load_state_dict(torch.load(model_path, map_location=device))
    m.eval()
    _model = m
    _gradcam = GradCAM(model=m, target_layer=m.resnet.layer4, device=device)
    return _model, _gradcam

# ------------------------
# Helpers
# ------------------------
def plot_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    return img_base64

def create_cam_overlay(original_pil, cam_map, out_path, alpha=0.5, colormap=cv2.COLORMAP_JET):
    orig = np.array(original_pil)
    orig_bgr = orig[..., ::-1].copy()
    cam_resized = cv2.resize(cam_map, (orig.shape[1], orig.shape[0]))
    cam_uint8 = np.uint8(255 * cam_resized)
    heatmap = cv2.applyColorMap(cam_uint8, colormap)
    overlay_bgr = cv2.addWeighted(heatmap, alpha, orig_bgr, 1 - alpha, 0)
    overlay_rgb = overlay_bgr[..., ::-1]
    overlay_pil = Image.fromarray(overlay_rgb)
    overlay_pil.save(out_path)
    return out_path

# ------------------------
# Main route
# ------------------------
@bp.route('/', methods=['GET', 'POST'])
@login_required
def page():
    if request.method == 'POST':
        if 'images' not in request.files:
            return render_template('home3.html', error="No image uploaded")

        files = request.files.getlist('images')
        if len(files) == 0:
            return render_template('home3.html', error="No image selected")

        # Get optional fields
        patient_id = request.form.get('patient_id', '').strip() or None
        doctor_notes = request.form.get('doctor_notes', '').strip()

        results = []

        for file in files:
            if file and file.filename != '':
                try:
                    model, gradcam = _load_model()

                    # Save uploaded image
                    upload_folder = os.path.join(current_app.static_folder, 'uploads')
                    os.makedirs(upload_folder, exist_ok=True)
                    image_filename = file.filename

                    # ── Load image (DICOM or standard) ──
                    if is_dicom_file(file.filename):
                        image = parse_dicom(file.stream)
                        # Save the converted image for cam overlay
                        image_path = os.path.join(upload_folder, image_filename + '.png')
                        image.save(image_path)
                    else:
                        image_path = os.path.join(upload_folder, image_filename)
                        file.save(image_path)
                        image = Image.open(image_path).convert('RGB')

                    # Preprocess
                    preprocessed_image = test_transform(image).unsqueeze(0).to(device)

                    # Predict
                    with torch.no_grad():
                        outputs = model(preprocessed_image)
                        probs = F.softmax(outputs, dim=1)
                        confidence, predicted = torch.max(probs, 1)
                        class_names = ['IDC(-)', 'IDC(+)']
                        predicted_class = class_names[predicted.item()]
                        cancer_status = "Cancer Positive" if predicted_class == "IDC(+)" else "Cancer Negative"

                        prob_idc_neg, prob_idc_pos = probs[0][0].item(), probs[0][1].item()

                    # Grad-CAM
                    input_tensor_for_grad = preprocessed_image.clone().detach().to(device)
                    input_tensor_for_grad.requires_grad = True
                    outputs_for_grad = model(input_tensor_for_grad)
                    pred_idx = int(outputs_for_grad.argmax(dim=1).item())
                    cam_map = gradcam.generate_cam(input_tensor_for_grad, target_class=pred_idx)
                    cam_filename = f"cam_{os.path.splitext(image_filename)[0]}.png"
                    cam_path = os.path.join(upload_folder, cam_filename)
                    create_cam_overlay(image, cam_map, cam_path, alpha=0.5)

                    # ── Ensemble (if available) ──
                    ensemble_results = None
                    models_dict = load_ensemble_models('breast_cancer', 2, os.path.dirname(__file__))
                    if models_dict:
                        ensemble_results = ensemble_predict(preprocessed_image, models_dict, class_names)

                    # Explanation
                    heat_strength = cam_map.mean()
                    heat_phrase = "strong localized regions" if heat_strength > 0.35 else "moderate regions" if heat_strength > 0.15 else "diffuse regions"
                    if predicted_class == "IDC(+)":
                        explanation_text = (
                            f"The model predicts **Cancer Positive (IDC+)** with a confidence of {confidence.item()*100:.2f}%. "
                            f"This indicates the presence of Invasive Ductal Carcinoma (IDC), a common type of breast cancer where abnormal cells are detected in the breast tissue. "
                            f"The prediction is based on patterns identified in the image by a deep learning model (ResNet-18), which was trained on histopathology images to distinguish between cancerous and non-cancerous tissues. "
                            f"The Grad-CAM visualization shows {heat_phrase} of focus, highlighting areas in the image that the model considers most indicative of cancer. "
                            f"Brighter regions in the heatmap suggest higher importance in the model's decision. "
                            f"Please note that this is an automated prediction and should not be considered a definitive diagnosis. Consult a medical professional for a comprehensive evaluation."
                        )
                    else:
                        explanation_text = (
                            f"The model predicts **Cancer Negative (IDC-)** with a confidence of {confidence.item()*100:.2f}%. "
                            f"This suggests that the image does not show signs of Invasive Ductal Carcinoma (IDC), indicating the absence of cancerous cells in the analyzed tissue. "
                            f"The prediction is made by a deep learning model (ResNet-18) trained to identify patterns in histopathology images. "
                            f"The Grad-CAM visualization shows {heat_phrase} of focus, indicating the areas the model analyzed to make this prediction. "
                            f"Brighter regions in the heatmap highlight areas of interest, though in this case, they support a non-cancerous prediction. "
                            f"While this result is encouraging, it is not a substitute for a professional medical diagnosis. Please consult a healthcare provider for confirmation."
                        )

                    # Image plots
                    fig_img = plt.figure(figsize=(8, 4))
                    plt.subplot(1, 3, 1)
                    plt.imshow(image)
                    plt.title(f"Original Image\nPrediction: {predicted_class} ({confidence.item():.2f})")
                    plt.axis('off')

                    preprocessed_img_np = preprocessed_image.squeeze(0).permute(1, 2, 0).cpu().numpy()
                    preprocessed_img_np = preprocessed_img_np * 0.5 + 0.5
                    preprocessed_img_np = np.clip(preprocessed_img_np, 0, 1)
                    plt.subplot(1, 3, 2)
                    plt.imshow(preprocessed_img_np)
                    plt.title("Preprocessed Image")
                    plt.axis('off')

                    cam_display = Image.open(cam_path).convert('RGB')
                    plt.subplot(1, 3, 3)
                    plt.imshow(cam_display)
                    plt.title("Grad-CAM Overlay")
                    plt.axis('off')

                    plt.tight_layout()
                    image_plot = plot_to_base64(fig_img)
                    plt.close(fig_img)

                    # Probability plot
                    fig_prob = plt.figure(figsize=(5, 3))
                    prob_classes = ['IDC(-)', 'IDC(+)']
                    probabilities = [prob_idc_neg, prob_idc_pos]
                    sns.barplot(x=probabilities, y=prob_classes)
                    plt.xlim(0, 1)
                    plt.xlabel("Probability")
                    plt.title("Prediction Probability Distribution")
                    prob_plot = plot_to_base64(fig_prob)
                    plt.close(fig_prob)

                    # Append result
                    results.append({
                        "filename": image_filename,
                        "predicted_class": predicted_class,
                        "cancer_status": cancer_status,
                        "confidence": f"{confidence.item():.4f}",
                        "prob_idc_neg": f"{prob_idc_neg:.4f}",
                        "prob_idc_pos": f"{prob_idc_pos:.4f}",
                        "image_plot": image_plot,
                        "prob_plot": prob_plot,
                        "uploaded_image": f"uploads/{image_filename}",
                        "cam_image": f"uploads/{cam_filename}",
                        "explanation_text": explanation_text,
                        "low_confidence": confidence.item() < LOW_CONFIDENCE_THRESHOLD,
                        "probabilities": [("IDC(-)", prob_idc_neg), ("IDC(+)", prob_idc_pos)],
                        "ensemble_results": ensemble_results,
                    })
                    save_prediction(request.user['_id'], 'breast_cancer', results[-1], patient_id=patient_id)

                except Exception as e:
                    return render_template('home3.html', error=f"Error processing image {file.filename}: {str(e)}")

        # Fetch patients for dropdown
        patients = list(db.patients.find({"doctor_id": request.user['_id']}).sort("name", 1))
        return render_template('home3.html', results=results, patients=patients)

    # GET
    patients = list(db.patients.find({"doctor_id": request.user['_id']}).sort("name", 1))
    return render_template('home3.html', patients=patients)


@bp.route('/download_report', methods=['POST'])
@login_required
def download_report():
    data = {
        'predicted_class': request.form.get('predicted_class', ''),
        'confidence': request.form.get('confidence', ''),
        'cancer_status': request.form.get('cancer_status', ''),
        'filename': request.form.get('filename', 'breast_scan'),
        'explanation_text': request.form.get('explanation_text', ''),
        'doctor_notes': request.form.get('doctor_notes', ''),
    }
    try:
        data['probabilities'] = json.loads(request.form.get('probabilities_json', '[]'))
    except Exception:
        data['probabilities'] = []
    try:
        data['ensemble_results'] = json.loads(request.form.get('ensemble_json', '{}')) or None
    except Exception:
        data['ensemble_results'] = None
    pdf_bytes = generate_detailed_report(data, 'Breast Cancer IDC Detection')
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name='deepscanx_breast_cancer_report.pdf'
    )