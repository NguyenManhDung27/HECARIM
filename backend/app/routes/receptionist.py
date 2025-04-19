from flask import Blueprint, render_template
from flask_login import login_required, current_user
from datetime import datetime

receptionist_bp = Blueprint('receptionist', __name__)

@receptionist_bp.route('/dashboard')
@login_required
def dashboard():
    stats = {
        'total_appointments': 12,
        'checked_in': 5,
        'waiting': 4,
        'completed': 3
    }

    waiting_list = []
    recent_activities = []

    today = datetime.today()

    return render_template(
        'receptionist/dashboard.html',
        stats=stats,
        waiting_list=waiting_list,
        recent_activities=recent_activities,
        notifications_count=3,  # hoặc context processor như đã nói
        today=today
    )
