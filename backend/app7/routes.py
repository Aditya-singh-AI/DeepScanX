"""
app7/routes.py — DeepScanX AI Chatbot page
The AI chat is handled entirely client-side via Puter.js (free, no API key needed).
This module only serves the chatbot page HTML.
"""
from flask import Blueprint, render_template, request, make_response
from utils.helpers import login_required

bp = Blueprint('app7', __name__, template_folder='templates')


@bp.route('/')
@login_required
def chatbot_page():
    response = make_response(render_template('chatbot.html', user=request.user))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
