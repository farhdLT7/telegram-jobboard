import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'jobboard.db')

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS copied_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_channel TEXT NOT NULL,
            message_id INTEGER NOT NULL,
            posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_channel, message_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            full_name TEXT,
            order_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            contact TEXT NOT NULL,
            salary_or_budget TEXT,
            status TEXT DEFAULT 'pending_payment',
            payment_id TEXT,
            amount INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            published_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def is_post_copied(source_channel, message_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM copied_posts WHERE source_channel=? AND message_id=?', (source_channel, message_id))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def mark_post_copied(source_channel, message_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO copied_posts (source_channel, message_id) VALUES (?, ?)', (source_channel, message_id))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

def create_order(user_id, username, full_name, order_type, title, description, contact, salary_or_budget, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (user_id, username, full_name, order_type, title, description, contact, salary_or_budget, amount)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, full_name, order_type, title, description, contact, salary_or_budget, amount))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_order(order_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders WHERE id=?', (order_id,))
    result = cursor.fetchone()
    conn.close()
    return dict(result) if result else None

def update_order_status(order_id, status, payment_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    if payment_id:
        cursor.execute('UPDATE orders SET status=?, payment_id=? WHERE id=?', (status, payment_id, order_id))
    else:
        cursor.execute('UPDATE orders SET status=? WHERE id=?', (status, order_id))
    conn.commit()
    conn.close()
