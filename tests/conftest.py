import os
import pytest
from app import create_app
from database import init_db, get_connection
from services.auth_service import create_admin
from services.book_service import add_book
from services.member_service import add_member

TEST_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance', 'test_library.db'))

@pytest.fixture(scope='session', autouse=True)
def test_app():
    """Create Flask application in testing mode with a dedicated test SQLite database."""
    os.environ['DATABASE_PATH'] = TEST_DB_PATH
    os.environ['FLASK_ENV'] = 'testing'
    
    # Remove existing test DB if any
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except OSError:
            pass

    app = create_app('testing')
    app.config['DATABASE'] = TEST_DB_PATH
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['TESTING'] = True

    with app.app_context():
        init_db(TEST_DB_PATH)
        # Create a default test administrator
        create_admin(
            username='testadmin',
            email='testadmin@libraverse.test',
            password='TestPassword123!',
            full_name='Test Administrator',
            db_path=TEST_DB_PATH
        )
        yield app

    # Cleanup test DB after tests finish
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except OSError:
            pass

@pytest.fixture
def client(test_app):
    """Test client for HTTP requests."""
    return test_app.test_client()

@pytest.fixture
def db_path(test_app):
    """Return path to test database."""
    return TEST_DB_PATH

@pytest.fixture
def sample_book_id(db_path):
    """Seed a sample book and return its ID."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM books WHERE isbn = 'TEST-ISBN-001'")
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return existing['id']
    conn.close()

    book_id = add_book({
        'title': 'Test Driven Development in Python',
        'author': 'Kent Beck',
        'isbn': 'TEST-ISBN-001',
        'category': 'Programming',
        'publisher': 'Tech Press',
        'publication_year': 2024,
        'total_copies': 3,
        'available_copies': 3,
        'description': 'A comprehensive handbook for unit testing.',
        'cover_url': ''
    }, db_path=db_path)
    return book_id

@pytest.fixture
def sample_member_id(db_path):
    """Seed a sample member and return its ID."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM members WHERE email = 'test.member@example.com'")
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return existing['id']
    conn.close()

    member_id = add_member({
        'full_name': 'Test Reader',
        'email': 'test.member@example.com',
        'phone': '+1 (555) 000-1111',
        'membership_status': 'Active',
        'registration_date': '2026-01-01'
    }, db_path=db_path)
    return member_id
