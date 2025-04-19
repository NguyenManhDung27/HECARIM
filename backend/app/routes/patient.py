from flask import Blueprint, render_template
from flask_login import login_required

patient_bp = Blueprint('patient', __name__)

@patient_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('patient/dashboard.html')