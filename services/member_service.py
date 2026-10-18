import re
from datetime import date
from database import get_connection

EMAIL_REGEX = re.compile(r"^[\w\.-]+@([\w-]+\.)+[\w-]{2,4}$")

def validate_member_payload(data):
    """Validate member details."""
    errors = []
    full_name = data.get('full_name', '').strip() if data.get('full_name') else ''
    email = data.get('email', '').strip().lower() if data.get('email') else ''
    phone = data.get('phone', '').strip() if data.get('phone') else ''
    status = data.get('membership_status', 'Active').strip() if data.get('membership_status') else 'Active'
    reg_date = data.get('registration_date', date.today().isoformat()).strip() if data.get('registration_date') else date.today().isoformat()

    if not full_name:
        errors.append("Member full name is required.")
    if not email:
        errors.append("Email address is required.")
    elif not EMAIL_REGEX.match(email):
        errors.append("Invalid email address format.")
    if not phone:
        errors.append("Phone number is required.")
    if status not in ['Active', 'Suspended', 'Expired']:
        errors.append("Membership status must be 'Active', 'Suspended', or 'Expired'.")

    return errors, {
        'full_name': full_name,
        'email': email,
        'phone': phone,
        'membership_status': status,
        'registration_date': reg_date
    }

def get_all_members(search=None, status=None, sort_by='full_name', order='asc', db_path=None):
    """
    Retrieve all members with search, filter, and borrowing counts.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    conditions = []
    params = []

    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        conditions.append("(LOWER(m.full_name) LIKE ? OR LOWER(m.email) LIKE ? OR m.phone LIKE ?)")
        params.extend([term, term, term])

    if status and status.strip() and status.strip().lower() != 'all':
        conditions.append("m.membership_status = ?")
        params.append(status.strip())

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    allowed_sort = {
        'full_name': 'm.full_name',
        'email': 'm.email',
        'registration_date': 'm.registration_date',
        'id': 'm.id'
    }
    col = allowed_sort.get(sort_by, 'm.full_name')
    dir_order = 'DESC' if order.lower() == 'desc' else 'ASC'

    query = f"""
        SELECT m.*,
               COUNT(CASE WHEN b.status IN ('Issued', 'Overdue') THEN 1 END) as active_loans_count,
               COUNT(b.id) as total_borrowings_count
        FROM members m
        LEFT JOIN borrowings b ON m.id = b.member_id
        {where_clause}
        GROUP BY m.id
        ORDER BY {col} {dir_order}
    """
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_member_by_id(member_id: int, db_path=None):
    """Retrieve single member by ID with loan summary."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.*,
               COUNT(CASE WHEN b.status IN ('Issued', 'Overdue') THEN 1 END) as active_loans_count,
               COUNT(b.id) as total_borrowings_count
        FROM members m
        LEFT JOIN borrowings b ON m.id = b.member_id
        WHERE m.id = ?
        GROUP BY m.id
    """, (member_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_member_by_email(email: str, db_path=None):
    """Retrieve member by email."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM members WHERE LOWER(email) = ?", (email.strip().lower(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_member(data, db_path=None):
    """Register a new member with duplicate email verification."""
    errors, clean_data = validate_member_payload(data)
    if errors:
        raise ValueError("; ".join(errors))

    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM members WHERE LOWER(email) = ?", (clean_data['email'],))
    if cursor.fetchone():
        conn.close()
        raise ValueError(f"A member with email '{clean_data['email']}' is already registered.")

    try:
        cursor.execute("""
            INSERT INTO members (full_name, email, phone, membership_status, registration_date)
            VALUES (?, ?, ?, ?, ?)
        """, (
            clean_data['full_name'],
            clean_data['email'],
            clean_data['phone'],
            clean_data['membership_status'],
            clean_data['registration_date']
        ))
        conn.commit()
        member_id = cursor.lastrowid
        return member_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def update_member(member_id: int, data, db_path=None):
    """Update existing member information."""
    current = get_member_by_id(member_id, db_path=db_path)
    if not current:
        raise ValueError(f"Member with ID {member_id} does not exist.")

    errors, clean_data = validate_member_payload(data)
    if errors:
        raise ValueError("; ".join(errors))

    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM members WHERE LOWER(email) = ? AND id != ?", (clean_data['email'], member_id))
    if cursor.fetchone():
        conn.close()
        raise ValueError(f"Another member with email '{clean_data['email']}' already exists.")

    try:
        cursor.execute("""
            UPDATE members
            SET full_name = ?, email = ?, phone = ?, membership_status = ?, registration_date = ?
            WHERE id = ?
        """, (
            clean_data['full_name'],
            clean_data['email'],
            clean_data['phone'],
            clean_data['membership_status'],
            clean_data['registration_date'],
            member_id
        ))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def delete_member(member_id: int, db_path=None):
    """Delete a member only if they have no active unreturned books."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) as active_count
        FROM borrowings
        WHERE member_id = ? AND status IN ('Issued', 'Overdue')
    """, (member_id,))
    active = cursor.fetchone()['active_count']

    if active > 0:
        conn.close()
        raise ValueError(f"Cannot delete member: {active} book(s) are currently checked out and not yet returned.")

    try:
        cursor.execute("DELETE FROM borrowings WHERE member_id = ? AND status = 'Returned'", (member_id,))
        cursor.execute("DELETE FROM members WHERE id = ?", (member_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_member_borrowing_history(member_id: int, db_path=None):
    """Retrieve full borrowing transaction history for a specific member."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.*, bk.title AS book_title, bk.author AS book_author, bk.isbn, bk.category
        FROM borrowings b
        JOIN books bk ON b.book_id = bk.id
        WHERE b.member_id = ?
        ORDER BY b.issue_date DESC, b.id DESC
    """, (member_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
