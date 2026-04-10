"""
utils/helpers.py — Shared utilities for DeepScanX-AI
"""
from functools import wraps
import os
import jwt
import datetime
from flask import request, redirect, url_for, jsonify
from app2.models import db, get_object_id
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image as RLImage
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
import base64
from PIL import Image as PILImage


# ─────────────────────────────────────────────
# Auth decorators
# ─────────────────────────────────────────────
import jwt as pyjwt
from jwt import PyJWKClient
from config import SUPABASE_JWT_SECRET

SUPABASE_URL = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL") or "https://lpiykgllsafrwwmcuvbo.supabase.co"
JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
_jwks_client = None

# Frontend URL — used for auth redirects; override in .env for local dev
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

def _get_jwks_client():
    global _jwks_client
    if not _jwks_client:
        _jwks_client = PyJWKClient(JWKS_URL)
    return _jwks_client

def _verify_supabase_token(token):
    """
    Verifies a Supabase JWT and ensures the user exists.
    Auto-migrates/heals users if they have a historical email record but no proper supabase_id yet.
    Supports both legacy HS256 tokens and modern RS256/ES256 asymmetric tokens.
    """
    from app2.models import db
    import datetime
    
    if not SUPABASE_JWT_SECRET:
        raise Exception("Server missing SUPABASE_JWT_SECRET. Ensure it is placed in the .env file")
        
    try:
        unv_header = pyjwt.get_unverified_header(token)
        alg = unv_header.get('alg', 'HS256')
        
        if alg == 'HS256':
            # Legacy symmetric signing
            decoded = pyjwt.decode(
                token, 
                SUPABASE_JWT_SECRET, 
                algorithms=["HS256"], 
                options={"verify_aud": False}
            )
        else:
            # Modern asymmetric (RS256, ES256)
            client = _get_jwks_client()
            signing_key = client.get_signing_key_from_jwt(token)
            decoded = pyjwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                options={"verify_aud": False}
            )
            
    except Exception as e:
        alg = "unknown"
        try:
            alg = pyjwt.get_unverified_header(token).get("alg", "unknown")
        except:
            pass
        raise Exception(f"Failed to verify JWT (Algorithm: {alg}). Error: {str(e)}")
        
    supabase_id = decoded.get('sub')
    email = decoded.get('email', '')
    
    if not supabase_id:
        raise Exception("Invalid token subject")

    # All DB operations wrapped to give clear error if MongoDB is misconfigured
    try:
        user = db.users.find_one({"supabase_id": supabase_id})
        
        # Self-healing: if we found a dummy user created by buggy code (missing email), delete it and migrate
        if user and email and not user.get("email"):
            db.users.delete_one({"_id": user["_id"]})
            user = None
            
        if not user:
            user = db.users.find_one({"clerk_id": supabase_id})
            if user:
                db.users.update_one({"_id": user["_id"]}, {"$set": {"supabase_id": supabase_id}})
                user["supabase_id"] = supabase_id
                
        if not user and email:
            user = db.users.find_one({"email": email})
            if user:
                db.users.update_one({"_id": user["_id"]}, {"$set": {"supabase_id": supabase_id}})
                user["supabase_id"] = supabase_id

        if not user:
            # Determine role: admin if email matches admin account
            admin_emails = {'aditya.asb24@gmail.com', 'adtiya.asb24@gmail.com'}
            role = 'admin' if email in admin_emails else 'patient'
            new_user = {
                "supabase_id": supabase_id,
                "email": email,
                "role": role,
                "created_at": datetime.datetime.utcnow(),
                "is_active": True,
                "is_verified": True
            }
            result = db.users.insert_one(new_user)
            user = db.users.find_one({"_id": result.inserted_id})

    except Exception as db_err:
        err_str = str(db_err)
        # Detect MongoDB connectivity issues clearly
        if 'Connection refused' in err_str or 'ServerSelectionTimeoutError' in err_str or 'timed out' in err_str.lower():
            raise Exception(
                "Database unavailable. The backend cannot reach MongoDB. "
                "Please set MONGO_URI to a MongoDB Atlas connection string in Render environment variables. "
                f"Detail: {err_str[:200]}"
            )
        raise Exception(f"Database error during user lookup: {err_str[:300]}")
        
    return user


def login_required(f):
    """JWT cookie/bearer-based login required decorator."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
            
        if not token:
            return redirect(f"{FRONTEND_URL}/login")
            
        try:
            user = _verify_supabase_token(token)
            request.user = user
        except Exception:
            return redirect(f"{FRONTEND_URL}/login")
        return f(*args, **kwargs)
    return decorated


def optional_login(f):
    """Attach request.user if JWT present, but allow guests through."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
            
        if token:
            try:
                user = _verify_supabase_token(token)
                request.user = user
            except Exception:
                request.user = None
        else:
            request.user = None
        return f(*args, **kwargs)
    return decorated


