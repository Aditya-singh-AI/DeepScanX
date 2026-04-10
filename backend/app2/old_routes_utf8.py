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
            subject="DeepScanX AI ΓÇö Email Verification Code",
            recipients=[email],
            html=f"""
            <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;padding:30px;
                        border-radius:12px;background:#0d0d1a;color:#e0e0ff;">
              <h2 style="color:#6c63ff;text-align:center;">≡ƒö¼ DeepScanX AI</h2>
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


@bp.route('/login', methods=['POST'])
def login():

    data = request.get_json(silent=True) or {}
    email = data.get('email')
    password = data.get('password')
    user = db.users.find_one({"email": email})

    if user and check_password_hash(user['password'], password):
        if not user.get('is_active', True):
            return jsonify({"error": "Your account has been deactivated. Contact admin."}), 403

        if not user.get('is_verified', False):
            # Re-send OTP
            code = generate_verification_code()
            db.users.update_one({"_id": user['_id']}, {
                "$set": {
                    "verification_code": code,
                    "otp_expires": datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
                }
            })
            send_otp_email(email, code)
            resp = make_response(jsonify({"ok": False, "requires_verification": True}))
            secret_key = os.getenv('SECRET_KEY', 'your-secret-key')
            token = jwt.encode({
                'user_id': str(user['_id']),
                'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=20)
            }, secret_key, algorithm="HS256")
            # SameSite None for cross-origin
            resp.set_cookie('verify_token', token, httponly=True, samesite='None', secure=True, max_age=1200)
            return resp

        return create_jwt_response(user['_id'])

    return jsonify({"error": "Invalid credentials"}), 401


@bp.route('/google_callback', methods=['POST'])
def google_callback():

    import requests as http_requests

    data = request.get_json(silent=True) or {}
    credential = data.get('credential')
    if not credential:
        return jsonify({"error": "No credential"}), 400

    # Verify with Google
    resp = http_requests.get(
        f'https://oauth2.googleapis.com/tokeninfo?id_token={credential}'
    )
    if resp.status_code != 200:
        return jsonify({"error": "Invalid token"}), 401

    info = resp.json()
    client_id = config.GOOGLE_CLIENT_ID
    if info.get('aud') != client_id:
        return jsonify({"error": "Token not for this app"}), 401

    email = info['email']
    name = info.get('name', email.split('@')[0])

    user = db.users.find_one({"email": email})
    if not user:
        # Auto-register Google user
        user_doc = {
            "name": name,
            "email": email,
            "password": "",
            "is_verified": True,
            "is_active": True,
            "role": "patient",
            "auth_provider": "google",
            "created_at": datetime.datetime.utcnow()
        }
        result = db.users.insert_one(user_doc)
        user_id = result.inserted_id
    else:
        if not user.get('is_active', True):
            return jsonify({"error": "Account deactivated"}), 403
        user_id = user['_id']

    return create_jwt_response(user_id)


@bp.route('/signup', methods=['POST'])
def signup():

    data = request.get_json(silent=True) or {}
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
         return jsonify({"error": "Email and password are required"}), 400

    if db.users.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 400

    verification_code = generate_verification_code()
    user_doc = {
        "name": name,
        "email": email,
        "password": generate_password_hash(password),
        "verification_code": verification_code,
        "otp_expires": datetime.datetime.utcnow() + datetime.timedelta(minutes=15),
        "is_verified": False,
        "is_active": True,
        "role": "patient",
        "created_at": datetime.datetime.utcnow()
    }

    result = db.users.insert_one(user_doc)

    email_sent = send_otp_email(email, verification_code)
    if not email_sent:
        db.users.update_one({"_id": result.inserted_id}, {"$set": {"is_verified": True}})
        return create_jwt_response(result.inserted_id)

    secret_key = os.getenv('SECRET_KEY', 'your-secret-key')
    token = jwt.encode({
        'user_id': str(result.inserted_id),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=20)
    }, secret_key, algorithm="HS256")
    
    resp = make_response(jsonify({"ok": True, "requires_verification": True}))
    resp.set_cookie('verify_token', token, httponly=True, samesite='None', secure=True, max_age=1200)
    return resp


@bp.route('/verify_email', methods=['POST'])
def verify_email():

    token = request.cookies.get('verify_token') or request.cookies.get('access_token')
    if not token:
        return jsonify({"error": "No token provided"}), 401
        
    try:
        secret_key = os.getenv('SECRET_KEY', 'your-secret-key')
        data = jwt.decode(token, secret_key, algorithms=["HS256"])
        user_id = get_object_id(data['user_id'])
    except Exception:
        return jsonify({"error": "Invalid token"}), 401

    user = db.users.find_one({"_id": user_id})
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.get('is_verified'):
        return create_jwt_response(user_id)

    data = request.get_json(silent=True) or {}
    code = data.get('code', '').strip()
    stored_code = user.get('verification_code', '')
    otp_expires = user.get('otp_expires')

    expired = otp_expires and datetime.datetime.utcnow() > otp_expires

    if code == stored_code and not expired:
        db.users.update_one(
            {"_id": user_id},
            {"$set": {"is_verified": True}, "$unset": {"verification_code": "", "otp_expires": ""}}
        )
        resp = create_jwt_response(user_id)
        # Delete verify token but keep access token
        resp.set_cookie('verify_token', '', expires=0, samesite='None', secure=True)
        return resp
    elif expired:
        # Generate new one
        new_code = generate_verification_code()
        db.users.update_one({"_id": user_id}, {
            "$set": {
                "verification_code": new_code,
                "otp_expires": datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
            }
        })
        send_otp_email(user['email'], new_code)
        return jsonify({"error": "Code expired. New code sent."}), 400
    else:
        return jsonify({"error": "Invalid code"}), 400


@bp.route('/resend_otp', methods=['POST'])
def resend_otp():

    token = request.cookies.get('verify_token')
    if not token:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        secret_key = os.getenv('SECRET_KEY', 'your-secret-key')
        data = jwt.decode(token, secret_key, algorithms=["HS256"])
        user_id = get_object_id(data['user_id'])
        user = db.users.find_one({"_id": user_id})
        if user and not user.get('is_verified'):
            new_code = generate_verification_code()
            db.users.update_one({"_id": user_id}, {
                "$set": {
                    "verification_code": new_code,
                    "otp_expires": datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
                }
            })
            send_otp_email(user['email'], new_code)
            return jsonify({"ok": True, "message": "Code sent"})
    except Exception:
        pass
    return jsonify({"error": "Failed to resend"}), 400


@bp.route('/logout', methods=['POST'])
def logout():

    resp = make_response(jsonify({"ok": True}))
    resp.set_cookie('access_token', '', expires=0, samesite='None', secure=True)
    resp.set_cookie('verify_token', '', expires=0, samesite='None', secure=True)
    return resp
