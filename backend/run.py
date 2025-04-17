import os
from backend.app import create_app
from flask import send_from_directory

# Get environment configuration
env = os.getenv('FLASK_ENV', 'development')
app = create_app(env)

# Add route for serving static files
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('../frontend/static', path)

# Add route for the root URL to serve the login page
@app.route('/')
def index():
    return send_from_directory('../frontend/templates/auth', 'login.html')

if __name__ == '__main__':
    # Set host to 0.0.0.0 to make it accessible from outside the container
    app.run(host='0.0.0.0', port=5000)