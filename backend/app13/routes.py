"""
app13/routes.py — Second Opinion / Collaboration System
Allows doctors to request peer review of AI predictions with secure shareable links.
"""
import datetime
import secrets
import json
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from utils.helpers import login_required, optional_login
from app2.models import db, get_object_id
from bson.objectid import ObjectId

bp = Blueprint('app13', __name__, template_folder='templates')


@bp.route('/request', methods=['POST'])
@login_required
def request_opinion():
    """Create a second opinion request for a prediction."""
    user = request.user
    prediction_id = request.form.get('prediction_id', '').strip()
    reviewer_email = request.form.get('reviewer_email', '').strip()
    message = request.form.get('message', '').strip()

    if not prediction_id:
        flash('Missing prediction ID')
        return redirect(url_for('app1.history'))

    # Find the prediction
    pred_oid = get_object_id(prediction_id)
    prediction = db.predictions.find_one({"_id": pred_oid})
    if not prediction:
        flash('Prediction not found')
        return redirect(url_for('app1.history'))

    # Generate secure review token
    review_token = secrets.token_urlsafe(32)

    opinion_doc = {
        "prediction_id": prediction_id,
        "requester_id": str(user['_id']),
        "requester_name": user.get('name', 'Unknown'),
        "requester_email": user.get('email', ''),
        "reviewer_email": reviewer_email or None,
        "review_token": review_token,
        "message": message or "",
        "status": "pending",  # pending, reviewed
        "comments": [],
        "prediction_data": {
            "module": prediction.get('module', ''),
            "predicted_class": prediction.get('predicted_class', ''),
            "confidence": prediction.get('confidence', ''),
            "cancer_status": prediction.get('cancer_status', ''),
            "filename": prediction.get('filename', ''),
            "timestamp": prediction.get('timestamp'),
        },
        "created_at": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow(),
    }
    db.second_opinions.insert_one(opinion_doc)

    review_url = url_for('app13.review', token=review_token, _external=True)

    # Try to send email notification
    try:
        if reviewer_email:
            from flask_mail import Message, Mail
            mail = Mail()
            msg = Message(
                subject="DeepScanX AI — Second Opinion Request",
                recipients=[reviewer_email],
                html=f"""
                <div style="font-family:Arial,sans-serif;max-width:500px;margin:auto;padding:30px;
                            border-radius:12px;background:#0d0d1a;color:#e0e0ff;">
                  <h2 style="color:#dc143c;text-align:center;">🔬 DeepScanX AI</h2>
                  <p>Dr. {user.get('name', 'A colleague')} has requested your second opinion
                     on an AI diagnostic prediction.</p>
                  <p><b>Module:</b> {prediction.get('module', '')}<br>
                     <b>Prediction:</b> {prediction.get('predicted_class', '')}<br>
                     <b>Status:</b> {prediction.get('cancer_status', '')}</p>
                  {f'<p><b>Message:</b> {message}</p>' if message else ''}
                  <div style="text-align:center;padding:20px;">
                    <a href="{review_url}" style="background:#dc143c;color:white;padding:12px 24px;
                       border-radius:8px;text-decoration:none;font-weight:bold;">
                       Review Prediction
                    </a>
                  </div>
                  <p style="color:#666;font-size:11px;text-align:center;">
                    For research & educational use only.</p>
                </div>
                """
            )
            mail.send(msg)
    except Exception:
        pass  # Email sending is optional

    flash(f'Second opinion request created. Review link: {review_url}')
    return redirect(url_for('app1.history'))


@bp.route('/review/<token>')
@optional_login
def review(token):
    """View a prediction for second opinion review."""
    opinion = db.second_opinions.find_one({"review_token": token})
    if not opinion:
        flash('Review link is invalid or expired')
        return redirect(url_for('app1.home'))

    user = getattr(request, 'user', None)
    return render_template('review.html', opinion=opinion, user=user, token=token)


@bp.route('/review/<token>/comment', methods=['POST'])
@optional_login
def add_comment(token):
    """Add a review comment to a second opinion request."""
    opinion = db.second_opinions.find_one({"review_token": token})
    if not opinion:
        return jsonify({"error": "Not found"}), 404

    comment_text = request.form.get('comment', '').strip()
    reviewer_name = request.form.get('reviewer_name', '').strip()

    if not comment_text:
        flash('Comment cannot be empty')
        return redirect(url_for('app13.review', token=token))

    user = getattr(request, 'user', None)
    if user and not reviewer_name:
        reviewer_name = user.get('name', 'Anonymous')

    comment = {
        "text": comment_text,
        "reviewer_name": reviewer_name or "Anonymous Reviewer",
        "reviewer_id": str(user['_id']) if user else None,
        "created_at": datetime.datetime.utcnow(),
    }

    db.second_opinions.update_one(
        {"review_token": token},
        {
            "$push": {"comments": comment},
            "$set": {"status": "reviewed", "updated_at": datetime.datetime.utcnow()}
        }
    )

    flash('Your review comment has been added')
    return redirect(url_for('app13.review', token=token))


