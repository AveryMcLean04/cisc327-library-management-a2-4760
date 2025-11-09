import pytest

from services.library_service import get_patron_status_report

def test_patron_status_valid_id():
    """Status report should include borrowed books and fees for a valid patron."""
    report = get_patron_status_report("123456")
    assert "currently_borrowed" in report
    assert isinstance(report["currently_borrowed"], list)

def test_patron_status_invalid_id():
    """Invalid patron ID should return a status indicating an error."""
    report = get_patron_status_report("12")
    assert "status" in report
    assert "invalid patron id" in report["status"].lower()

def test_patron_status_no_borrowed_books():
    """A valid patron with no borrowed books should return an empty list."""
    report = get_patron_status_report("654321")
    assert "currently_borrowed" in report
    assert report["currently_borrowed"] == []

def test_patron_status_includes_fees():
    """Status report should include late fee information when applicable."""
    report = get_patron_status_report("123456")
    assert "total_late_fees" in report
    assert isinstance(report["total_late_fees"], (float, int))
