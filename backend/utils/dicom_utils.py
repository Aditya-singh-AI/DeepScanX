"""
utils/dicom_utils.py — DICOM (.dcm) file support for DeepScanX AI
Parses medical DICOM files and converts them to PIL images for model inference.
"""
import numpy as np
from PIL import Image

DICOM_EXTENSIONS = {'.dcm', '.dicom', '.DCM', '.DICOM'}


def is_dicom_file(filename: str) -> bool:
    """Check if a filename has a DICOM extension."""
    if not filename:
        return False
    from pathlib import Path
    return Path(filename).suffix in DICOM_EXTENSIONS


def parse_dicom(file_stream) -> Image.Image:
    """
    Read a DICOM file stream and return a PIL RGB Image.
    Applies window/level normalization when available.
    """
    try:
        import pydicom
    except ImportError:
        raise ImportError(
            "pydicom is required for DICOM file support. "
            "Install it with: pip install pydicom"
        )

    # Read the DICOM dataset
    file_stream.seek(0)
    ds = pydicom.dcmread(file_stream)

    # Extract pixel array
    pixel_array = ds.pixel_array.astype(np.float64)

    # Apply rescale slope/intercept if present (common in CT)
    slope = getattr(ds, 'RescaleSlope', 1)
    intercept = getattr(ds, 'RescaleIntercept', 0)
    pixel_array = pixel_array * slope + intercept

    # Apply window/level if available
    window_center = getattr(ds, 'WindowCenter', None)
    window_width = getattr(ds, 'WindowWidth', None)

    if window_center is not None and window_width is not None:
        # Handle multi-value window/level
        if isinstance(window_center, pydicom.multival.MultiValue):
            window_center = float(window_center[0])
        else:
            window_center = float(window_center)
        if isinstance(window_width, pydicom.multival.MultiValue):
            window_width = float(window_width[0])
        else:
            window_width = float(window_width)

        lower = window_center - window_width / 2
        upper = window_center + window_width / 2
        pixel_array = np.clip(pixel_array, lower, upper)
        pixel_array = ((pixel_array - lower) / (upper - lower) * 255)
    else:
        # Simple min-max normalization
        pmin, pmax = pixel_array.min(), pixel_array.max()
        if pmax > pmin:
            pixel_array = ((pixel_array - pmin) / (pmax - pmin) * 255)
        else:
            pixel_array = np.zeros_like(pixel_array)

    pixel_array = pixel_array.astype(np.uint8)

    # Handle MONOCHROME1 (inverted)
    photometric = getattr(ds, 'PhotometricInterpretation', '')
    if photometric == 'MONOCHROME1':
        pixel_array = 255 - pixel_array

    # Convert to RGB
    if pixel_array.ndim == 2:
        # Grayscale → RGB
        rgb = np.stack([pixel_array] * 3, axis=-1)
    elif pixel_array.ndim == 3 and pixel_array.shape[2] == 3:
        rgb = pixel_array
    elif pixel_array.ndim == 3 and pixel_array.shape[0] == 3:
        rgb = np.transpose(pixel_array, (1, 2, 0))
    else:
        # Multi-frame: take first frame
        frame = pixel_array[0] if pixel_array.ndim >= 3 else pixel_array
        if frame.ndim == 2:
            rgb = np.stack([frame] * 3, axis=-1)
        else:
            rgb = frame

    return Image.fromarray(rgb.astype(np.uint8), 'RGB')


def get_dicom_metadata(file_stream) -> dict:
    """Extract useful metadata from a DICOM file."""
    try:
        import pydicom
    except ImportError:
        return {}

    file_stream.seek(0)
    ds = pydicom.dcmread(file_stream)

    metadata = {}
    fields = {
        'PatientName': 'patient_name',
        'PatientID': 'patient_id',
        'PatientAge': 'patient_age',
        'PatientSex': 'patient_sex',
        'StudyDate': 'study_date',
        'StudyDescription': 'study_description',
        'Modality': 'modality',
        'Manufacturer': 'manufacturer',
        'InstitutionName': 'institution',
        'BodyPartExamined': 'body_part',
    }
    for dcm_field, key in fields.items():
        val = getattr(ds, dcm_field, None)
        if val is not None:
            metadata[key] = str(val)

    return metadata
