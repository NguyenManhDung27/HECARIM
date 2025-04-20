from flask import Flask, redirect, url_for
from dotenv import load_dotenv
import os

from .extensions import mongo, login_manager

def create_app(env="development"):
    # Load environment variables
    load_dotenv()
    
    # Create Flask app
    app = Flask(__name__,
                static_folder='../../frontend/static',
                template_folder='../../frontend/templates')
    
    # Configure app
    app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/hospital_management")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    # Initialize extensions with app
    mongo.init_app(app)
    login_manager.init_app(app)
    
    with app.app_context():
        # Register blueprints
        from .routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')

        from .routes.doctor import doctor_bp
        app.register_blueprint(doctor_bp, url_prefix='/doctor')

        from .routes.receptionist import receptionist_bp
        app.register_blueprint(receptionist_bp, url_prefix='/receptionist')

        from .routes.receptionist_api import receptionist_api
        app.register_blueprint(receptionist_api, url_prefix='/receptionist/api')

        from .routes.patient import patient_bp
        app.register_blueprint(patient_bp, url_prefix='/patient')
        
        # Main route redirects to auth login
        @app.route('/')
        def main():
            return redirect(url_for('auth.login'))
            
    return app