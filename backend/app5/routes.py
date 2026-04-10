from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file
from utils.helpers import login_required, save_prediction
from utils.report_generator import generate_detailed_report
from utils.dicom_utils import is_dicom_file, parse_dicom
from utils.ensemble import load_ensemble_models, ensemble_predict
from app2.models import db, get_object_id
import torch
from torchvision import transforms, models
from PIL import Image, ImageEnhance
import torch.nn.functional as F
import io
import json
import numpy as np
import cv2
import matplotlib.pyplot as plt
import seaborn as sns
import torch.nn as nn
import base64
import os

LOW_CONFIDENCE_THRESHOLD = 0.65


bp = Blueprint('app5', __name__, template_folder='templates')

# Config
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_SAVE_PATH = os.path.join(os.path.dirname(__file__), "lung_cancer_prediction_20250821_150505.pth")
IMG_SIZE = 224
class_names = ['Cancer -', ' Cancer +']  # Cancer -, Cancer +

# Load the model lazily when first needed
_model = None

def _load_model():
    global _model
    if _model is not None:
        return _model
    try:
        from utils.model_downloader import ensure_model
        ensure_model(MODEL_SAVE_PATH, 'lung_cancer_prediction_20250821_150505.pth')
    except Exception:
        pass
    if not os.path.isfile(MODEL_SAVE_PATH):
        raise FileNotFoundError(
            f"Brain tumor model not found: {MODEL_SAVE_PATH}. "
            "Upload models to HF Hub and redeploy."
        )
    m = models.resnet18(weights=None)
    in_features = m.fc.in_features
    m.fc = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(in_features, 256),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(256, len(class_names))
    )
    checkpoint = torch.load(MODEL_SAVE_PATH, map_location=DEVICE)
    m.load_state_dict(checkpoint['model_state_dict'])
    m = m.to(DEVICE)
    m.eval()
    _model = m
    return _model

# Advanced preprocessing
def advanced_preprocess(image):
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.2)
    return image

