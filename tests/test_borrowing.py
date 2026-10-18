import pytest
from datetime import date, timedelta
from services.book_service import add_book, get_book_by_id
from services.member_service import add_member
from services.borrowing_service import issue_book, return_book, get_borrowing_by_id
from database import update_overdue_statuses

def test_issue_book_success(db_path):
    """Test successful issuance decrements available stock."""
    # Create single-copy book
    book_id = add_book({
        'title': 'Limited Edition Python',
        'author': 'Guido van Rossum',
        'isbn': 'TEST-ISBN-LIMITED-1',
        'category': 'Programming',
        'publisher': 'Python Software Foundation',
        'publication_year': 2024,
        'total_copies': 1,
        'available_copies': 1
    }, db_path=db_path)

    member_id = add_member({
        'full_name': 'Borrower Alpha',
        'email': 'alpha@borrower.com',
        'phone': '123456789',
        'membership_status': 'Active'
    }, db_path=db_path)

    today = date.today().isoformat()
    due = (date.today() + timedelta(days=14)).isoformat()

    borrowing_id = issue_book(book_id, member_id, today, due, db_path=db_path)
    assert borrowing_id is not None

    # Check that available copies is now 0
    book = get_book_by_id(book_id, db_path=db_path)
    assert book['available_copies'] == 0

    # Attempt to issue again when 0 copies left -> must fail!
    with pytest.raises(ValueError, match="No copies available"):
        issue_book(book_id, member_id, today, due, db_path=db_path)

def test_return_book_and_prevent_duplicate_return(db_path):
    """Test returning book increments stock and prevents double return."""
    book_id = add_book({
        'title': 'Returnable Book',
        'author': 'Author R',
        'isbn': 'TEST-ISBN-RET-01',
        'category': 'Science',
        'publisher': 'Press',
        'publication_year': 2024,
        'total_copies': 2,
        'available_copies': 2
    }, db_path=db_path)

    member_id = add_member({
        'full_name': 'Borrower Beta',
        'email': 'beta@borrower.com',
        'phone': '987654321',
        'membership_status': 'Active'
    }, db_path=db_path)

    today = date.today()
    issue_date = (today - timedelta(days=10)).isoformat()
    due_date = (today + timedelta(days=4)).isoformat()

    borrowing_id = issue_book(book_id, member_id, issue_date, due_date, db_path=db_path)
    
    # Available should be 1
    book = get_book_by_id(book_id, db_path=db_path)
    assert book['available_copies'] == 1

    # Return on time
    res = return_book(borrowing_id, today.isoformat(), db_path=db_path)
    assert res['overdue_days'] == 0
    assert res['fine_amount'] == 0.0

    # Available should now be back to 2
    book_after = get_book_by_id(book_id, db_path=db_path)
    assert book_after['available_copies'] == 2

    # Attempt duplicate return -> must raise ValueError!
    with pytest.raises(ValueError, match="already been returned"):
        return_book(borrowing_id, today.isoformat(), db_path=db_path)

def test_overdue_calculation(db_path):
    """Test overdue days and fine calculation on late return."""
    book_id = add_book({
        'title': 'Late Return Book',
        'author': 'Author L',
        'isbn': 'TEST-ISBN-LATE-01',
        'category': 'History',
        'publisher': 'Press',
        'publication_year': 2020,
        'total_copies': 3,
        'available_copies': 3
    }, db_path=db_path)

    member_id = add_member({
        'full_name': 'Borrower Late',
        'email': 'late@borrower.com',
        'phone': '5551234',
        'membership_status': 'Active'
    }, db_path=db_path)

    today = date.today()
    issue_date = (today - timedelta(days=20)).isoformat()
    due_date = (today - timedelta(days=6)).isoformat()  # was due 6 days ago

    borrowing_id = issue_book(book_id, member_id, issue_date, due_date, db_path=db_path)

    # Return today (6 days overdue)
    res = return_book(borrowing_id, today.isoformat(), db_path=db_path)
    assert res['overdue_days'] == 6
    assert res['fine_amount'] == 6 * 1.50
