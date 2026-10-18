import pandas as pd
import numpy as np
from datetime import date
from database import get_connection

def get_dashboard_metrics(db_path=None):
    """
    Calculate high-level library KPIs from database records.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Books KPIs
    cursor.execute("""
        SELECT COUNT(id) AS total_titles,
               COALESCE(SUM(total_copies), 0) AS total_copies,
               COALESCE(SUM(available_copies), 0) AS available_copies
        FROM books
    """)
    books_summary = cursor.fetchone()
    total_titles = books_summary['total_titles']
    total_copies = books_summary['total_copies']
    available_copies = books_summary['available_copies']
    issued_copies = max(0, total_copies - available_copies)

    # Members KPIs
    cursor.execute("SELECT COUNT(id) AS total_members, COUNT(CASE WHEN membership_status = 'Active' THEN 1 END) AS active_members FROM members")
    members_summary = cursor.fetchone()
    total_members = members_summary['total_members']
    active_members = members_summary['active_members']

    # Borrowings KPIs
    cursor.execute("""
        SELECT COUNT(id) AS total_transactions,
               COUNT(CASE WHEN status = 'Issued' THEN 1 END) AS active_issued,
               COUNT(CASE WHEN status = 'Overdue' THEN 1 END) AS overdue_count,
               COUNT(CASE WHEN status = 'Returned' THEN 1 END) AS returned_count,
               COALESCE(SUM(fine_amount), 0.0) AS total_fines
        FROM borrowings
    """)
    borrowings_summary = cursor.fetchone()
    total_transactions = borrowings_summary['total_transactions']
    active_issued = borrowings_summary['active_issued']
    overdue_count = borrowings_summary['overdue_count']
    returned_count = borrowings_summary['returned_count']
    total_fines = borrowings_summary['total_fines']

    conn.close()

    circulation_rate = round((issued_copies / total_copies * 100), 1) if total_copies > 0 else 0.0

    return {
        'total_titles': total_titles,
        'total_copies': total_copies,
        'available_copies': available_copies,
        'issued_copies': issued_copies,
        'circulation_rate': circulation_rate,
        'total_members': total_members,
        'active_members': active_members,
        'active_issued': active_issued,
        'overdue_count': overdue_count,
        'returned_count': returned_count,
        'total_active_loans': active_issued + overdue_count,
        'total_transactions': total_transactions,
        'total_fines': round(total_fines, 2)
    }

def get_category_analytics(db_path=None):
    """
    Use Pandas to aggregate book inventory, distribution, and circulation rates per category.
    """
    conn = get_connection(db_path)
    books_df = pd.read_sql_query("SELECT id, title, category, total_copies, available_copies FROM books", conn)
    borrowings_df = pd.read_sql_query("SELECT b.id, bk.category FROM borrowings b JOIN books bk ON b.book_id = bk.id", conn)
    conn.close()

    if books_df.empty:
        return {
            'labels': [],
            'title_counts': [],
            'total_copies': [],
            'available_copies': [],
            'issued_copies': [],
            'borrow_counts': [],
            'table_data': []
        }

    books_df['issued_copies'] = books_df['total_copies'] - books_df['available_copies']

    # Group by category using Pandas
    cat_summary = books_df.groupby('category').agg(
        title_count=('id', 'count'),
        total_copies=('total_copies', 'sum'),
        available_copies=('available_copies', 'sum'),
        issued_copies=('issued_copies', 'sum')
    ).reset_index()

    # Calculate borrow counts per category
    if not borrowings_df.empty:
        borrow_cat = borrowings_df.groupby('category').size().reset_index(name='borrow_count')
        merged = pd.merge(cat_summary, borrow_cat, on='category', how='left')
        merged['borrow_count'] = merged['borrow_count'].fillna(0).astype(int)
    else:
        merged = cat_summary
        merged['borrow_count'] = 0

    merged['utilization_rate'] = np.where(
        merged['total_copies'] > 0,
        np.round((merged['issued_copies'] / merged['total_copies']) * 100, 1),
        0.0
    )

    merged = merged.sort_values(by='total_copies', ascending=False)

    return {
        'labels': merged['category'].tolist(),
        'title_counts': merged['title_count'].astype(int).tolist(),
        'total_copies': merged['total_copies'].astype(int).tolist(),
        'available_copies': merged['available_copies'].astype(int).tolist(),
        'issued_copies': merged['issued_copies'].astype(int).tolist(),
        'borrow_counts': merged['borrow_count'].astype(int).tolist(),
        'table_data': merged.to_dict(orient='records')
    }

def get_top_borrowed_books(limit=8, db_path=None):
    """
    Use Pandas to aggregate transaction frequency and rank the most popular titles.
    """
    conn = get_connection(db_path)
    query = """
        SELECT b.id AS borrowing_id, bk.id AS book_id, bk.title, bk.author, bk.category, bk.total_copies, bk.available_copies
        FROM borrowings b
        JOIN books bk ON b.book_id = bk.id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        return {'labels': [], 'counts': [], 'records': []}

    total_borrows = len(df)
    grouped = df.groupby(['book_id', 'title', 'author', 'category']).size().reset_index(name='borrow_count')
    grouped['share_percentage'] = np.round((grouped['borrow_count'] / total_borrows) * 100, 1)
    sorted_df = grouped.sort_values(by='borrow_count', ascending=False).head(limit)

    return {
        'labels': sorted_df['title'].tolist(),
        'counts': sorted_df['borrow_count'].astype(int).tolist(),
        'records': sorted_df.to_dict(orient='records')
    }

