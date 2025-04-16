from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)

# MongoDB connection - local instance
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['patient_health_db']
    # Test the connection
    client.server_info()
    print("Connected to MongoDB successfully")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    # Continue with the application even if DB connection fails
    # In a production environment, you might want to handle this differently

# Routes for main pages
@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/patients')
def patient_list():
    try:
        patients = list(db.patients.find())
        for patient in patients:
            patient['_id'] = str(patient['_id'])
    except Exception as e:
        print(f"Error fetching patients: {e}")
        patients = []
    return render_template('patient_list.html', patients=patients)

@app.route('/patients/new')
def patient_form():
    return render_template('patient_form.html')

@app.route('/metrics')
def metrics():
    return render_template('metrics.html')

@app.route('/history')
def medical_history():
    return render_template('medical_history.html')

@app.route('/appointments')
def appointments():
    return render_template('appointments.html')

# API routes for patient management
@app.route('/api/patients', methods=['GET'])
def get_patients():
    try:
        patients = list(db.patients.find())
        for patient in patients:
            patient['_id'] = str(patient['_id'])
        return jsonify(patients)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/patients', methods=['POST'])
def create_patient():
    patient_data = request.json
    try:
        result = db.patients.insert_one(patient_data)
        return jsonify({'_id': str(result.inserted_id)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/patients/<id>', methods=['GET'])
def get_patient(id):
    try:
        patient = db.patients.find_one({'_id': ObjectId(id)})
        if patient:
            patient['_id'] = str(patient['_id'])
            return jsonify(patient)
        return jsonify({'error': 'Patient not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/patients/<id>', methods=['PUT'])
def update_patient(id):
    try:
        patient_data = request.json
        result = db.patients.update_one(
            {'_id': ObjectId(id)},
            {'$set': patient_data}
        )
        if result.modified_count:
            return jsonify({'message': 'Patient updated successfully'})
        return jsonify({'error': 'Patient not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/patients/<id>', methods=['DELETE'])
def delete_patient(id):
    try:
        result = db.patients.delete_one({'_id': ObjectId(id)})
        if result.deleted_count:
            return jsonify({'message': 'Patient deleted successfully'})
        return jsonify({'error': 'Patient not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)