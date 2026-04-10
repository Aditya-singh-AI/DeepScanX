"""
app12/routes.py — Patient Management & Longitudinal Tracking
CRUD for patient profiles and timeline visualization of scan history.
"""
import datetime
import json
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from utils.helpers import login_required, api_login_required
from app2.models import db, get_object_id
from bson.objectid import ObjectId

bp = Blueprint('app12', __name__, template_folder='templates')


@bp.route('/')
@login_required
def patients_list():
    """List all patients for the current doctor."""
    user = request.user
    patients = list(db.patients.find({"doctor_id": user['_id']}).sort("name", 1))
    # Attach scan counts
    for p in patients:
        p['scan_count'] = db.predictions.count_documents({"patient_id": str(p['_id'])})
        p['last_scan'] = None
        last = db.predictions.find_one(
            {"patient_id": str(p['_id'])},
            sort=[("timestamp", -1)]
        )
        if last:
            p['last_scan'] = last.get('timestamp')
    return render_template('patients.html', patients=patients, user=user)


@bp.route('/create', methods=['POST'])
@login_required
def create_patient():
    """Create a new patient profile."""
    user = request.user
    name = request.form.get('name', '').strip()
    age = request.form.get('age', '').strip()
    gender = request.form.get('gender', '').strip()
    medical_record = request.form.get('medical_record', '').strip()
    notes = request.form.get('notes', '').strip()

    if not name:
        flash('Patient name is required')
        return redirect(url_for('app12.patients_list'))

    patient_doc = {
        "name": name,
        "age": int(age) if age.isdigit() else None,
        "gender": gender or None,
        "medical_record_number": medical_record or None,
        "notes": notes or "",
        "doctor_id": user['_id'],
        "created_at": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow(),
    }
    db.patients.insert_one(patient_doc)
    flash(f'Patient "{name}" created successfully')
    return redirect(url_for('app12.patients_list'))


@bp.route('/<patient_id>')
@login_required
def patient_detail(patient_id):
    """View a patient's profile and scan history."""
    user = request.user
    oid = get_object_id(patient_id)
    patient = db.patients.find_one({"_id": oid, "doctor_id": user['_id']})
    if not patient:
        flash('Patient not found')
        return redirect(url_for('app12.patients_list'))

    # Get all predictions for this patient
    predictions = list(
        db.predictions.find({"patient_id": patient_id}).sort("timestamp", -1)
    )

    # Build timeline data for Chart.js
    timeline_data = []
    for p in predictions:
        try:
            conf = float(p.get('confidence', 0))
            if conf > 1:
                conf = conf / 100
        except (ValueError, TypeError):
            conf = 0
        timeline_data.append({
            'date': p.get('timestamp', datetime.datetime.utcnow()).strftime('%Y-%m-%d %H:%M'),
            'module': p.get('module', 'unknown'),
            'predicted_class': p.get('predicted_class', ''),
            'confidence': round(conf * 100, 2),
            'cancer_status': p.get('cancer_status', ''),
        })

    return render_template('patient_detail.html',
                           patient=patient, predictions=predictions,
                           timeline_data=json.dumps(timeline_data),
                           user=user)


@bp.route('/<patient_id>/edit', methods=['POST'])
@login_required
def edit_patient(patient_id):
    """Update patient profile."""
    user = request.user
    oid = get_object_id(patient_id)
    patient = db.patients.find_one({"_id": oid, "doctor_id": user['_id']})
    if not patient:
        flash('Patient not found')
        return redirect(url_for('app12.patients_list'))

    updates = {"updated_at": datetime.datetime.utcnow()}
    name = request.form.get('name', '').strip()
    if name:
        updates['name'] = name
    age = request.form.get('age', '').strip()
    if age.isdigit():
        updates['age'] = int(age)
    gender = request.form.get('gender', '').strip()
    if gender:
        updates['gender'] = gender
    notes = request.form.get('notes', '')
    updates['notes'] = notes
    medical_record = request.form.get('medical_record', '').strip()
    if medical_record:
        updates['medical_record_number'] = medical_record

    db.patients.update_one({"_id": oid}, {"$set": updates})
    flash('Patient profile updated')
    return redirect(url_for('app12.patient_detail', patient_id=patient_id))


@bp.route('/<patient_id>/delete', methods=['POST'])
@login_required
def delete_patient(patient_id):
    """Delete a patient profile."""
    user = request.user
    oid = get_object_id(patient_id)
    result = db.patients.delete_one({"_id": oid, "doctor_id": user['_id']})
    if result.deleted_count:
        flash('Patient profile deleted')
    else:
        flash('Patient not found')
    return redirect(url_for('app12.patients_list'))


