import pytest
from services.book_service import (
    add_book, update_book, delete_book, get_book_by_id,
    get_book_by_isbn, get_all_books
)
from services.borrowing_service import issue_book

def test_add_book_success(db_path):
    """Test successful book creation."""
    book_id = add_book({
        'title': 'Quantum Computing Principles',
        'author': 'Richard Feynman',
        'isbn': 'TEST-ISBN-QC-100',
        'category': 'Science',
        'publisher': 'Caltech Press',
        'publication_year': 2023,
        'total_copies': 4,
        'available_copies': 4,
        'description': 'Foundational quantum mechanics.',
        'cover_url': ''
    }, db_path=db_path)

    assert book_id is not None
    book = get_book_by_id(book_id, db_path=db_path)
    assert book['title'] == 'Quantum Computing Principles'
    assert book['available_copies'] == 4

def test_prevent_duplicate_isbn(db_path):
    """Ensure duplicate ISBN throws ValueError."""
    with pytest.raises(ValueError, match="already exists"):
        add_book({
            'title': 'Another QC Book',
            'author': 'Someone Else',
            'isbn': 'TEST-ISBN-QC-100',  # Duplicate!
            'category': 'Science',
            'publisher': 'Press',
            'publication_year': 2023,
            'total_copies': 2
        }, db_path=db_path)

def test_update_book_success(db_path, sample_book_id):
    """Test updating existing book information."""
    update_book(sample_book_id, {
        'title': 'Test Driven Development in Python (Updated Edition)',
        'author': 'Kent Beck & Friends',
        'isbn': 'TEST-ISBN-001',
        'category': 'Programming',
        'publisher': 'Tech Press Modern',
        'publication_year': 2025,
        'total_copies': 5
    }, db_path=db_path)

    updated = get_book_by_id(sample_book_id, db_path=db_path)
    assert updated['title'] == 'Test Driven Development in Python (Updated Edition)'
    assert updated['publication_year'] == 2025
    assert updated['total_copies'] == 5

def test_search_and_filter_books(db_path):
    """Test searching by title and filtering by category."""
    results = get_all_books(search='Quantum', db_path=db_path)
    assert any(b['isbn'] == 'TEST-ISBN-QC-100' for b in results['books'])

    cat_results = get_all_books(category='Science', db_path=db_path)
    assert all(b['category'] == 'Science' for b in cat_results['books'])

def test_prevent_delete_when_active_borrowing(db_path, sample_member_id):
    """Ensure deleting a book with active loans is blocked."""
    # Create a book to issue
    book_id = add_book({
        'title': 'Cannot Delete Book',
        'author': 'Author X',
        'isbn': 'TEST-ISBN-NODELETE',
        'category': 'Technology',
        'publisher': 'Pub',
        'publication_year': 2024,
        'total_copies': 2
    }, db_path=db_path)

    # Issue copy
    issue_book(book_id, sample_member_id, '2026-01-01', '2026-01-15', db_path=db_path)

    # Attempt delete
    with pytest.raises(ValueError, match="Cannot delete book"):
        delete_book(book_id, db_path=db_path)