def api_login_required(f):
    """JWT Bearer-token auth or cookie-based auth for the REST API."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)
            
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
            
        if not token:
            print("[DEBUG Auth] Missing token", flush=True)
            return jsonify({"error": "Missing or invalid Authorization credential"}), 401
            
        try:
            user = _verify_supabase_token(token)
            request.user = user
        except Exception as e:
            print(f"[DEBUG Auth] Exception verifying token: {str(e)}", flush=True)
            return jsonify({"error": f"Invalid token: {str(e)}"}), 401
        return f(*args, **kwargs)
    return decorated


def role_required(role):
    """Decorator to restrict a route to a specific role (e.g. 'admin')."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ', 1)[1]
                
            if not token:
                token = request.cookies.get('access_token')
                
            if not token:
                return redirect(f"{FRONTEND_URL}/login")
                
            try:
                user = _verify_supabase_token(token)
                if user.get('role') != role:
                    return redirect(url_for('app1.home'))
                request.user = user
            except Exception:
                return redirect(f"{FRONTEND_URL}/login")
            return f(*args, **kwargs)
        return decorated
    return decorator


# ─────────────────────────────────────────────
# Prediction history
# ─────────────────────────────────────────────

def save_prediction(user_id, module: str, data: dict, patient_id: str = None):
    """Persist a prediction result to MongoDB."""
    doc = {
        "user_id": user_id,
        "module": module,
        "predicted_class": data.get("predicted_class") or data.get("pred_class") or data.get("predicted_class", ""),
        "confidence": data.get("confidence", ""),
        "cancer_status": data.get("cancer_status") or data.get("status", ""),
        "filename": data.get("filename", ""),
        "timestamp": datetime.datetime.utcnow(),
    }
    if patient_id:
        doc["patient_id"] = patient_id
    try:
        result = db.predictions.insert_one(doc)
        return str(result.inserted_id)
    except Exception:
        pass  # Non-critical — never break the app over history saving
    return None


# ─────────────────────────────────────────────
# PDF report generator
# ─────────────────────────────────────────────

def generate_pdf_report(data: dict, module_name: str) -> bytes:
    """
    Build a styled PDF report and return it as bytes.
    data — the result dict from any prediction route
    module_name — human-readable string, e.g. "Breast Cancer IDC"
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'AuraTitle',
        parent=styles['Title'],
        fontSize=22,
        textColor=colors.HexColor('#6c63ff'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    )
    subtitle_style = ParagraphStyle(
        'AuraSub',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#888888'),
        spaceAfter=12,
        alignment=TA_CENTER,
    )
    heading_style = ParagraphStyle(
        'AuraH2',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#6c63ff'),
        spaceBefore=14,
        spaceAfter=4,
        fontName='Helvetica-Bold',
    )
    normal_style = ParagraphStyle(
        'AuraNormal',
        parent=styles['Normal'],
        fontSize=10,
        leading=15,
        spaceAfter=6,
    )
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#aaaaaa'),
        alignment=TA_CENTER,
        spaceBefore=20,
    )

    story = []

    # ── Header ──────────────────────────────
    story.append(Paragraph("DeepScanX AI", title_style))
    story.append(Paragraph("AI Unified Radiology Assistant — Diagnostic Report", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#6c63ff')))
    story.append(Spacer(1, 12))

    # ── Module & date ────────────────────────
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    story.append(Paragraph(f"<b>Module:</b> {module_name}", normal_style))
    story.append(Paragraph(f"<b>Report Generated:</b> {now}", normal_style))
    story.append(Spacer(1, 8))

    # ── Result summary table ─────────────────
    story.append(Paragraph("Prediction Summary", heading_style))

    predicted_class = (
        data.get("predicted_class") or
        data.get("pred_class") or
        data.get("predicted_class", "N/A")
    )
    confidence_raw = data.get("confidence", "N/A")
    try:
        conf_display = f"{float(confidence_raw) * 100:.2f}%"
    except (ValueError, TypeError):
        conf_display = str(confidence_raw)

    cancer_status = data.get("cancer_status") or data.get("status", "N/A")
    filename = data.get("filename", "N/A")

    table_data = [
        ["Field", "Value"],
        ["File Name", filename],
        ["Predicted Class", predicted_class],
        ["Cancer Status", cancer_status],
        ["Confidence", conf_display],
    ]

    tbl = Table(table_data, colWidths=[6 * cm, 12 * cm])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6c63ff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f5f5ff'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 12))

    # ── Clinical explanation ─────────────────
    explanation = (
        data.get("explanation_text") or
        data.get("explanation") or
        ""
    )
    if explanation:
        story.append(Paragraph("Clinical Interpretation", heading_style))
        # Strip markdown bold markers for PDF
        explanation_clean = explanation.replace("**", "")
        story.append(Paragraph(explanation_clean, normal_style))
        story.append(Spacer(1, 8))

    # ── Probability breakdown ────────────────
    probabilities = data.get("probabilities")
    if probabilities:
        story.append(Paragraph("Class Probability Breakdown", heading_style))
        prob_rows = [["Class", "Probability"]]
        for cls, prob in probabilities:
            prob_rows.append([cls, f"{float(prob) * 100:.2f}%"])
        prob_tbl = Table(prob_rows, colWidths=[10 * cm, 8 * cm])
        prob_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6c63ff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f5f5ff'), colors.white]),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(prob_tbl)
        story.append(Spacer(1, 8))

    # ── Disclaimer ───────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#dddddd')))
    story.append(Paragraph(
        "⚠  This report is generated by an AI model for research and educational purposes only. "
        "It must NOT be used as a clinical diagnosis. All results must be validated by a certified "
        "pathologist or oncologist.",
        disclaimer_style
    ))

    doc.build(story)
    return buf.getvalue()