@bp.route('/api/list')
@login_required
def api_list():
    """API endpoint to get patients list (for AJAX dropdowns)."""
    user = request.user
    patients = list(db.patients.find(
        {"doctor_id": user['_id']},
        {"name": 1, "age": 1, "gender": 1, "medical_record_number": 1}
    ).sort("name", 1))
    result = []
    for p in patients:
        result.append({
            "id": str(p['_id']),
            "name": p.get('name', ''),
            "age": p.get('age'),
            "gender": p.get('gender', ''),
            "mrn": p.get('medical_record_number', ''),
        })
@bp.route('/api/react', methods=['GET', 'POST'])
@api_login_required
def api_react_patients():
    user = request.user
    if request.method == 'POST':
        data = request.json or {}
        name = str(data.get('name', '')).strip()
        age = str(data.get('age', '')).strip()
        gender = str(data.get('gender', 'Male')).strip()
        medical_record = str(data.get('medical_record_number', '')).strip()
        notes = str(data.get('notes', '')).strip()
        
        if not name:
            return jsonify({"error": "Name is required"}), 400
            
        patient_doc = {
            "name": name,
            "age": int(age) if age.isdigit() else None,
            "gender": gender or None,
            "medical_record_number": medical_record or None,
            "notes": notes or "",
            "doctor_id": user['_id'],
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow(),
        }
        result = db.patients.insert_one(patient_doc)
        patient_doc['_id'] = str(result.inserted_id)
        patient_doc['id'] = patient_doc['_id']
        patient_doc['created_at'] = patient_doc['created_at'].isoformat()
        patient_doc['updated_at'] = patient_doc['updated_at'].isoformat()
        patient_doc['doctor_id'] = str(patient_doc['doctor_id'])
        
        return jsonify({"patient": patient_doc})

    # GET
    patients = list(db.patients.find(
        {"doctor_id": user['_id']}
    ).sort("name", 1))
    
    for p in patients:
        p['_id'] = str(p['_id'])
        if 'created_at' in p:
            p['created_at'] = p['created_at'].isoformat() if isinstance(p['created_at'], datetime.datetime) else str(p['created_at'])
        if 'updated_at' in p:
            p['updated_at'] = p['updated_at'].isoformat() if isinstance(p['updated_at'], datetime.datetime) else str(p['updated_at'])
        p['doctor_id'] = str(p['doctor_id'])

    return jsonify({"patients": patients})

@bp.route('/api/react/<patient_id>', methods=['GET'])
@api_login_required
def api_react_patient_detail(patient_id):
    user = request.user
    oid = get_object_id(patient_id)
    patient = db.patients.find_one({"_id": oid, "doctor_id": user['_id']})
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
        
    patient['_id'] = str(patient['_id'])
    if 'created_at' in patient:
        patient['created_at'] = patient['created_at'].isoformat() if isinstance(patient['created_at'], datetime.datetime) else str(patient['created_at'])
    if 'updated_at' in patient:
        patient['updated_at'] = patient['updated_at'].isoformat() if isinstance(patient['updated_at'], datetime.datetime) else str(patient['updated_at'])
    patient['doctor_id'] = str(patient['doctor_id'])
    
    return jsonify({"patient": patient})

@bp.route('/api/react/<patient_id>/timeline', methods=['GET'])
@api_login_required
def api_react_patient_timeline(patient_id):
    user = request.user
    oid = get_object_id(patient_id)
    patient = db.patients.find_one({"_id": oid, "doctor_id": user['_id']})
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    predictions = list(
        db.predictions.find({"patient_id": patient_id}).sort("timestamp", -1)
    )
    
    timeline_data = []
    for p in predictions:
        try:
            conf = float(p.get('confidence', 0))
            if conf > 1:
                conf = conf / 100
        except (ValueError, TypeError):
            conf = 0
            
        timestamp = p.get('timestamp')
        
        timeline_data.append({
            'timestamp': timestamp.isoformat() if timestamp else None,
            'module': p.get('module', 'unknown'),
            'predicted_class': p.get('predicted_class', ''),
            'confidence': round(conf * 100, 2),
            'cancer_status': p.get('cancer_status', ''),
            'filename': p.get('filename', '')
        })
        
    return jsonify({"timeline": timeline_data})
