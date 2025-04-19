from flask import Blueprint, render_template
from flask_login import login_required

patient_bp = Blueprint('patient', __name__)

@patient_bp.route('/dashboard')
@login_required
def dashboard():
    health_info = {
        'height': 170,  # Ví dụ: chiều cao
        'weight': 65,   # Ví dụ: cân nặng
        'bmi': 22.5,    # Ví dụ: chỉ số BMI
        'allergies': ['Dị ứng phấn hoa', 'Dị ứng thuốc']  # Ví dụ: danh sách dị ứng
    }
    return render_template('patient/dashboard.html', health_info=health_info)