eval_transform = transforms.Compose([
    transforms.Lambda(advanced_preprocess),
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.GaussianBlur(kernel_size=3, sigma=0.5),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# Grad-CAM implementation
def get_gradcam(model, image_tensor, target_class=None):
    model.eval()
    gradients = []
    activations = []

    def backward_hook(module, grad_in, grad_out):
        gradients.append(grad_out[0].detach())

    def forward_hook(module, input, output):
        activations.append(output.detach())

    target_layer = model.layer4[-1].conv2
    forward_handle = target_layer.register_forward_hook(forward_hook)
    backward_handle = target_layer.register_backward_hook(backward_hook)

    try:
        output = model(image_tensor)
        if target_class is None:
            target_class = output.argmax(dim=1).item()

        model.zero_grad()
        one_hot = torch.zeros_like(output)
        one_hot[0][target_class] = 1
        output.backward(gradient=one_hot)

        if not gradients or not activations:
            raise ValueError("Gradients or activations not captured.")

        gradient = gradients[0].cpu().numpy()
        activation = activations[0].cpu().numpy()
        g = gradient[0]
        a = activation[0]
        weights = np.mean(g, axis=(1, 2))[:, np.newaxis, np.newaxis]
        gradcam = np.sum(weights * a, axis=0)
        gradcam = np.maximum(gradcam, 0)
        gradcam = gradcam / (np.max(gradcam) + 1e-8)
        return gradcam, target_class
    finally:
        forward_handle.remove()
        backward_handle.remove()

# Generate base64 image from matplotlib figure
def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    base64_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return base64_str

# Plot probability distribution and return base64
def get_probability_distribution_base64(probs, class_names, pred_class):
    plt.style.use("dark_background")
    fig = plt.figure(figsize=(8, 5))
    sns.barplot(x=class_names, y=probs, palette="viridis")
    plt.ylim(0, 1)
    plt.xlabel("Class", fontsize=12, color="white")
    plt.ylabel("Probability", fontsize=12, color="white")
    plt.title(f"Prediction Probability Distribution\n(Predicted: {pred_class})",
              fontsize=14, color="white")
    plt.grid(True, axis='y', linestyle='--', alpha=0.5)
    plt.xticks(rotation=45, ha='right', color="white")
    plt.yticks(color="white")
    base64_str = fig_to_base64(fig)
    plt.close(fig)
    return base64_str

# Plot results with Grad-CAM and return base64
def get_results_plot_base64(original_img, processed_img, gradcam_map, pred_class, confidence, cancer_status):
    processed_img = processed_img.squeeze(0).permute(1, 2, 0).detach().cpu().numpy()
    processed_img = processed_img * np.array([0.229, 0.224, 0.225]) + np.array([0.485, 0.456, 0.406])
    processed_img = np.clip(processed_img, 0, 1)

    cam_resized = cv2.resize(gradcam_map, (original_img.size[0], original_img.size[1]))
    heatmap = cv2.applyColorMap(np.uint8(255 * cam_resized), cv2.COLORMAP_JET)
    heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
    heatmap = heatmap / 255.0
    overlay = 0.5 * np.array(original_img) / 255.0 + 0.5 * heatmap
    overlay = np.clip(overlay, 0, 1)

    threshold = np.percentile(cam_resized, 95)
    important_regions = cam_resized > threshold

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    axes[0].imshow(original_img)
    axes[0].set_title(f"Original Image\n{pred_class} ({confidence*100:.2f}%)\n{cancer_status}", fontsize=12)
    axes[0].axis('off')

    axes[1].imshow(processed_img)
    axes[1].set_title("Processed Image", fontsize=12)
    axes[1].axis('off')

    axes[2].imshow(overlay)
    axes[2].set_title("Grad-CAM Heatmap\n(Red = High Importance)", fontsize=12)
    axes[2].imshow(important_regions, cmap='Reds', alpha=0.3)
    axes[2].text(10, 20, f"Top 5% Importance: {threshold:.3f}", color='white', fontsize=10, bbox=dict(facecolor='black', alpha=0.7))
    axes[2].axis('off')

    plt.tight_layout()
    base64_str = fig_to_base64(fig)
    return base64_str


@bp.route('/', methods=['GET', 'POST'])
@login_required
def page():
    if request.method == 'POST':
        if 'images' not in request.files:
            flash('No file part')
            return redirect(request.url)
        files = request.files.getlist('images')
        if not files or all(file.filename == '' for file in files):
            flash('No selected files')
            return redirect(request.url)

        # Get optional fields
        patient_id = request.form.get('patient_id', '').strip() or None
        doctor_notes = request.form.get('doctor_notes', '').strip()

        results = []
        for file in files:
            try:
                model = _load_model()

                # ── Load image (DICOM or standard) ──
                if is_dicom_file(file.filename):
                    image = parse_dicom(file.stream)
                else:
                    image = Image.open(file.stream).convert('RGB')

                input_tensor = eval_transform(image).unsqueeze(0)
                input_tensor = input_tensor.to(DEVICE)

                # Inference
                with torch.no_grad():
                    output = model(input_tensor)
                    probabilities = F.softmax(output, dim=1)[0]
                    predicted_prob, predicted_idx = torch.max(probabilities, 0)
                    predicted_class = class_names[predicted_idx.item()]
                    cancer_status = 'Cancer - (negative)' if predicted_class == 'colon_image_sets' else 'Cancer + (positive)'

                # Adjust probabilities
                prob_np = probabilities.cpu().numpy().copy()
                adjustment = 0.0345
                if predicted_class == 'lung_image_sets':
                    prob_np[1] = max(prob_np[1] - adjustment, 0.0)
                    prob_np[0] = min(prob_np[0] + adjustment, 1.0)
                else:
                    prob_np[0] = max(prob_np[0] - adjustment, 0.0)
                    prob_np[1] = min(prob_np[1] + adjustment, 1.0)
                prob_sum = prob_np.sum()
                if prob_sum > 0:
                    prob_np = prob_np / prob_sum
                probabilities = torch.tensor(prob_np)
                predicted_prob = probabilities[predicted_idx.item()]
                cancer_status = 'Cancer - (negative)' if prob_np[0] > prob_np[1] else 'Cancer + (positive)'

                # Compute Grad-CAM
                gradcam_map, target_class = get_gradcam(model, input_tensor, predicted_idx.item())

                # ── Ensemble (if available) ──
                ensemble_results = None
                models_dict = load_ensemble_models('lung_cancer', len(class_names), os.path.dirname(__file__))
                if models_dict:
                    ensemble_results = ensemble_predict(input_tensor, models_dict, class_names)

                # Generate plots as base64
                prob_plot_base64 = get_probability_distribution_base64(probabilities.numpy(), class_names, predicted_class)
                results_plot_base64 = get_results_plot_base64(image, input_tensor, gradcam_map, predicted_class, predicted_prob.item(), cancer_status)

                # Human explanations
                explanation = ""
                if prob_np[1] > prob_np[0]:
                    explanation = "Based on the analysis, the image shows clear indications of cancer-positive features, typically associated with lung tissue abnormalities. This means the model detects patterns consistent with cancerous cells in the lung biopsy. Please consult a medical professional for a definitive diagnosis, as this is an AI-assisted tool and not a replacement for expert medical advice."
                else:
                    explanation = "From the test results, we can conclude that the image appears to be cancer-negative, resembling colon tissue patterns without evident cancerous features. However, always seek confirmation from a healthcare provider, as AI predictions are supportive and not conclusive."

                additional_explanation = """
                <h3>Understanding the Results:</h3>
                <p><strong>Predicted Class and Confidence:</strong> The model predicts the image as belonging to '{}' with a confidence of {:.2f}%. This translates to a {} status for cancer.</p>
                <p><strong>Probability Scores:</strong></p>
                <ul>
                    <li>Colon (Cancer -): {:.4f}</li>
                    <li>Lung (Cancer +): {:.4f}</li>
                </ul>
                <p><strong>Grad-CAM Heatmap:</strong> This visualization highlights the regions in the image that the model focused on for its prediction. Red areas indicate high importance, showing where the model detected key features (e.g., abnormal cell structures in cancer-positive cases).</p>
                <p><strong>Important Note:</strong> This tool uses a deep learning model trained on histopathological images to differentiate between colon (non-cancerous reference) and lung (cancerous) datasets. It provides an educational and supportive analysis but should not be used for self-diagnosis. Always consult a doctor for health concerns.</p>
                """.format(predicted_class, predicted_prob.item() * 100, cancer_status, prob_np[0], prob_np[1])

                results.append({
                    'filename': file.filename,
                    'prob_plot': f'data:image/png;base64,{prob_plot_base64}',
                    'results_plot': f'data:image/png;base64,{results_plot_base64}',
                    'explanation': explanation,
                    'additional_explanation': additional_explanation,
                    'predicted_class': predicted_class,
                    'confidence': str(predicted_prob.item()),
                    'cancer_status': cancer_status,
                    'low_confidence': predicted_prob.item() < LOW_CONFIDENCE_THRESHOLD,
                    'probabilities': [(class_names[0], float(prob_np[0])), (class_names[1], float(prob_np[1]))],
                    'ensemble_results': ensemble_results,
                })
                save_prediction(request.user['_id'], 'lung_cancer', results[-1], patient_id=patient_id)

            except Exception as e:
                flash(f'Error processing image {file.filename}: {str(e)}')
                continue

        if results:
            patients = list(db.patients.find({"doctor_id": request.user['_id']}).sort("name", 1))
            return render_template('home4.html', results=results, patients=patients)
        return redirect(request.url)

    # GET
    patients = list(db.patients.find({"doctor_id": request.user['_id']}).sort("name", 1))
    return render_template('home4.html', patients=patients)


@bp.route('/download_report', methods=['POST'])
@login_required
def download_report():
    data = {
        'predicted_class': request.form.get('predicted_class', ''),
        'confidence': request.form.get('confidence', ''),
        'cancer_status': request.form.get('cancer_status', ''),
        'filename': request.form.get('filename', 'lung_scan'),
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
    pdf_bytes = generate_detailed_report(data, 'Lung Cancer Detection')
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name='deepscanx_lung_cancer_report.pdf'
    )
