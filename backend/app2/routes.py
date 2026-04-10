from flask import Blueprint, request, jsonify, make_response
from flask_mail import Mail, Message
from .models import db, get_object_id
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
import os
import jwt
import datetime
import config  # centralized .env loader

bp = Blueprint('app2', __name__)

mail = Mail()

@bp.record
def record_params(setup_state):
    app = setup_state.app
    mail.init_app(app)


def generate_verification_code(length=6):
    return ''.join(random.choices(string.digits, k=length))


def create_jwt_response(user_id):
    secret_key = os.getenv('SECRET_KEY', 'your-secret-key')
    token = jwt.encode({
        'user_id': str(user_id),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, secret_key, algorithm="HS256")
    resp = make_response(jsonify({"ok": True, "message": "Authenticated"}))
    # CRITICAL FIX: samesite='None' and secure=True is REQUIRED for cross-origin (Vercel->Render) cookies!
    resp.set_cookie('access_token', token, httponly=True, samesite='None', secure=True)
    return resp


def send_otp_email(email, code):
    """Send OTP verification email."""
    try:
        msg = Message(
            subject="DeepScanX AI — Email Verification Code",
            recipients=[email],
            html=f"""
            <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;padding:30px;
                        border-radius:12px;background:#0d0d1a;color:#e0e0ff;">
              <h2 style="color:#6c63ff;text-align:center;">🔬 DeepScanX AI</h2>
              <p style="text-align:center;color:#aaa;">AI Unified Radiology Assistant</p>
              <hr style="border-color:#2a2a4a;">
              <p>Your email verification code is:</p>
              <div style="font-size:36px;font-weight:bold;letter-spacing:12px;
                          text-align:center;color:#6c63ff;padding:20px 0;">{code}</div>
              <p style="color:#aaa;font-size:12px;text-align:center;">
                This code expires in 15 minutes. Do not share it with anyone.</p>
              <hr style="border-color:#2a2a4a;">
              <p style="color:#666;font-size:11px;text-align:center;">
                For research &amp; educational use only. Not for clinical diagnosis.</p>
            </div>
            """
        )
        mail.send(msg)
        return True
    except Exception:
        return False

