from flask_pymongo import PyMongo
from flask_login import LoginManager

# Initialize MongoDB
mongo = PyMongo()

# Initialize Login Manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Vui lòng đăng nhập để tiếp tục.'
login_manager.login_message_category = 'info'