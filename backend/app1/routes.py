from flask import Blueprint, render_template, request, redirect, url_for, send_file
from utils.helpers import login_required, optional_login, save_prediction
from app2.models import db
import io

bp = Blueprint('app1', __name__, template_folder='templates')


@bp.route('/')
@optional_login
def home():
    user = request.user
    # Stats for dashboard
    total_predictions = 0
    if user:
        total_predictions = db.predictions.count_documents({"user_id": user['_id']})
    return render_template('home.html', user=user, total_predictions=total_predictions)


@bp.route('/history')
@login_required
def history():
    user = request.user
    predictions = list(
        db.predictions.find({"user_id": user['_id']}).sort("timestamp", -1).limit(100)
    )
    return render_template('history.html', user=user, predictions=predictions)