@bp.route('/my-requests')
@login_required
def my_requests():
    """View all second opinion requests made by the current user."""
    user = request.user
    requests_list = list(
        db.second_opinions.find({"requester_id": str(user['_id'])}).sort("created_at", -1)
    )
    return render_template('second_opinion.html', requests=requests_list, user=user)


# ==========================================
# React API Endpoints
# ==========================================

@bp.route('/api/requests', methods=['GET'])
@login_required
def api_get_requests():
    user = request.user
    reqs = list(db.second_opinions.find({"requester_id": str(user['_id'])}).sort("created_at", -1))
    for r in reqs:
        r['_id'] = str(r['_id'])
        r['created_at'] = r['created_at'].isoformat() if r.get('created_at') else None
        r['updated_at'] = r['updated_at'].isoformat() if r.get('updated_at') else None
    return jsonify({"requests": reqs})


@bp.route('/api/request', methods=['POST'])
@login_required
def api_create_request():
    user = request.user
    data = request.get_json()
    prediction_id = data.get('prediction_id', '').strip()
    reviewer_email = data.get('recipient_email', '').strip()
    message = data.get('message', '').strip()

    if not prediction_id:
        return jsonify({"error": "Missing prediction ID"}), 400

    pred_oid = get_object_id(prediction_id)
    prediction = db.predictions.find_one({"_id": pred_oid})
    if not prediction:
        return jsonify({"error": "Prediction not found"}), 404

    review_token = secrets.token_urlsafe(32)
    opinion_doc = {
        "prediction_id": prediction_id,
        "requester_id": str(user['_id']),
        "requester_name": user.get('name', 'Unknown'),
        "requester_email": user.get('email', ''),
        "recipient_email": reviewer_email or None,
        "review_token": review_token,
        "message": message or "",
        "status": "pending",
        "comments": [],
        "prediction_data": {
            "module": prediction.get('module', ''),
            "predicted_class": prediction.get('predicted_class', ''),
            "confidence": prediction.get('confidence', ''),
            "cancer_status": prediction.get('cancer_status', ''),
            "filename": prediction.get('filename', ''),
            "timestamp": prediction.get('timestamp'),
        },
        "created_at": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow(),
    }
    db.second_opinions.insert_one(opinion_doc)
    opinion_doc['_id'] = str(opinion_doc['_id'])
    opinion_doc['created_at'] = opinion_doc['created_at'].isoformat()
    opinion_doc['updated_at'] = opinion_doc['updated_at'].isoformat()

    return jsonify({"request": opinion_doc})


@bp.route('/api/review/<token>', methods=['GET'])
@optional_login
def api_get_review(token):
    opinion = db.second_opinions.find_one({"review_token": token})
    if not opinion:
        return jsonify({"error": "Review link invalid or expired"}), 404

    # Sanitize for frontend
    opinion['_id'] = str(opinion['_id'])
    opinion['created_at'] = opinion['created_at'].isoformat() if opinion.get('created_at') else None
    opinion['updated_at'] = opinion['updated_at'].isoformat() if opinion.get('updated_at') else None
    
    return jsonify({
        "prediction": opinion.get('prediction_data', {}),
        "message": opinion.get('message', ''),
        "status": opinion.get('status', ''),
        "comments": opinion.get('comments', [])
    })


@bp.route('/api/review/<token>', methods=['POST'])
@optional_login
def api_submit_review(token):
    opinion = db.second_opinions.find_one({"review_token": token})
    if not opinion:
        return jsonify({"error": "Review link invalid or expired"}), 404

    data = request.get_json()
    comment_text = data.get('opinion', '').strip()
    
    if not comment_text:
        return jsonify({"error": "Comment cannot be empty"}), 400

    user = getattr(request, 'user', None)
    reviewer_name = user.get('name', 'Anonymous') if user else "Anonymous Reviewer"

    comment = {
        "text": comment_text,
        "reviewer_name": reviewer_name,
        "reviewer_id": str(user['_id']) if user else None,
        "created_at": datetime.datetime.utcnow(),
    }

    db.second_opinions.update_one(
        {"review_token": token},
        {
            "$push": {"comments": comment},
            "$set": {"status": "reviewed", "updated_at": datetime.datetime.utcnow()}
        }
    )

    return jsonify({"success": True, "comment": comment_text})
