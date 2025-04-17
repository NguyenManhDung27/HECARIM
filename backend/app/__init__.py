from flask import Flask
from flask_pymongo import PyMongo
from flask_login import LoginManager
from backend.config.settings import config

# Initialize MongoDB and Login Manager
mongo = PyMongo()
login_manager = LoginManager()

def create_app(config_name='default'):
    app = Flask(__name__, 
                template_folder='../../frontend/templates',
                static_folder='../../frontend/static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize MongoDB
    mongo.init_app(app)
    
    # Initialize Login Manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Vui lòng đăng nhập để tiếp tục.'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from backend.app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from backend.app.routes.patient import patient_bp
    app.register_blueprint(patient_bp, url_prefix='/patient')
    
    from backend.app.routes.doctor import doctor_bp
    app.register_blueprint(doctor_bp, url_prefix='/doctor')
    
    from backend.app.routes.receptionist import receptionist_bp
    app.register_blueprint(receptionist_bp, url_prefix='/receptionist')
    
    # Register API routes
    from backend.app.routes.receptionist_api import receptionist_api
    app.register_blueprint(receptionist_api, url_prefix='/receptionist/api')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Not Found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal Server Error'}, 500
        
    return app