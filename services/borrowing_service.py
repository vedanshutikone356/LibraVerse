from datetime import date, datetime
from database import get_connection

def issue_book(book_id: int, member_id: int, issue_date_str: str, due_date_str: str, db_path=None):
    """
    Issue an available copy of a book to an active library member.
    Executes in a single SQLite transaction to guarantee consistency.
    """
    # Parse and validate dates
    try:
        issue_d = date.fromisoformat(issue_date_str.strip())
        due_d = date.fromisoformat(due_date_str.strip())
    except (ValueError, AttributeError):
        raise ValueError("Invalid date format. Expected YYYY-MM-DD.")

    if due_d < issue_d:
        raise ValueError("Due date cannot be earlier than issue date.")

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        # Check member status
        cursor.execute("SELECT id, full_name, membership_status FROM members WHERE id = ?", (member_id,))
        member = cursor.fetchone()
        if not member:
            raise ValueError(f"Member ID {member_id} not found.")
        if member['membership_status'] != 'Active':
            raise ValueError(f"Member '{member['full_name']}' is currently {member['membership_status']}. Cannot issue books.")

        # Check book availability
        cursor.execute("SELECT id, title, available_copies, total_copies FROM books WHERE id = ?", (book_id,))
        book = cursor.fetchone()
        if not book:
            raise ValueError(f"Book ID {book_id} not found.")
        if book['available_copies'] <= 0:
            raise ValueError(f"No copies available for '{book['title']}'. All {book['total_copies']} copies are currently checked out.")

        # Determine initial status
        today = date.today()
        status = 'Overdue' if due_d < today else 'Issued'
        overdue_days = max(0, (today - due_d).days) if status == 'Overdue' else 0
        fine = overdue_days * 1.50

        # Decrement available copies
        cursor.execute("""
            UPDATE books
            SET available_copies = available_copies - 1
            WHERE id = ? AND available_copies > 0
        """, (book_id,))

        if cursor.rowcount == 0:
            raise ValueError("Failed to reserve book copy. Availability changed.")

        # Insert borrowing record
        cursor.execute("""
            INSERT INTO borrowings (book_id, member_id, issue_date, due_date, status, overdue_days, fine_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (book_id, member_id, issue_d.isoformat(), due_d.isoformat(), status, overdue_days, fine))

        borrowing_id = cursor.lastrowid
        conn.commit()
        return borrowing_id

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def return_book(borrowing_id: int, return_date_str: str = None, db_path=None):
    """
    Record book return, increment available stock, compute overdue days/fine,
    and prevent duplicate return in a safe database transaction.
    """
    if not return_date_str:
        return_d = date.today()
    else:
        try:
            return_d = date.fromisoformat(return_date_str.strip())
        except (ValueError, AttributeError):
            raise ValueError("Invalid return date format. Expected YYYY-MM-DD.")

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        # Fetch current record with book details
        cursor.execute("""
            SELECT b.*, bk.available_copies, bk.total_copies, bk.title AS book_title
            FROM borrowings b
            JOIN books bk ON b.book_id = bk.id
            WHERE b.id = ?
        """, (borrowing_id,))
        record = cursor.fetchone()

        if not record:
            raise ValueError(f"Borrowing transaction #{borrowing_id} not found.")

        if record['status'] == 'Returned':
            raise ValueError(f"Transaction #{borrowing_id} has already been returned on {record['return_date']}.")

        issue_val = record['issue_date']
        issue_d = date.fromisoformat(issue_val) if isinstance(issue_val, str) else issue_val
        if return_d < issue_d:
            raise ValueError("Return date cannot precede the issue date.")

        due_val = record['due_date']
        due_d = date.fromisoformat(due_val) if isinstance(due_val, str) else due_val
        overdue_days = max(0, (return_d - due_d).days)
        fine = overdue_days * 1.50

        # Increment available copies
        cursor.execute("""
            UPDATE books
            SET available_copies = available_copies + 1
            WHERE id = ? AND available_copies < total_copies
        """, (record['book_id'],))

        if cursor.rowcount == 0:
            # Check if copies were already at maximum
            cursor.execute("SELECT available_copies, total_copies FROM books WHERE id = ?", (record['book_id'],))
            b_check = cursor.fetchone()
            if b_check['available_copies'] >= b_check['total_copies']:
                raise ValueError("All copies for this book are already marked as returned.")

        # Update borrowing record
        cursor.execute("""
            UPDATE borrowings
            SET return_date = ?, status = 'Returned', overdue_days = ?, fine_amount = ?
            WHERE id = ?
        """, (return_d.isoformat(), overdue_days, fine, borrowing_id))

        conn.commit()
        return {
            'borrowing_id': borrowing_id,
            'overdue_days': overdue_days,
            'fine_amount': fine,
            'book_title': record['book_title']
        }

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_all_borrowings(status=None, search=None, sort_by='issue_date', order='desc', db_path=None):
    """
    Retrieve full list of borrowing transactions joined with book and member information.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    conditions = []
    params = []

    if status and status.strip() and status.strip().lower() != 'all':
        conditions.append("b.status = ?")
        params.append(status.strip())

    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        conditions.append("(LOWER(bk.title) LIKE ? OR LOWER(m.full_name) LIKE ? OR LOWER(bk.isbn) LIKE ? OR LOWER(m.email) LIKE ?)")
        params.extend([term, term, term, term])

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    allowed_sort = {
        'issue_date': 'b.issue_date',
        'due_date': 'b.due_date',
        'return_date': 'b.return_date',
        'id': 'b.id',
        'title': 'bk.title',
        'member': 'm.full_name',
        'status': 'b.status'
    }
    col = allowed_sort.get(sort_by, 'b.issue_date')
    dir_order = 'DESC' if order.lower() == 'desc' else 'ASC'

    query = f"""
        SELECT b.*,
               bk.title AS book_title,
               bk.author AS book_author,
               bk.isbn AS book_isbn,
               bk.category AS book_category,
               m.full_name AS member_name,
               m.email AS member_email,
               m.phone AS member_phone
        FROM borrowings b
        JOIN books bk ON b.book_id = bk.id
        JOIN members m ON b.member_id = m.id
        {where_clause}
        ORDER BY {col} {dir_order}, b.id DESC
    """
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_borrowing_by_id(borrowing_id: int, db_path=None):
    """Retrieve detailed borrowing transaction record."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.*,
               bk.title AS book_title,
               bk.author AS book_author,
               bk.isbn AS book_isbn,
               bk.category AS book_category,
               bk.cover_url AS book_cover,
               m.full_name AS member_name,
               m.email AS member_email,
               m.phone AS member_phone
        FROM borrowings b
        JOIN books bk ON b.book_id = bk.id
        JOIN members m ON b.member_id = m.id
        WHERE b.id = ?
    """, (borrowing_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None
