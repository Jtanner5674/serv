import os
import argparse
import pymysql
import uuid
import pyperclip  # For clipboard functionality
from datetime import datetime

def connect_to_db():
    """ Connect to the MariaDB database using connection parameters. """
    conn = pymysql.connect(
        database=os.getenv('DB_NAME', 'licenses'),  # Replace with your actual database name
        user=os.getenv('DB_USER', 'josh'),
        password=os.getenv('DB_PASS', 'root'),
        host=os.getenv('DB_HOST', '74.208.7.239'),
        port=int(os.getenv('DB_PORT', '8443')),
        cursorclass=pymysql.cursors.DictCursor  
    )
    return conn

def create_license(conn, user_id):
    """ Create a license entry and return the activation key. """
    activation_key = str(uuid.uuid4())
    default_hash = "default_hash_value"
    
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO licenses (id, activation_key, hash, activated_on)
            VALUES (%s, %s, %s, %s)
        """, (user_id, activation_key, default_hash, None))  # Pass None for NULL
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
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("SELECT * FROM licenses")
        entries = cur.fetchall()
    return entries

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
        # Initialize the database (you can modify this to create the table if needed)
        print("Initializing the database...")  # Add your initialization logic here
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

if __name__ == "__main__":
    main()
