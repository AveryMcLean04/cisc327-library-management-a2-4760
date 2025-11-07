import pytest
from datetime import datetime, timedelta
from services.library_service import (
    add_book_to_catalog,
    borrow_book_by_patron,
    calculate_late_fee_for_book,
    get_book_by_isbn
)
from database import get_db_connection

def test_late_fee_no_overdue():
    """Test calculating late fee for a book returned on time (0 days overdue)."""
    # Add and borrow a book
    add_book_to_catalog("On Time Book", "Author", "6666666666661", 1)
    book = get_book_by_isbn("6666666666661")
    borrow_book_by_patron("999999", book['id'])

    # Calculate fee immediately (0 days overdue)
    result = calculate_late_fee_for_book("999999", book['id'])

    assert result["fee_amount"] == 0.00
    assert result["days_overdue"] == 0
    assert "no active borrow found" in result["status"].lower()


def test_late_fee_overdue_book():
    """Test calculating late fee for an overdue book should return positive fee."""
    # Add a book
    add_book_to_catalog("Overdue Book", "Author", "6666666666662", 1)
    book = get_book_by_isbn("6666666666662")

    # Manually insert overdue borrow (borrowed 20 days ago)
    conn = get_db_connection()
    borrow_date = datetime.now() - timedelta(days=20)
    due_date = borrow_date + timedelta(days=14)
    conn.execute(
        'INSERT INTO borrow_records (patron_id, book_id, borrow_date, due_date) VALUES (?, ?, ?, ?)',
        ("999999", book['id'], borrow_date.isoformat(), due_date.isoformat())
    )
    conn.execute('UPDATE books SET available_copies = 0 WHERE id = ?', (book['id'],))
    conn.commit()
    conn.close()

    result = calculate_late_fee_for_book("999999", book['id'])

    assert result["days_overdue"] > 0
    assert result["fee_amount"] > 0
    assert "ok" in result["status"].lower()


def test_late_fee_book_not_returned():
    """Test calculating late fee for a book that has not been returned."""
    # Add a book and borrow it
    add_book_to_catalog("Not Returned Book", "Author", "6666666666663", 1)
    book = get_book_by_isbn("6666666666663")

    # Manually insert borrow record without return
    conn = get_db_connection()
    borrow_date = datetime.now() - timedelta(days=16)
    due_date = borrow_date + timedelta(days=14)
    conn.execute(
        'INSERT INTO borrow_records (patron_id, book_id, borrow_date, due_date) VALUES (?, ?, ?, ?)',
        ("123456", book['id'], borrow_date.isoformat(), due_date.isoformat())
    )
    conn.commit()
    conn.close()

    result = calculate_late_fee_for_book("123456", book['id'])

    assert result["days_overdue"] > 0
    assert result["fee_amount"] > 0
    assert "ok" in result["status"].lower()


def test_late_fee_invalid_patron_id():
    """Test calculating late fee with an invalid patron ID."""
    result = calculate_late_fee_for_book("12", 1)

    assert result["fee_amount"] == 0.00
    assert "invalid patron id" in result["status"].lower()
