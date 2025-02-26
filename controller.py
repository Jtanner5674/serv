from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__)

# Determine the base directory of this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    """Main page route"""
    return render_template('index.html')

@app.route('/.well-known/pki-validation/7808F76644558602520F32FD9DF9790C.txt')
def serve_pki_validation():
    return send_from_directory(BASE_DIR, "7808F76644558602520F32FD9DF9790C.txt")

if __name__ == "__main__":
    # Build the full paths to the certificate and key files
    cert_path = os.path.join(BASE_DIR, "tnrtechnologies_net.crt")
    key_path = os.path.join(BASE_DIR, "private.key")
    
    # Run the Flask app with SSL on port 443
    app.run(host="0.0.0.0", port=443, ssl_context=(cert_path, key_path))
