# database.py
import sqlite3
from datetime import datetime, timedelta

DB_NAME = "clients.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Check if the clients table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clients'")
    table_exists = c.fetchone() is not None
    
    if not table_exists:
        # Create new table with payment_amount field
        c.execute('''
            CREATE TABLE clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT UNIQUE,
                name TEXT,
                email TEXT,
                profile TEXT,
                start_date TEXT,
                end_date TEXT,
                status TEXT,
                payment_amount REAL DEFAULT 0.0,
                is_burned INTEGER DEFAULT 0,
                burn_reason TEXT DEFAULT NULL,
                burn_date TEXT DEFAULT NULL
            )
        ''')
    else:
        # Check and add columns if they don't exist
        columns_to_add = [
            ("payment_amount", "REAL DEFAULT 0.0"),
            ("is_burned", "INTEGER DEFAULT 0"),
            ("burn_reason", "TEXT DEFAULT NULL"),
            ("burn_date", "TEXT DEFAULT NULL")
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                c.execute(f"SELECT {column_name} FROM clients LIMIT 1")
            except sqlite3.OperationalError:
                # Add column to existing table
                c.execute(f"ALTER TABLE clients ADD COLUMN {column_name} {column_type}")
    
    # Create burned_tokens table if it doesn't exist
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='burned_tokens'")
    burned_table_exists = c.fetchone() is not None
    
    if not burned_table_exists:
        c.execute('''
            CREATE TABLE burned_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT UNIQUE,
                burn_reason TEXT,
                burn_date TEXT,
                client_id INTEGER,
                FOREIGN KEY (client_id) REFERENCES clients (id)
            )
        ''')
    
    conn.commit()
    conn.close()

def parse_duration(duration):
    """Parse duration string like '30', '2m', '1h' into timedelta"""
    if isinstance(duration, int) or duration.isdigit():
        # Regular days
        return timedelta(days=int(duration))
    elif duration.endswith('m'):
        # Minutes
        try:
            minutes = int(duration[:-1])
            return timedelta(minutes=minutes)
        except ValueError:
            raise ValueError(f"Invalid minute format: {duration}")
    elif duration.endswith('h'):
        # Hours
        try:
            hours = int(duration[:-1])
            return timedelta(hours=hours)
        except ValueError:
            raise ValueError(f"Invalid hour format: {duration}")
    else:
        raise ValueError(f"Unsupported duration format: {duration}")

def add_client(token, name, email, profile, duration):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    start = datetime.now()
    
    # Parse duration (can be days, minutes, or hours)
    duration_delta = parse_duration(duration)
    end = start + duration_delta
    
    c.execute('''
        INSERT INTO clients (token, name, email, profile, start_date, end_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (token, name, email, profile, start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S"), "Unpaid"))
    conn.commit()
    conn.close()
    return start, end

def token_exists(token):
    """Check if a token already exists in the database"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM clients WHERE token=?", (token,))
    count = c.fetchone()[0]
    conn.close()
    return count > 0

def get_client_by_token(token):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM clients WHERE token=?", (token,))
    client = c.fetchone()
    conn.close()
    return client

def update_status(token, new_status, payment_amount=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    if payment_amount is not None:
        # Update both status and payment amount
        c.execute("UPDATE clients SET status=?, payment_amount=? WHERE token=?", 
                 (new_status, payment_amount, token))
    else:
        # Update only status
        c.execute("UPDATE clients SET status=? WHERE token=?", (new_status, token))
    
    conn.commit()
    conn.close()

def extend_subscription(token, extra_days):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT end_date FROM clients WHERE token=?", (token,))
    result = c.fetchone()
    if not result:
        conn.close()
        return None
    
    # Try to parse with time component first, then fall back to just date
    try:
        old_end = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            old_end = datetime.strptime(result[0], "%Y-%m-%d")
        except ValueError:
            # If both formats fail, log error and return None
            print(f"Error parsing date: {result[0]}")
            conn.close()
            return None
    
    new_end = old_end + timedelta(days=extra_days)
    
    # Preserve the time component if it existed in the original date
    if ":" in result[0]:
        new_end_str = new_end.strftime("%Y-%m-%d %H:%M:%S")
    else:
        new_end_str = new_end.strftime("%Y-%m-%d")
    
    c.execute("UPDATE clients SET end_date=? WHERE token=?", (new_end_str, token))
    conn.commit()
    conn.close()
    return new_end

def get_unpaid_clients():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT token, name, profile, start_date, end_date FROM clients WHERE status='Unpaid'")
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_clients():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT token, name, email, profile, start_date, end_date, status FROM clients")
    rows = c.fetchall()
    conn.close()
    return rows

def burn_token(token, reason):
    """Mark a token as burned with a reason"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Get current time
    burn_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # First check if token exists
    c.execute("SELECT id FROM clients WHERE token=?", (token,))
    result = c.fetchone()
    
    if not result:
        conn.close()
        return False, "Token not found"
    
    client_id = result[0]
    
    # Check if token is already burned
    c.execute("SELECT is_burned FROM clients WHERE token=?", (token,))
    is_burned = c.fetchone()[0]
    
    if is_burned:
        conn.close()
        return False, "Token is already burned"
    
    # Update client record
    c.execute("UPDATE clients SET is_burned=1, burn_reason=?, burn_date=? WHERE token=?", 
              (reason, burn_date, token))
    
    # Add to burned_tokens table
    c.execute("INSERT INTO burned_tokens (token, burn_reason, burn_date, client_id) VALUES (?, ?, ?, ?)",
              (token, reason, burn_date, client_id))
    
    conn.commit()
    conn.close()
    return True, f"Token {token} has been burned successfully"

def get_burned_tokens():
    """Get all burned tokens"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""SELECT bt.token, bt.burn_reason, bt.burn_date, c.name, c.email, c.profile 
               FROM burned_tokens bt 
               JOIN clients c ON bt.client_id = c.id 
               ORDER BY bt.burn_date DESC""")
    tokens = c.fetchall()
    conn.close()
    return tokens

def get_stats():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Total clients
    c.execute("SELECT COUNT(*) FROM clients")
    total = c.fetchone()[0]
    
    # Paid clients
    c.execute("SELECT COUNT(*) FROM clients WHERE status='Paid'")
    paid = c.fetchone()[0]
    
    # Unpaid clients
    c.execute("SELECT COUNT(*) FROM clients WHERE status='Unpaid'")
    unpaid = c.fetchone()[0]
    
    # Expired clients
    c.execute("SELECT COUNT(*) FROM clients WHERE datetime(end_date) < datetime('now')")
    expired = c.fetchone()[0]
    
    # Burned tokens
    c.execute("SELECT COUNT(*) FROM clients WHERE is_burned=1")
    burned = c.fetchone()[0]
    
    conn.close()
    return total, paid, unpaid, expired, burned

def get_expiring_clients(days):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    today = datetime.now()
    limit = today + timedelta(days=days)
    c.execute("SELECT token, name, profile, end_date, status FROM clients WHERE end_date <= ?", (limit.strftime("%Y-%m-%d"),))
    rows = c.fetchall()
    conn.close()
    return rows

def search_clients(query):
    """
    Search for clients by name, email, profile, or token
    Returns matching clients
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Use LIKE for case-insensitive partial matching
    search_query = f"%{query}%"
    
    c.execute("""
        SELECT token, name, email, profile, start_date, end_date, status 
        FROM clients 
        WHERE 
            token LIKE ? OR 
            name LIKE ? OR 
            email LIKE ? OR 
            profile LIKE ?
    """, (search_query, search_query, search_query, search_query))
    
    rows = c.fetchall()
    conn.close()
    return rows
