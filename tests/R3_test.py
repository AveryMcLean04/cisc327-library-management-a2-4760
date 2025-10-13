import pytest
from library_service import (
    borrow_book_by_patron
)

def test_borrow_book_valid_input():
    """Test borrowing a book with valid input."""
    success, message = borrow_book_by_patron("999999", 1)

    assert success == True
    assert "successfully borrowed" in message.lower()
    assert "due date" in message.lower()

def test_borrow_book_invalid_patron_id():
    """Test borrowing a book with an invalid patron ID (not 6 digits)."""
    success, message = borrow_book_by_patron("123", 1)

    assert success == False
    assert "invalid patron id" in message.lower()

def test_borrow_book_unavailable_book():
    """Test borrowing a book that has no available copies (book id 6)."""
    success, message = borrow_book_by_patron("999999", 6)

    assert success == False
    assert "not available" in message.lower()

def test_borrow_book_limit_reached():
    """Test borrowing a 6th book after already borrowing 5."""
    # Patron "777777" was already used in the app to borrow 5 books
    success, message = borrow_book_by_patron("777777", 5)

    # Requirement says this should fail
    assert success == False
    assert "maximum borrowing limit" in message.lower()
