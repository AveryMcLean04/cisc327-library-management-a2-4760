import pytest
from library_service import (
    calculate_late_fee_for_book
)

def test_late_fee_no_overdue():
    """Test calculating late fee for a book returned on time (0 days overdue)."""
    result = calculate_late_fee_for_book("999999", 1)

    assert result["fee_amount"] == 0.00
    assert result["days_overdue"] == 0
    assert "no active borrow found" in result["status"].lower()

def test_late_fee_overdue_book():
    """Test calculating late fee for an overdue book should return positive fee."""
    result = calculate_late_fee_for_book("999999", 12)

    assert result["days_overdue"] > 0
    assert result["fee_amount"] > 0
    assert "ok" in result["status"].lower()

def test_late_fee_book_not_returned():
    """Test calculating late fee for a book that has not been returned."""
    result = calculate_late_fee_for_book("123456", 4)

    assert result["days_overdue"] > 0
    assert result["fee_amount"] > 0
    assert "ok" in result["status"].lower()

def test_late_fee_invalid_patron_id():
    """Test calculating late fee with an invalid patron ID."""
    result = calculate_late_fee_for_book("12", 1)

    assert result["fee_amount"] == 0.00
    assert "invalid patron id" in result["status"].lower()
