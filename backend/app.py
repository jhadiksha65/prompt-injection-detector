"""
app.py
Flask backend for the Browser-Based Prompt Injection Detection Framework.

CA-1 Scope:
This backend currently provides only a health check endpoint to verify
that the Flask server is running successfully.

Detection logic will be added in later reviews.
"""

from flask import Flask, jsonify
from flask_cors import CORS

# Create Flask application
app = Flask(__name__)

# Enable Cross-Origin Resource Sharing
CORS(app)

# -------------------------------
# Health Check Route
# -------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "message": "Backend is running successfully."
    })

# -------------------------------
# Run Flask Server
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)