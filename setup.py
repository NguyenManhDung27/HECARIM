from setuptools import setup, find_packages

setup(
    name="hospital-management",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'flask==2.0.1',
        'flask-login==0.5.0',
        'flask-pymongo==2.3.0',
        'python-dotenv==1.0.0',
        'bcrypt==4.0.1',
        'python-jose==3.3.0',
        'email-validator==2.0.0',
        'pytest==7.4.0',
        'python-dateutil==2.8.2',
        'Werkzeug==2.0.1',
    ],
    python_requires='>=3.8',
)