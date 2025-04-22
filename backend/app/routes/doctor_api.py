from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from ..extensions import mongo
from bson import ObjectId
from datetime import datetime

doctor_api = Blueprint('doctor/api', __name__)