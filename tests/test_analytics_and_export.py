import pytest
import pandas as pd
import numpy as np
from services.analytics_service import (
    get_dashboard_metrics, get_category_analytics,
    get_top_borrowed_books, get_monthly_borrowing_trends,
    get_duration_and_overdue_stats
)
from services.export_service import (
    get_books_dataframe, get_members_dataframe, get_borrowings_dataframe,
    export_to_csv, export_to_excel, generate_comprehensive_excel
)

def test_pandas_dataframes(db_path):
    """Ensure database records convert cleanly into Pandas DataFrames."""
    books_df = get_books_dataframe(db_path)
    assert isinstance(books_df, pd.DataFrame)
    assert 'Book ID' in books_df.columns
    assert 'Available Copies' in books_df.columns

    members_df = get_members_dataframe(db_path)
    assert isinstance(members_df, pd.DataFrame)
    assert 'Member ID' in members_df.columns
    assert 'Status' in members_df.columns

    borrowings_df = get_borrowings_dataframe(db_path)
    assert isinstance(borrowings_df, pd.DataFrame)
    assert 'Transaction ID' in borrowings_df.columns

def test_numpy_statistics_computations(db_path):
    """Test NumPy-based numerical and statistical aggregations."""
    trends = get_monthly_borrowing_trends(db_path)
    assert 'mean_monthly' in trends
    assert isinstance(trends['mean_monthly'], float)
    assert 'std_monthly' in trends
    assert 'median_monthly' in trends

    durations = get_duration_and_overdue_stats(db_path)
    assert 'avg_duration' in durations
    assert 'median_duration' in durations
    assert 'p90_duration' in durations
    assert 'overdue_rate' in durations

def test_csv_and_excel_exports(db_path):
    """Test generating binary CSV and Excel files."""
    books_df = get_books_dataframe(db_path)
    csv_bytes = export_to_csv(books_df)
    assert isinstance(csv_bytes, bytes)
    assert len(csv_bytes) > 0
    assert b"Book ID" in csv_bytes

    # Single sheet Excel
    excel_bytes = export_to_excel({'Inventory': books_df})
    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 500  # Valid Excel header

    # Multi-sheet comprehensive Excel
    comprehensive_bytes = generate_comprehensive_excel(db_path)
    assert isinstance(comprehensive_bytes, bytes)
    assert len(comprehensive_bytes) > 1000
