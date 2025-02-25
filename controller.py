from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    """ Main page route """
    return render_template('index.html')

# Flask app initialization
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
