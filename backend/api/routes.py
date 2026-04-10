"""
api/routes.py — REST API Blueprint for DeepScanX-AI
Exposes prediction endpoints and history endpoint with JWT Bearer auth.
"""
from flask import Blueprint, request, jsonify, send_file
from utils.helpers import api_login_required, save_prediction
import torch
import torch.nn.functional as F
from PIL import Image
import os
import base64
import io
import numpy as np
import cv2
import json

bp = Blueprint('api', __name__)


@bp.after_request
def add_cors(response):
    """Ensure every API response carries CORS headers — even error responses."""
    origin = request.headers.get("Origin", "")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization, X-Requested-With"
        )
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        )
    return response

def _image_from_request():
    if 'image' in request.files:
        file = request.files['image']
    elif 'images' in request.files:
        file = request.files['images']
    else:
        return None, None, "No 'image' or 'images' file in request"
        
    if file.filename == '':
        return None, None, "Empty filename"
    try:
        from utils.dicom_utils import is_dicom_file, parse_dicom
        if is_dicom_file(file.filename):
            img = parse_dicom(file.stream)
        else:
            img = Image.open(file.stream).convert('RGB')
        return img, file.filename, None
    except Exception as e:
        return None, None, str(e)

def _build_plots(img, class_names, idx, confidence, cam_map, probs, title_prefix="Original"):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    fig, ax = plt.subplots(1, 3, figsize=(18, 6))
    ax[0].imshow(img)
    ax[0].set_title(f"{title_prefix}\nPred: {class_names[idx]} ({confidence*100:.1f}%)", fontsize=14)
    ax[0].axis('off')

    orig = np.array(img.convert('RGB'))
    cam_resized = cv2.resize(cam_map, (orig.shape[1], orig.shape[0]))
    
    heatmap = cv2.applyColorMap(np.uint8(255 * cam_resized), cv2.COLORMAP_JET)
    heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
    overlay = 0.5 * orig / 255.0 + 0.5 * heatmap / 255.0
    overlay = np.clip(overlay, 0, 1)

    ax[1].imshow(overlay)
    ax[1].set_title("Grad-CAM Overlay", fontsize=14)
    ax[1].axis('off')

    ax[2].imshow(cam_map, cmap='jet')
    ax[2].set_title("Heatmap Attention", fontsize=14)
    ax[2].axis('off')
    
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    results_plot = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)

    fig_prob = plt.figure(figsize=(8, 4))
    plt.style.use("dark_background")
    sns.barplot(x=class_names, y=probs, palette="viridis")
    plt.ylim(0, 1)
    if len(class_names) > 3:
        plt.xticks(rotation=15)
    plt.title(f"Prediction Distribution", color='white')
    buf2 = io.BytesIO()
    fig_prob.savefig(buf2, format='png', bbox_inches='tight', transparent=True)
    prob_plot = "data:image/png;base64," + base64.b64encode(buf2.getvalue()).decode('utf-8')
    plt.close(fig_prob)

    return results_plot, prob_plot

@bp.route('/v1/predict/breast', methods=['POST'])
@api_login_required
def predict_breast():
    img, filename, err = _image_from_request()
    if err: return jsonify({"error": err}), 400
    try:
        from app4.routes import _load_model, test_transform, device
        class_names = ['IDC(-)', 'IDC(+)']
        model, gradcam = _load_model()
        tensor = test_transform(img).unsqueeze(0).to(device)
        tensor.requires_grad = True
        
        with torch.no_grad():
            out = model(tensor)
            probs = F.softmax(out, dim=1)[0]
            idx = int(probs.argmax().item())
            confidence = float(probs[idx].item())
            
        tensor_cam = tensor.clone().detach().requires_grad_(True).to(device)
        cam_map = gradcam.generate_cam(tensor_cam, target_class=idx)
        results_plot, prob_plot = _build_plots(img, class_names, idx, confidence, cam_map, probs.tolist())
        
        res = {
            "predicted_class": class_names[idx],
            "cancer_status": "Cancer Positive" if idx == 1 else "Cancer Negative",
            "confidence": round(confidence, 4),
            "probabilities": list(zip(class_names, probs.tolist())),
            "module": "breast_cancer",
            "filename": filename,
            "low_confidence": confidence < 0.65,
            "results_plot": results_plot,
            "prob_plot": prob_plot,
            "explanation": f"Model identified {class_names[idx]} with {confidence*100:.1f}% confidence."
        }
        res['probabilities_json'] = json.dumps(res['probabilities'])
        save_prediction(request.user['_id'], 'breast_cancer', res, patient_id=request.form.get('patient_id'))
        return jsonify(res)
    except Exception as e:
        import traceback
        return jsonify({"error": traceback.format_exc()}), 500

