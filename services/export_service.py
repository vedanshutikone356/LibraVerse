import os
import io
from datetime import datetime
import pandas as pd
from database import get_connection

def get_books_dataframe(db_path=None):
    """Retrieve book inventory as a cleanly formatted Pandas DataFrame."""
    conn = get_connection(db_path)
    df = pd.read_sql_query("""
        SELECT id AS "Book ID",
               isbn AS "ISBN",
               title AS "Title",
               author AS "Author",
               category AS "Category",
               publisher AS "Publisher",
               publication_year AS "Year",
               total_copies AS "Total Copies",
               available_copies AS "Available Copies",
               (total_copies - available_copies) AS "Issued Copies",
               created_at AS "Date Added"
        FROM books
        ORDER BY id ASC
    """, conn)
    conn.close()
    return df

def get_members_dataframe(db_path=None):
    """Retrieve members with loan summaries as a Pandas DataFrame."""
    conn = get_connection(db_path)
    df = pd.read_sql_query("""
        SELECT m.id AS "Member ID",
               m.full_name AS "Full Name",
               m.email AS "Email Address",
               m.phone AS "Phone",
               m.membership_status AS "Status",
               m.registration_date AS "Joined Date",
               COUNT(CASE WHEN b.status IN ('Issued', 'Overdue') THEN 1 END) AS "Active Loans",
               COUNT(b.id) AS "Total Borrowings"
        FROM members m
        LEFT JOIN borrowings b ON m.id = b.member_id
        GROUP BY m.id
        ORDER BY m.id ASC
    """, conn)
    conn.close()
    return df

def get_borrowings_dataframe(db_path=None):
    """Retrieve full borrowing transactions as a Pandas DataFrame."""
    conn = get_connection(db_path)
    df = pd.read_sql_query("""
        SELECT b.id AS "Transaction ID",
               bk.title AS "Book Title",
               bk.isbn AS "ISBN",
               m.full_name AS "Member Name",
               m.email AS "Member Email",
               b.issue_date AS "Issue Date",
               b.due_date AS "Due Date",
               COALESCE(b.return_date, 'Not Returned') AS "Return Date",
               b.status AS "Status",
               b.overdue_days AS "Overdue Days",
               b.fine_amount AS "Fine ($)"
        FROM borrowings b
        JOIN books bk ON b.book_id = bk.id
        JOIN members m ON b.member_id = m.id
        ORDER BY b.id DESC
    """, conn)
    conn.close()
    return df

def export_to_csv(df: pd.DataFrame) -> bytes:
    """Export a Pandas DataFrame to UTF-8 CSV bytes."""
    return df.to_csv(index=False).encode('utf-8')

def export_to_excel(df_dict: dict) -> bytes:
    """
    Export one or more DataFrames into an Excel workbook (.xlsx) using openpyxl engine.
    df_dict is a mapping of sheet_name -> DataFrame.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in df_dict.items():
            # Excel sheet name max length is 31
            safe_sheet = sheet_name[:31]
            df.to_excel(writer, sheet_name=safe_sheet, index=False)
    output.seek(0)
    return output.getvalue()

def generate_comprehensive_excel(db_path=None) -> bytes:
    """
    Generate a full-featured multi-sheet Excel report combining:
    - Inventory
    - Members
    - Borrowing Transactions
    - Category Summary
    """
    books_df = get_books_dataframe(db_path)
    members_df = get_members_dataframe(db_path)
    borrowings_df = get_borrowings_dataframe(db_path)

    # Category summary sheet via Pandas
    conn = get_connection(db_path)
    cat_df = pd.read_sql_query("""
        SELECT category AS "Category",
               COUNT(id) AS "Titles Count",
               SUM(total_copies) AS "Total Physical Copies",
               SUM(available_copies) AS "Available Copies",
               SUM(total_copies - available_copies) AS "In Circulation"
        FROM books
        GROUP BY category
        ORDER BY SUM(total_copies) DESC
    """, conn)
    conn.close()

    sheet_map = {
        'Book Inventory': books_df,
        'Member Directory': members_df,
        'Transaction History': borrowings_df,
        'Category Analytics': cat_df
    }

    return export_to_excel(sheet_map)
