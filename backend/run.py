from app1 import create_app as create_app1
from app2 import create_app as create_app2
from app3 import create_app as create_app3
from app4 import create_app as create_app4
from app5 import create_app as create_app5
from app6 import create_app as create_app6
from app7 import create_app as create_app7
from app8 import create_app as create_app8
from app9 import create_app as create_app9
from app10 import create_app as create_app10
from app11 import create_app as create_app11
from app12 import create_app as create_app12
from app13 import create_app as create_app13
from api import create_app as create_api
from flask import Flask, redirect, url_for, request, jsonify
from flask_mail import Mail
from flask_cors import CORS
import os
import config  # centralized .env loader

app = Flask(__name__)

# ── CORS setup ──────────────────────────────────────────────────────────────
# Explicit origin list — localhost for local dev, Vercel for production.
# withCredentials=True requires we reflect the exact origin (no wildcard "*").
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:3000",
    "https://deepscanx-ai.vercel.app",
]
CORS(app, supports_credentials=True, origins=ALLOWED_ORIGINS,
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])

# ── Explicit after_request CORS header injection ─────────────────────────────
# flask-cors sometimes misses error responses (4xx / 5xx). This ensures every
# single response — including exceptions — gets proper CORS headers so the
# browser never sees a CORS block when the backend crashes.
@app.after_request
def inject_cors_headers(response):
    origin = request.headers.get("Origin", "")
    allowed = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "https://deepscanx-ai.vercel.app",
    ]
    
    # Allow any origin that's in our allowed list
    if origin in allowed:
        response.headers["Access-Control-Allow-Origin"] = origin
    elif not origin:
        # No origin header, allow all (development safety)
        response.headers["Access-Control-Allow-Origin"] = "*"
    
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Headers"] = (
        "Content-Type, Authorization, X-Requested-With, Accept"
    )
    response.headers["Access-Control-Allow-Methods"] = (
        "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
    )
    response.headers["Access-Control-Max-Age"] = "3600"
    
    return response

# ── Handle OPTIONS pre-flight for every route ────────────────────────────────
@app.before_request
def handle_options():
    if request.method == "OPTIONS":
        from flask import make_response
        resp = make_response("", 204)
        origin = request.headers.get("Origin", "")
        if origin:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Credentials"] = "true"
            resp.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization, X-Requested-With"
            )
            resp.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            )
            resp.headers["Access-Control-Max-Age"] = "3600"
        return resp

# ── Global error handler to ensure CORS headers on errors ─────────────────────
@app.errorhandler(Exception)
def handle_error(error):
    from flask import make_response
    import traceback
    
    error_message = str(error)
    status_code = getattr(error, "code", 500)
    
    # Log the full traceback for debugging
    if app.debug:
        print(f"\n[ERROR] {status_code}: {error_message}")
        print(traceback.format_exc())
    
    response = make_response(
        jsonify({
            "error": error_message,
            "status": "error",
            "traceback": traceback.format_exc() if app.debug else None
        }),
        status_code
    )
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

# ── Configuration (all values come from config.py which loads .env reliably) ─
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['GOOGLE_CLIENT_ID'] = config.GOOGLE_CLIENT_ID
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = config.MAIL_USERNAME
app.config['MAIL_PASSWORD'] = config.MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = config.MAIL_DEFAULT_SENDER

# Initialize Flask-Mail
Mail(app)

# ── Register blueprints — Original modules ───────────────────────────────────
app.register_blueprint(create_app1(), url_prefix='/app1')
app.register_blueprint(create_app2(), url_prefix='/app2')
app.register_blueprint(create_app3(), url_prefix='/app3')
app.register_blueprint(create_app4(), url_prefix='/app4')
app.register_blueprint(create_app5(), url_prefix='/app5')
app.register_blueprint(create_app6(), url_prefix='/admin')
app.register_blueprint(create_app7(), url_prefix='/app7')

# ── Register blueprints — New diagnostic modules ─────────────────────────────
app.register_blueprint(create_app8(), url_prefix='/app8')
app.register_blueprint(create_app9(), url_prefix='/app9')
app.register_blueprint(create_app10(), url_prefix='/app10')
app.register_blueprint(create_app11(), url_prefix='/app11')

# ── Register blueprints — Clinical workflow ──────────────────────────────────
app.register_blueprint(create_app12(), url_prefix='/patients')
app.register_blueprint(create_app13(), url_prefix='/opinions')

# ── Register blueprints — REST API ──────────────────────────────────────────
app.register_blueprint(create_api(), url_prefix='/api')


@app.route('/')
def index():
    return redirect(url_for('app1.home'))


@app.route('/health')
def health():
    """Health-check endpoint for Render uptime monitoring."""
    return jsonify({"status": "ok", "service": "DeepScanX-AI"}), 200


if __name__ == '__main__':
    # Startup diagnostics — verify all blueprints are registered
    registered_endpoints = sorted(set(r.endpoint for r in app.url_map.iter_rules()))
    print("\n=== REGISTERED ENDPOINTS ===")
    for ep in registered_endpoints:
        print(f"  * {ep}")
    critical = ['app8.page', 'app9.page', 'app10.page', 'app11.page']
    missing = [e for e in critical if e not in registered_endpoints]
    if missing:
        print(f"\n  [!] MISSING ENDPOINTS: {missing}")
    else:
        print(f"\n  [OK] All critical endpoints registered ({len(registered_endpoints)} total)")
    print("============================\n")

    # use_reloader=False prevents Windows socket crashes (WinError 10038)
    # when using gRPC under the hood via google.generativeai
    app.run(debug=True, use_reloader=False)