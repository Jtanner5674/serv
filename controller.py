from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__)

@app.route('/')
def index():
    """ Main page route """
    return render_template('index.html')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/.well-known/pki-validation/7808F76644558602520F32FD9DF9790C.txt')
def serve_pki_validation():
    return send_from_directory(BASE_DIR, "7808F76644558602520F32FD9DF9790C.txt")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
