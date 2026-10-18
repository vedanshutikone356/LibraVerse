import sqlite3
import os
from datetime import date
from flask import g, current_app

def get_db_path():
    """Retrieve the current database path from current_app or fallback to default."""
    try:
        return current_app.config['DATABASE']
    except (RuntimeError, KeyError):
        base_dir = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_dir, 'instance', 'library.db')

def get_connection(db_path=None):
    """Create and return a raw SQLite connection with row factory and foreign keys enabled."""
    if db_path is None:
        db_path = get_db_path()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def get_db():
    """Flask request-context aware database connection provider."""
    if 'db' not in g:
        g.db = get_connection()
    return g.db

def close_db(e=None):
    """Close request-context database connection if open."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(db_path=None):
    """Create all required tables, triggers, and indices if they do not exist."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Admins table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT DEFAULT 'admin',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Books table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        isbn TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        category TEXT NOT NULL,
        publisher TEXT NOT NULL,
        publication_year INTEGER NOT NULL,
        total_copies INTEGER NOT NULL CHECK(total_copies >= 0),
        available_copies INTEGER NOT NULL CHECK(available_copies >= 0 AND available_copies <= total_copies),
        description TEXT,
        cover_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Members table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,
        membership_status TEXT DEFAULT 'Active' CHECK(membership_status IN ('Active', 'Suspended', 'Expired')),
        registration_date DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Borrowing records table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS borrowings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE RESTRICT,
        member_id INTEGER NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
        issue_date DATE NOT NULL,
        due_date DATE NOT NULL,
        return_date DATE,
        status TEXT NOT NULL CHECK(status IN ('Issued', 'Returned', 'Overdue')),
        overdue_days INTEGER DEFAULT 0,
        fine_amount REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Performance indices
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_books_isbn ON books(isbn);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_books_category ON books(category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_members_email ON members(email);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_borrowings_status ON borrowings(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_borrowings_book ON borrowings(book_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_borrowings_member ON borrowings(member_id);")

    conn.commit()
    conn.close()

def update_overdue_statuses(db_path=None):
    """
    Check all unreturned borrowings past their due date and mark them as Overdue,
    updating the calculated overdue days and estimated fine.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    today_str = date.today().isoformat()

    # Find unreturned records where due_date < today
    cursor.execute("""
        SELECT id, due_date
        FROM borrowings
        WHERE return_date IS NULL AND due_date < ?
    """, (today_str,))
    rows = cursor.fetchall()

    for row in rows:
        b_id = row['id']
        due_val = row['due_date']
        if isinstance(due_val, str):
            due = date.fromisoformat(due_val)
        else:
            due = due_val
        overdue_days = max(0, (date.today() - due).days)
        fine = max(0.0, overdue_days * 1.50)  # $1.50 per day standard overdue fine
        cursor.execute("""
            UPDATE borrowings
            SET status = 'Overdue', overdue_days = ?, fine_amount = ?
            WHERE id = ?
        """, (overdue_days, fine, b_id))

    conn.commit()
    conn.close()