def get_monthly_borrowing_trends(db_path=None):
    """
    Use Pandas for date time-series grouping and NumPy for statistical dispersion and trends.
    """
    conn = get_connection(db_path)
    df = pd.read_sql_query("SELECT id, issue_date, status FROM borrowings", conn)
    conn.close()

    if df.empty:
        return {
            'labels': [],
            'counts': [],
            'mean_monthly': 0.0,
            'std_monthly': 0.0,
            'median_monthly': 0.0,
            'max_monthly': 0,
            'min_monthly': 0,
            'trend_slope': 0.0
        }

    df['issue_date'] = pd.to_datetime(df['issue_date'], errors='coerce')
    df = df.dropna(subset=['issue_date'])
    df['year_month'] = df['issue_date'].dt.to_period('M').astype(str)

    monthly_summary = df.groupby('year_month').size().reset_index(name='count')
    monthly_summary = monthly_summary.sort_values(by='year_month')

    labels = monthly_summary['year_month'].tolist()
    counts = monthly_summary['count'].to_numpy()

    # Meaningful NumPy numerical calculations
    mean_monthly = float(np.mean(counts)) if len(counts) > 0 else 0.0
    std_monthly = float(np.std(counts)) if len(counts) > 0 else 0.0
    median_monthly = float(np.median(counts)) if len(counts) > 0 else 0.0
    max_monthly = int(np.max(counts)) if len(counts) > 0 else 0
    min_monthly = int(np.min(counts)) if len(counts) > 0 else 0

    # Trend calculation using NumPy linear fit
    if len(counts) >= 2:
        x = np.arange(len(counts))
        slope, _ = np.polyfit(x, counts, 1)
        trend_slope = float(round(slope, 2))
    else:
        trend_slope = 0.0

    return {
        'labels': labels,
        'counts': counts.tolist(),
        'mean_monthly': round(mean_monthly, 1),
        'std_monthly': round(std_monthly, 1),
        'median_monthly': round(median_monthly, 1),
        'max_monthly': max_monthly,
        'min_monthly': min_monthly,
        'trend_slope': trend_slope
    }

def get_duration_and_overdue_stats(db_path=None):
    """
    Use NumPy to compute loan duration statistics and overdue ratios.
    """
    conn = get_connection(db_path)
    df = pd.read_sql_query("SELECT id, issue_date, due_date, return_date, status, overdue_days FROM borrowings", conn)
    conn.close()

    if df.empty:
        return {
            'avg_duration': 0.0,
            'median_duration': 0.0,
            'p90_duration': 0.0,
            'overdue_rate': 0.0,
            'distribution_labels': ['0-7 Days', '8-14 Days', '15-21 Days', '22-30 Days', '30+ Days'],
            'distribution_counts': [0, 0, 0, 0, 0]
        }

    # Analyze completed returns
    returned_df = df[df['status'] == 'Returned'].copy()
    if not returned_df.empty:
        returned_df['issue_dt'] = pd.to_datetime(returned_df['issue_date'])
        returned_df['return_dt'] = pd.to_datetime(returned_df['return_date'])
        durations = (returned_df['return_dt'] - returned_df['issue_dt']).dt.days.to_numpy()

        avg_duration = float(np.mean(durations)) if len(durations) > 0 else 0.0
        median_duration = float(np.median(durations)) if len(durations) > 0 else 0.0
        p90_duration = float(np.percentile(durations, 90)) if len(durations) > 0 else 0.0

        # Histogram bins using NumPy
        bins = [0, 7, 14, 21, 30, 9999]
        hist_counts, _ = np.histogram(durations, bins=bins)
        distribution_counts = hist_counts.tolist()
    else:
        avg_duration = 0.0
        median_duration = 0.0
        p90_duration = 0.0
        distribution_counts = [0, 0, 0, 0, 0]

    # Overall overdue rate
    total_borrows = len(df)
    overdue_count = len(df[df['status'] == 'Overdue'])
    overdue_rate = round((overdue_count / total_borrows * 100), 1) if total_borrows > 0 else 0.0

    return {
        'avg_duration': round(avg_duration, 1),
        'median_duration': round(median_duration, 1),
        'p90_duration': round(p90_duration, 1),
        'overdue_rate': overdue_rate,
        'distribution_labels': ['0-7 Days', '8-14 Days', '15-21 Days', '22-30 Days', '30+ Days'],
        'distribution_counts': distribution_counts
    }