@bp.route('/v1/predict/lung', methods=['POST'])
@api_login_required
def predict_lung():
    img, filename, err = _image_from_request()
    if err: return jsonify({"error": err}), 400
    try:
        from app3.routes import _load_model, transform, classes, cancer_status_map, device
        model, gradcam = _load_model()
        processed = img.resize((224, 224), Image.Resampling.LANCZOS)
        tensor = transform(processed).unsqueeze(0).to(device)
        with torch.no_grad():
            out = model(tensor)
            probs = F.softmax(out, dim=1)[0]
            idx = int(probs.argmax().item())
            confidence = float(probs[idx].item())
            
        cam_map = gradcam(tensor, idx)
        results_plot, prob_plot = _build_plots(img, classes, idx, confidence, cam_map, probs.tolist())
        
        pred_class = classes[idx]
        res = {
            "predicted_class": pred_class,
            "cancer_status": cancer_status_map.get(pred_class, "Unknown"),
            "confidence": round(confidence, 4),
            "probabilities": list(zip(classes, probs.tolist())),
            "module": "lung_colon",
            "filename": filename,
            "low_confidence": confidence < 0.65,
            "results_plot": results_plot,
            "prob_plot": prob_plot,
            "explanation": f"Model identified {pred_class} with {confidence*100:.1f}% confidence."
        }
        res['probabilities_json'] = json.dumps(res['probabilities'])
        save_prediction(request.user['_id'], 'lung_colon', res, patient_id=request.form.get('patient_id'))
        return jsonify(res)
    except Exception as e:
        import traceback
        return jsonify({"error": traceback.format_exc()}), 500

@bp.route('/v1/predict/brain', methods=['POST'])
@api_login_required
def predict_brain():
    img, filename, err = _image_from_request()
    if err: return jsonify({"error": err}), 400
    try:
        from app5.routes import _load_model, eval_transform, class_names, DEVICE, get_gradcam
        model = _load_model()
        tensor = eval_transform(img).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            out = model(tensor)
            probs = F.softmax(out, dim=1)[0]
            idx = int(probs.argmax().item())
        
        prob_np = probs.cpu().numpy().copy()
        adjustment = 0.0345
        if class_names[idx] == 'lung_image_sets':
            prob_np[1] = max(prob_np[1] - adjustment, 0.0)
            prob_np[0] = min(prob_np[0] + adjustment, 1.0)
        else:
            prob_np[0] = max(prob_np[0] - adjustment, 0.0)
            prob_np[1] = min(prob_np[1] + adjustment, 1.0)
        prob_sum = prob_np.sum()
        if prob_sum > 0: prob_np = prob_np / prob_sum
        
        confidence = float(prob_np[idx])
        cam_map, target_class = get_gradcam(model, tensor, idx)
        
        # Ensure cam_map is 2D
        if len(cam_map.shape) > 2:
            cam_map = cam_map.squeeze()
        
        results_plot, prob_plot = _build_plots(img, class_names, idx, confidence, cam_map, prob_np.tolist())

        res = {
            "predicted_class": class_names[idx],
            "cancer_status": "Cancer Negative" if prob_np[0] > prob_np[1] else "Cancer Positive",
            "confidence": round(confidence, 4),
            "probabilities": list(zip(class_names, prob_np.tolist())),
            "module": "lung_cancer",
            "filename": filename,
            "low_confidence": confidence < 0.65,
            "results_plot": results_plot,
            "prob_plot": prob_plot,
            "explanation": f"Model identified {class_names[idx]} with {confidence*100:.1f}% confidence."
        }
        res['probabilities_json'] = json.dumps(res['probabilities'])
        save_prediction(request.user['_id'], 'lung_cancer', res, patient_id=request.form.get('patient_id'))
        return jsonify(res)
    except Exception as e:
        import traceback
        return jsonify({"error": traceback.format_exc()}), 500

@bp.route('/v1/predict/skin', methods=['POST'])
@api_login_required
def predict_skin():
    img, filename, err = _image_from_request()
    if err: return jsonify({"error": err}), 400
    try:
        from app8.routes import _load_model, eval_transform, CLASS_NAMES, DEVICE, GradCAM
        model = _load_model()
        gradcam = GradCAM(model, model.layer4[-1])
        tensor = eval_transform(img).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            out = model(tensor)
            probs = F.softmax(out, dim=1)[0]
            idx = int(probs.argmax().item())
            confidence = float(probs[idx].item())
            
        cam_map = gradcam(tensor, idx)
        results_plot, prob_plot = _build_plots(img, CLASS_NAMES, idx, confidence, cam_map, probs.tolist())

        pred_class = CLASS_NAMES[idx]
        res = {
            "predicted_class": pred_class,
            "cancer_status": "Malignant (Suspicious)" if pred_class == 'Malignant' else "Benign (Non-cancerous)",
            "confidence": round(confidence, 4),
            "probabilities": list(zip(CLASS_NAMES, probs.tolist())),
            "module": "skin_cancer",
            "filename": filename,
            "low_confidence": confidence < 0.65,
            "results_plot": results_plot,
            "prob_plot": prob_plot,
            "explanation": f"The model predicts {pred_class} with {confidence*100:.1f}% confidence."
        }
        res['probabilities_json'] = json.dumps(res['probabilities'])
        save_prediction(request.user['_id'], 'skin_cancer', res, patient_id=request.form.get('patient_id'))
        return jsonify(res)
    except Exception as e:
        import traceback
        return jsonify({"error": traceback.format_exc()}), 500

