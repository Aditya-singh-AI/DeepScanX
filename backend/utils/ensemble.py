"""
utils/ensemble.py — Multi-model ensembling for DeepScanX AI
Runs inference through ResNet-18, EfficientNet-B0, and DenseNet-121,
then uses a voting system for the final prediction.
"""
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models
import numpy as np
from collections import Counter

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_model_cache = {}


def _build_resnet18(num_classes):
    m = models.resnet18(weights=None)
    m.fc = nn.Linear(m.fc.in_features, num_classes)
    return m


def _build_efficientnet(num_classes):
    """Build EfficientNet-B0 with custom classifier."""
    try:
        m = models.efficientnet_b0(weights=None)
        m.classifier[-1] = nn.Linear(m.classifier[-1].in_features, num_classes)
    except Exception:
        # Fallback if efficientnet not available in torchvision version
        m = models.resnet34(weights=None)
        m.fc = nn.Linear(m.fc.in_features, num_classes)
    return m


def _build_densenet121(num_classes):
    m = models.densenet121(weights=None)
    m.classifier = nn.Linear(m.classifier.in_features, num_classes)
    return m


MODEL_BUILDERS = {
    'resnet18': _build_resnet18,
    'efficientnet_b0': _build_efficientnet,
    'densenet121': _build_densenet121,
}


def load_ensemble_models(module_name: str, num_classes: int, model_dir: str) -> dict:
    """
    Load all ensemble models for a given module.
    Expects weight files named: {module_name}_{arch}.pth
    Falls back gracefully if a model file is missing.
    """
    cache_key = f"{module_name}_{num_classes}"
    if cache_key in _model_cache:
        return _model_cache[cache_key]

    loaded = {}
    for arch_name, builder in MODEL_BUILDERS.items():
        weight_file = os.path.join(model_dir, f"{module_name}_{arch_name}.pth")
        if not os.path.isfile(weight_file):
            continue
        try:
            m = builder(num_classes)
            state = torch.load(weight_file, map_location=DEVICE)
            if isinstance(state, dict) and 'model_state_dict' in state:
                m.load_state_dict(state['model_state_dict'])
            else:
                m.load_state_dict(state)
            m = m.to(DEVICE)
            m.eval()
            loaded[arch_name] = m
        except Exception:
            continue

    _model_cache[cache_key] = loaded
    return loaded


def ensemble_predict(image_tensor, models_dict: dict, class_names: list) -> dict:
    """
    Run image through all models and produce an ensemble prediction.

    Returns:
        {
            'individual': [
                {'model': 'resnet18', 'predicted_class': ..., 'confidence': ..., 'probabilities': [...]},
                ...
            ],
            'ensemble_prediction': str,
            'ensemble_confidence': float,
            'ensemble_probabilities': [(class, prob), ...],
            'agreement_ratio': float,   # e.g. 1.0 if all agree
            'num_models': int,
        }
    """
    if not models_dict:
        return None

    image_tensor = image_tensor.to(DEVICE)
    individual_results = []
    all_probs = []
    predictions = []

    for arch_name, model in models_dict.items():
        try:
            with torch.no_grad():
                output = model(image_tensor)
                probs = F.softmax(output, dim=1)[0].cpu().numpy()
                pred_idx = int(np.argmax(probs))
                pred_class = class_names[pred_idx]
                confidence = float(probs[pred_idx])

                individual_results.append({
                    'model': arch_name,
                    'predicted_class': pred_class,
                    'confidence': confidence,
                    'probabilities': [(class_names[i], float(probs[i])) for i in range(len(class_names))],
                })
                all_probs.append(probs)
                predictions.append(pred_class)
        except Exception:
            continue

    if not individual_results:
        return None

    # Average probabilities across models
    avg_probs = np.mean(all_probs, axis=0)
    avg_probs = avg_probs / (avg_probs.sum() + 1e-8)  # re-normalize

    # Majority vote
    vote_counts = Counter(predictions)
    ensemble_pred = vote_counts.most_common(1)[0][0]
    ensemble_pred_idx = class_names.index(ensemble_pred)
    ensemble_conf = float(avg_probs[ensemble_pred_idx])

    # Agreement ratio
    most_common_count = vote_counts.most_common(1)[0][1]
    agreement = most_common_count / len(predictions)

    return {
        'individual': individual_results,
        'ensemble_prediction': ensemble_pred,
        'ensemble_confidence': ensemble_conf,
        'ensemble_probabilities': [(class_names[i], float(avg_probs[i])) for i in range(len(class_names))],
        'agreement_ratio': agreement,
        'num_models': len(individual_results),
    }
