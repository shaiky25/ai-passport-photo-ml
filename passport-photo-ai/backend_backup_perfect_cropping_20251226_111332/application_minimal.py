"""
Minimal test application for AWS deployment
"""
from flask import Flask, jsonify
from flask_cors import CORS

application = Flask(__name__)
CORS(application)

@application.route('/', methods=['GET'])
def root():
    return jsonify({"status": "healthy", "message": "Minimal test app running"}), 200

@application.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Minimal test app running"}), 200

if __name__ == '__main__':
    application.run(debug=False, host='0.0.0.0', port=5000)