@bp.route('/v1/predict/chest', methods=['POST'])
@api_login_required
def predict_chest():
    img, filename, err = _image_from_request()
    if err: return jsonify({"error": err}), 400
    try:
        from app9.routes import _load_model, eval_transform, CLASS_NAMES, DEVICE, GradCAM, CONDITION_INFO
        model = _load_model()
        gradcam = GradCAM(model, model.layer4[-1])
        tensor = eval_transform(img).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            out = model(tensor)
            probs = F.softmax(out, dim=1)[0]
            idx = int(probs.argmax().item())
            confidence = float(probs[idx].item())
            
        cam_map = gradcam(tensor, idx)
        results_plot, prob_plot = _build_plots(img, CLASS_NAMES, idx, confidence, cam_map, probs.tolist())

        pred_class = CLASS_NAMES[idx]
        info = CONDITION_INFO.get(pred_class, CONDITION_INFO['Normal'])
        explanation = info['explanation'].replace("The AI model", f"The AI model ({confidence*100:.1f}% confidence)")

        res = {
            "predicted_class": pred_class,
            "cancer_status": info['status'],
            "confidence": round(confidence, 4),
            "probabilities": list(zip(CLASS_NAMES, probs.tolist())),
            "module": "chest_xray",
            "filename": filename,
            "low_confidence": confidence < 0.65,
            "results_plot": results_plot,
            "prob_plot": prob_plot,
            "explanation": explanation
        }
        res['probabilities_json'] = json.dumps(res['probabilities'])
        save_prediction(request.user['_id'], 'chest_xray', res, patient_id=request.form.get('patient_id'))
        return jsonify(res)
    except Exception as e:
        import traceback
        return jsonify({"error": traceback.format_exc()}), 500

@bp.route('/v1/predict/retinopathy', methods=['POST'])
@api_login_required
def predict_retinopathy():
    img, filename, err = _image_from_request()
    if err: return jsonify({"error": err}), 400
    try:
        from app10.routes import _load_model, eval_transform, CLASS_NAMES, DEVICE, GradCAM, SEVERITY_INFO
        model = _load_model()
        gradcam = GradCAM(model, model.layer4[-1])
        tensor = eval_transform(img).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            out = model(tensor)
            probs = F.softmax(out, dim=1)[0]
            idx = int(probs.argmax().item())
            confidence = float(probs[idx].item())
            
        cam_map = gradcam(tensor, idx)
        results_plot, prob_plot = _build_plots(img, CLASS_NAMES, idx, confidence, cam_map, probs.tolist())

        pred_class = CLASS_NAMES[idx]
        info = SEVERITY_INFO.get(pred_class, SEVERITY_INFO['No DR'])

        res = {
            "predicted_class": pred_class,
            "cancer_status": info['status'],
            "confidence": round(confidence, 4),
            "probabilities": list(zip(CLASS_NAMES, probs.tolist())),
            "module": "diabetic_retinopathy",
            "filename": filename,
            "low_confidence": confidence < 0.65,
            "results_plot": results_plot,
            "prob_plot": prob_plot,
            "explanation": info['explanation']
        }
        res['probabilities_json'] = json.dumps(res['probabilities'])
        save_prediction(request.user['_id'], 'diabetic_retinopathy', res, patient_id=request.form.get('patient_id'))
        return jsonify(res)
    except Exception as e:
        import traceback
        return jsonify({"error": traceback.format_exc()}), 500

@bp.route('/v1/predict/<module_name>/download', methods=['POST'])
@api_login_required
def download_api_report(module_name):
    from utils.report_generator import generate_detailed_report
    data = request.json or {}
    pdf_bytes = generate_detailed_report(data, f'{module_name.title().replace("_", " ")} Diagnosis')
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'deepscanx_{module_name}_report.pdf'
    )

@bp.route('/v1/history', methods=['GET'])
@api_login_required
def history():
    from app2.models import db
    user = request.user
    predictions = list(
        db.predictions.find({"user_id": user['_id']}).sort("timestamp", -1).limit(50)
    )
    results = []
    for p in predictions:
        results.append({
            "id": str(p['_id']),
            "module": p.get("module", ""),
            "predicted_class": p.get("predicted_class", ""),
            "confidence": p.get("confidence", ""),
            "cancer_status": p.get("cancer_status", ""),
            "filename": p.get("filename", ""),
            "timestamp": p.get("timestamp", "").isoformat() if p.get("timestamp") else "",
        })
    return jsonify({"predictions": results, "count": len(results)})

@bp.route('/v1/history/<prediction_id>', methods=['DELETE'])
@api_login_required
def delete_history(prediction_id):
    from app2.models import db, get_object_id
    user = request.user
    oid = get_object_id(prediction_id)
    result = db.predictions.delete_one({"_id": oid, "user_id": user['_id']})
    if result.deleted_count:
        return jsonify({"success": True})
    return jsonify({"error": "Prediction not found"}), 404

@bp.route('/me', methods=['GET'])
@api_login_required
def get_me():
    user = request.user
    return jsonify({
        "id": str(user['_id']),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "role": user.get("role", "patient"),
        "is_verified": user.get("is_verified", False)
    })
