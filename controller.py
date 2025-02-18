from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, Response
import logging
import ctypes
import sys
import os
import argparse
import pymysql
import uuid
import pyperclip  # For clipboard functionality
from datetime import datetime
from waitress import serve
from server_tools import connect_to_db
app = Flask(__name__)
app.secret_key = 'nti_secret_key_2024'
 
# Set your desired password
PASSWORD = "Pr0j3ctFW1m"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database operations
def create_license(conn, user_id, company):
    """ Create a license entry and return the activation key. """
    activation_key = str(uuid.uuid4())
    default_hash = "default_hash_value"
    
    with conn.cursor() as cur:
        cur.execute(""" 
            INSERT INTO licenses (id, activation_key, hash, activated_on, company) 
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, activation_key, default_hash, None, company))
    conn.commit()

    return activation_key

def initialize_db(conn):
    """ Initialize the database by creating the licenses table if it doesn't exist. """
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                id VARCHAR(255) PRIMARY KEY,
                activation_key VARCHAR(255) NOT NULL UNIQUE,
                hash VARCHAR(255) NOT NULL,
                activated_on TIMESTAMP NULL
            )
        """)
        conn.commit()
    print("Database initialized.")

def remove_entry(conn, entry_id):
    """ Remove a license entry by its ID. """
    with conn.cursor() as cur:
        cur.execute("DELETE FROM licenses WHERE id = %s", (entry_id,))
    conn.commit()

def list_entries(conn):
    """ List all licenses in the database. """
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM licenses")
        entries = cur.fetchall()
    return entries

# Helper functions
def is_admin():
    """Check if the script is run as root (UID 0)."""
    return os.geteuid() == 0


def filter_licenses(licenses, search_term):
    """Filter licenses based on search term"""
    if not search_term:
        return licenses
    search_term = search_term.lower()
    return [
        license for license in licenses
        if search_term in str(license['id']).lower() or \
           search_term in str(license['activation_key']).lower()
    ]
# Password protection
@app.route('/login', methods=['GET', 'POST'])
def login():
    """ Password login page route """
    if request.method == 'POST':
        password = request.form.get('password')
        if password == PASSWORD:
            session['logged_in'] = True
            flash("Login successful!", "success")
            return redirect(url_for('index'))
        else:
            flash("Incorrect password. Please try again.", "error")
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/')
def index():
    """ Main page route """
    if not session.get('logged_in'):
        return redirect(url_for('login'))  # Redirect to login if not authenticated
    
    try:
        conn = connect_to_db()
        licenses = list_entries(conn)
                # Count the NTi licenses
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM licenses WHERE company = 'NTi'")
            nti_count = cur.fetchone()[0]  # Fetch the count of NTi licenses
        return render_template('index.html', licenses=licenses, nti_count=nti_count
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        flash(f"Error: {str(e)}", "error")
        return render_template('index.html', licenses=[])
    


    
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        flash(f"Error: {str(e)}", "error")
        return render_template('index.html', licenses=[], nti_count=0)

@app.route('/search')
def search():
    """Dynamic search endpoint"""
    try:
        conn = connect_to_db()
        search_term = request.args.get('term', '')
        all_licenses = list_entries(conn)
        filtered_licenses = filter_licenses(all_licenses, search_term)
        return jsonify(filtered_licenses)
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/create', methods=['POST'])
def create_new_license():
    """ Create new license route with company tracking """
    try:
        conn = connect_to_db()
        user_id = request.form.get('user_id')
        company = request.form.get('company', 'individual')  # Default to 'individual' unless specified

        if not user_id:
            flash("User ID is required", "error")
            return redirect(url_for('index'))

        activation_key = create_license(conn, user_id, company)
        flash(f"License created successfully. Key: {activation_key}", "success")
    except Exception as e:
        logger.error(f"Error creating license: {e}")
        flash(f"Failed to create license: {str(e)}", "error")

    return redirect(url_for('index'))

@app.route('/export', methods=['GET'])
def export_licenses():
    try:
        conn = connect_to_db()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM licenses")
            licenses = cur.fetchall()
            def generate():
                yield "ID,Activation Key,Status,Activated On\n"
                for license in licenses:
                    status = "Activated" if license['activated_on'] else "Not Activated"
                    yield f"{license['id']},{license['activation_key']},{status},{license['activated_on'] or ''}\n"
            return Response(generate(), mimetype='text/csv',
                            headers={"Content-Disposition": "attachment;filename=licenses.csv"})
    except Exception as e:
        logger.error(f"Error exporting licenses: {e}")
        return jsonify({"error": "Failed to export licenses"}), 500

@app.route('/license_management')
def license_management():
    # Get all licenses from the database
    licenses = License.query.all()

    # Count how many have company == "NTi"
    nti_count = License.query.filter_by(company='NTi').count()

    return render_template('license_management.html', licenses=licenses, nti_count=nti_count)

@app.route('/delete/<license_id>', methods=['POST'])
def delete_license(license_id):
    """ Delete license route """
    try:
        conn = connect_to_db()
        remove_entry(conn, license_id)
        flash("License deleted successfully", "success")
    except Exception as e:
        logger.error(f"Error deleting license: {e}")
        flash(f"Failed to delete license: {str(e)}", "error")
    
    return redirect(url_for('index'))


# CLI interface
def main():
    """ Command line interface for managing licenses. """
    parser = argparse.ArgumentParser(description='Manage database entries.')
    parser.add_argument('--init',
                        action='store_true',
                        help='Initialize the database')
    parser.add_argument('--add',
                        metavar='ENTRY',
                        help='Add an entry to the database. Example: --add "id=1 hash=hash activation_key=activation-key"')
    parser.add_argument('--remove',
                        metavar='ID',
                        type=int,
                        help='Remove an entry from the database by ID')
    parser.add_argument('--list',
                        action='store_true',
                        help='List all entries in the database')

    args = parser.parse_args()

    conn = connect_to_db()

    if args.init:
        initialize_db(conn)
    elif args.add:
        arguments = args.add.split(' ')
        entry = {
            'id': arguments[0].split('id=')[-1],
            'hash': arguments[1].split('hash=')[-1],
            'activation_key': arguments[2].split('activation_key=')[-1],
            'activated_on': arguments[3].split('activated_on=')[-1],
        }
        create_license(conn, entry['id'])
    elif args.remove:
        remove_entry(conn, args.remove)
    elif args.list:
        entries = list_entries(conn)
        for entry in entries:
            print(f"ID: {entry['id']}, Hash: {entry['hash']}, Activation Key: {entry['activation_key']}, Activated On: {entry['activated_on']}")
    else:
        parser.print_help()

# Flask app initialization
if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        try:
            if not is_admin():
                print("This script must be run with administrator privileges to use port 80")
                print("Please right-click and select 'Run as administrator'")
                if sys.executable.lower().endswith('pythonw.exe'):
                    ctypes.windll.user32.MessageBoxW(0, 
                        "This script must be run with administrator privileges to use port 80\n"
                        "Please right-click and select 'Run as administrator'", 
                        "Administrator Rights Required", 0x10)
                sys.exit(1)

            print("Starting license management interface...")
            conn = connect_to_db()
            initialize_db(conn)
            print("Access the interface at http://licenses.nti.local")
            serve(app, host="0.0.0.0", port=80, threads=4)
        except Exception as e:
            logger.error(f"Server failed to start: {e}")
            print(f"Error starting the server: {e}")