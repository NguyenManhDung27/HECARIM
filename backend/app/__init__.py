from flask import Flask, redirect, url_for
from dotenv import load_dotenv
import os

from .extensions import mongo, login_manager, mail
from flask_mail import Mail

def create_app(env="development"):
    # Load environment variables
    load_dotenv()
    
    # Create Flask app
    app = Flask(__name__,
                static_folder='../../frontend/static',
                template_folder='../../frontend/templates')
    # Mail config
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')  # đặt trong .env
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  # dùng App Password
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')  # đặt trong .env
    # Configure app
    app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/hospital_management")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your-secret-key-here")
    # Initialize extensions with app
    mongo.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    with app.app_context():
        # Register blueprints
        from .routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')

        from .routes.doctor import doctor_bp
        app.register_blueprint(doctor_bp, url_prefix='/doctor')

        from .routes.doctor_api import doctor_api
        app.register_blueprint(doctor_api, url_prefix='/doctor/api')
        
        from .routes.receptionist import receptionist_bp
        app.register_blueprint(receptionist_bp, url_prefix='/receptionist')

        from .routes.receptionist_api import receptionist_api
        app.register_blueprint(receptionist_api, url_prefix='/receptionist/api')

        from .routes.patient import patient_bp
        app.register_blueprint(patient_bp, url_prefix='/patient')

        from .routes.patient_api import patient_api
        app.register_blueprint(patient_api, url_prefix='/patient/api')
        
        # Main route redirects to auth login
        @app.route('/')
        def main():
            return redirect(url_for('auth.login'))
            
    return app