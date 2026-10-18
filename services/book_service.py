import math
from datetime import datetime
from database import get_connection

DEFAULT_CATEGORIES = [
    'Technology',
    'Programming',
    'Science',
    'Fiction',
    'Mystery',
    'History',
    'Business',
    'Personal Development'
]

def get_categories(db_path=None):
    """Retrieve distinct book categories from the database, combined with standard categories."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM books ORDER BY category ASC")
    rows = cursor.fetchall()
    conn.close()
    
    db_cats = [r['category'] for r in rows if r['category']]
    all_cats = sorted(list(set(DEFAULT_CATEGORIES + db_cats)))
    return all_cats

def get_featured_books(limit=6, db_path=None):
    """Retrieve featured books for hero and homepage showcase."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.*, (b.total_copies - b.available_copies) AS issued_copies
        FROM books b
        ORDER BY b.available_copies DESC, b.id ASC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_books(search=None, category=None, availability=None, sort_by='title', order='asc', page=1, per_page=12, db_path=None):
    """
    Search, filter, sort, and paginate the book collection.
    Returns: dict with 'books', 'total', 'page', 'per_page', 'total_pages'
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    conditions = []
    params = []

    # Search filter (title, author, isbn, category)
    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        conditions.append("(LOWER(title) LIKE ? OR LOWER(author) LIKE ? OR LOWER(isbn) LIKE ? OR LOWER(category) LIKE ?)")
        params.extend([term, term, term, term])

    # Category filter
    if category and category.strip() and category.strip().lower() != 'all':
        conditions.append("LOWER(category) = ?")
        params.append(category.strip().lower())

    # Availability filter
    if availability == 'available':
        conditions.append("available_copies > 0")
    elif availability == 'unavailable':
        conditions.append("available_copies = 0")

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    # Validate sorting options to prevent SQL injection
    allowed_sort = {
        'title': 'title',
        'author': 'author',
        'publication_year': 'publication_year',
        'created_at': 'created_at',
        'available_copies': 'available_copies',
        'id': 'id'
    }
    sort_column = allowed_sort.get(sort_by, 'title')
    sort_order = 'DESC' if order.lower() == 'desc' else 'ASC'

    # Count total matching books
    count_query = f"SELECT COUNT(*) as total FROM books {where_clause}"
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()['total']

    # Pagination calculation
    page = max(1, int(page))
    per_page = max(1, int(per_page))
    total_pages = max(1, math.ceil(total_count / per_page))
    if page > total_pages and total_count > 0:
        page = total_pages
    offset = (page - 1) * per_page

    # Fetch rows
    data_query = f"""
        SELECT *, (total_copies - available_copies) AS issued_copies
        FROM books
        {where_clause}
        ORDER BY {sort_column} {sort_order}
        LIMIT ? OFFSET ?
    """
    fetch_params = list(params) + [per_page, offset]
    cursor.execute(data_query, fetch_params)
    rows = cursor.fetchall()
    conn.close()

    return {
        'books': [dict(r) for r in rows],
        'total': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages
    }

def get_book_by_id(book_id: int, db_path=None):
    """Retrieve full book details by ID."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT *, (total_copies - available_copies) AS issued_copies
        FROM books
        WHERE id = ?
    """, (book_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_book_by_isbn(isbn: str, db_path=None):
    """Retrieve book by ISBN."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE isbn = ?", (isbn.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def validate_book_payload(data, is_update=False, current_book=None):
    """Validate book fields for creation or update."""
    errors = []
    
    title = data.get('title', '').strip() if data.get('title') else ''
    author = data.get('author', '').strip() if data.get('author') else ''
    isbn = data.get('isbn', '').strip() if data.get('isbn') else ''
    category = data.get('category', '').strip() if data.get('category') else ''
    publisher = data.get('publisher', '').strip() if data.get('publisher') else ''
    
    if not title:
        errors.append("Book title is required.")
    if not author:
        errors.append("Author name is required.")
    if not isbn:
        errors.append("ISBN is required.")
    if not category:
        errors.append("Category is required.")
    if not publisher:
        errors.append("Publisher is required.")

    # Validate year
    current_year = datetime.now().year
    try:
        year = int(data.get('publication_year', 0))
        if year < 1000 or year > current_year + 1:
            errors.append(f"Publication year must be between 1000 and {current_year + 1}.")
    except (ValueError, TypeError):
        errors.append("Invalid publication year.")

    # Validate copies
    try:
        total_copies = int(data.get('total_copies', 1))
        if total_copies < 0:
            errors.append("Total copies cannot be negative.")
    except (ValueError, TypeError):
        errors.append("Total copies must be a valid non-negative integer.")
        total_copies = 0

    available_copies = data.get('available_copies')
    if available_copies is not None and str(available_copies).strip() != '':
        try:
            available_copies = int(available_copies)
            if available_copies < 0:
                errors.append("Available copies cannot be negative.")
            elif available_copies > total_copies:
                errors.append("Available copies cannot exceed total copies.")
        except (ValueError, TypeError):
            errors.append("Available copies must be a valid integer.")
    else:
        # Default available copies
        if is_update and current_book:
            currently_issued = current_book['total_copies'] - current_book['available_copies']
            if total_copies < currently_issued:
                errors.append(f"Total copies cannot be less than currently issued copies ({currently_issued}).")
            available_copies = total_copies - currently_issued
        else:
            available_copies = total_copies

    return errors, {
        'title': title,
        'author': author,
        'isbn': isbn,
        'category': category,
        'publisher': publisher,
        'publication_year': int(data.get('publication_year', current_year)),
        'total_copies': total_copies,
        'available_copies': available_copies,
        'description': data.get('description', '').strip(),
        'cover_url': data.get('cover_url', '').strip()
    }

def add_book(data, db_path=None):
    """Add a new book with validation and uniqueness checks."""
    errors, clean_data = validate_book_payload(data)
    if errors:
        raise ValueError("; ".join(errors))

    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Check duplicate ISBN
    cursor.execute("SELECT id FROM books WHERE isbn = ?", (clean_data['isbn'],))
    if cursor.fetchone():
        conn.close()
        raise ValueError(f"A book with ISBN '{clean_data['isbn']}' already exists.")

    try:
        cursor.execute("""
            INSERT INTO books (isbn, title, author, category, publisher, publication_year,
                               total_copies, available_copies, description, cover_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            clean_data['isbn'],
            clean_data['title'],
            clean_data['author'],
            clean_data['category'],
            clean_data['publisher'],
            clean_data['publication_year'],
            clean_data['total_copies'],
            clean_data['available_copies'],
            clean_data['description'],
            clean_data['cover_url']
        ))
        conn.commit()
        book_id = cursor.lastrowid
        return book_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def update_book(book_id: int, data, db_path=None):
    """Update an existing book with consistency checks."""
    current_book = get_book_by_id(book_id, db_path=db_path)
    if not current_book:
        raise ValueError(f"Book with ID {book_id} does not exist.")

    errors, clean_data = validate_book_payload(data, is_update=True, current_book=current_book)
    if errors:
        raise ValueError("; ".join(errors))

    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Check duplicate ISBN on other books
    cursor.execute("SELECT id FROM books WHERE isbn = ? AND id != ?", (clean_data['isbn'], book_id))
    if cursor.fetchone():
        conn.close()
        raise ValueError(f"Another book with ISBN '{clean_data['isbn']}' already exists.")

    try:
        cursor.execute("""
            UPDATE books
            SET isbn = ?, title = ?, author = ?, category = ?, publisher = ?,
                publication_year = ?, total_copies = ?, available_copies = ?,
                description = ?, cover_url = ?
            WHERE id = ?
        """, (
            clean_data['isbn'],
            clean_data['title'],
            clean_data['author'],
            clean_data['category'],
            clean_data['publisher'],
            clean_data['publication_year'],
            clean_data['total_copies'],
            clean_data['available_copies'],
            clean_data['description'],
            clean_data['cover_url'],
            book_id
        ))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def delete_book(book_id: int, db_path=None):
    """
    Safely delete a book.
    Ensures that books with active unreturned borrowings cannot be deleted.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Check for active borrowings
    cursor.execute("""
        SELECT COUNT(*) as active_count
        FROM borrowings
        WHERE book_id = ? AND status IN ('Issued', 'Overdue')
    """, (book_id,))
    active_count = cursor.fetchone()['active_count']

    if active_count > 0:
        conn.close()
        raise ValueError(f"Cannot delete book: {active_count} copy/copies are currently issued and not returned.")

    try:
        # If there are past returned borrowings, clean them up or preserve integrity
        cursor.execute("DELETE FROM borrowings WHERE book_id = ? AND status = 'Returned'", (book_id,))
        cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
