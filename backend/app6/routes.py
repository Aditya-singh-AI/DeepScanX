"""
app6/routes.py — Admin Panel Blueprint
Only accessible by users with role == 'admin'
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from utils.helpers import role_required, api_login_required
from app2.models import db, get_object_id
import datetime

bp = Blueprint('app6', __name__, template_folder='templates')


@bp.route('/')
@role_required('admin')
def dashboard():
    total_users = db.users.count_documents({})
    active_users = db.users.count_documents({"is_active": True})
    total_predictions = db.predictions.count_documents({})

    # Per-module stats
    module_stats = {}
    for module in ['breast_cancer', 'lung_colon', 'lung_cancer']:
        module_stats[module] = db.predictions.count_documents({"module": module})

    # Recent predictions (last 10)
    recent_predictions = list(
        db.predictions.find({}).sort("timestamp", -1).limit(10)
    )

    return render_template(
        'admin_dashboard.html',
        total_users=total_users,
        active_users=active_users,
        total_predictions=total_predictions,
        module_stats=module_stats,
        recent_predictions=recent_predictions,
        admin=request.user,
    )


@bp.route('/users')
@role_required('admin')
def users():
    page = int(request.args.get('page', 1))
    per_page = 20
    skip = (page - 1) * per_page
    all_users = list(db.users.find({}).skip(skip).limit(per_page))
    total = db.users.count_documents({})
    total_pages = (total + per_page - 1) // per_page
    return render_template(
        'admin_users.html',
        users=all_users,
        page=page,
        total_pages=total_pages,
        admin=request.user,
    )


@bp.route('/deactivate/<user_id>', methods=['POST'])
@role_required('admin')
def deactivate_user(user_id):
    uid = get_object_id(user_id)
    if uid:
        user = db.users.find_one({"_id": uid})
        if user:
            new_status = not user.get('is_active', True)
            db.users.update_one({"_id": uid}, {"$set": {"is_active": new_status}})
            action = "activated" if new_status else "deactivated"
            flash(f"User {user.get('email')} has been {action}.")
    return redirect(url_for('app6.users'))


@bp.route('/make_admin/<user_id>', methods=['POST'])
@role_required('admin')
def make_admin(user_id):
    uid = get_object_id(user_id)
    if uid:
        user = db.users.find_one({"_id": uid})
        if user:
            new_role = 'patient' if user.get('role') == 'admin' else 'admin'
            db.users.update_one({"_id": uid}, {"$set": {"role": new_role}})
            flash(f"User {user.get('email')} role changed to {new_role}.")
    return redirect(url_for('app6.users'))


# ==========================================
# React API Endpoints
# ==========================================

def is_admin():
    user = getattr(request, 'user', None)
    return user and user.get('role') == 'admin'

@bp.route('/api/stats', methods=['GET'])
@api_login_required
def api_stats():
    if not is_admin():
        return jsonify({"error": "Admin access required"}), 403

    total_users = db.users.count_documents({})
    total_predictions = db.predictions.count_documents({})
    
    # Calculate active today mapping
    today = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    active_today = db.predictions.count_documents({"timestamp": {"$gte": today}})

    recent_users_cursor = db.users.find({}).sort("_id", -1).limit(5)
    recent_users = []
    for u in recent_users_cursor:
        u['_id'] = str(u['_id'])
        if 'password' in u:
            del u['password']
        recent_users.append(u)

    return jsonify({
        "total_users": total_users,
        "total_predictions": total_predictions,
        "active_today": active_today,
        "recent_users": recent_users
    })

@bp.route('/api/users', methods=['GET'])
@api_login_required
def api_users():
    if not is_admin():
        return jsonify({"error": "Admin access required"}), 403
        
    users_cursor = db.users.find({}).sort("_id", -1)
    users_list = []
    for u in users_cursor:
        u['_id'] = str(u['_id'])
        if 'password' in u:
            del u['password']
        users_list.append(u)
        
    return jsonify({"users": users_list})

@bp.route('/api/users/<user_id>', methods=['PATCH'])
@api_login_required
def api_patch_user(user_id):
    if not is_admin():
        return jsonify({"error": "Admin access required"}), 403
        
    data = request.json or {}
    new_role = data.get('role')
    
    if new_role not in ['admin', 'user']:
        return jsonify({"error": "Invalid role specified"}), 400
        
    uid = get_object_id(user_id)
    if not uid:
        return jsonify({"error": "Invalid user ID"}), 400
        
    result = db.users.update_one({"_id": uid}, {"$set": {"role": new_role}})
    if result.matched_count == 0:
        return jsonify({"error": "User not found"}), 404
        
    return jsonify({"success": True})

@bp.route('/api/users/<user_id>', methods=['DELETE'])
@api_login_required
def api_delete_user(user_id):
    if not is_admin():
        return jsonify({"error": "Admin access required"}), 403
        
    uid = get_object_id(user_id)
    if not uid:
        return jsonify({"error": "Invalid user ID"}), 400
        
    # Prevent deleting self
    if str(request.user['_id']) == str(uid):
        return jsonify({"error": "Cannot delete your own admin account"}), 400
        
    result = db.users.delete_one({"_id": uid})
    if result.deleted_count == 0:
        return jsonify({"error": "User not found"}), 404
        
    db.predictions.delete_many({"user_id": uid})
    
    return jsonify({"success": True})
