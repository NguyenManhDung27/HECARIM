from flask import Blueprint, render_template
from flask_login import login_required

receptionist_bp = Blueprint('receptionist', __name__)

@receptionist_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('receptionist/dashboard.html')
