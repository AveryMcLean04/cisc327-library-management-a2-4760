import pytest
from library_service import (
    return_book_by_patron
)

def test_return_book_valid_input():
    """Test returning a book with valid input."""
    success, message = return_book_by_patron("999999", 1)

    assert success == True
    assert "returned" in message.lower()

def test_return_book_invalid_patron_id():
    """Test returning a book with an invalid patron ID (too short)."""
    success, message = return_book_by_patron("123", 1)

    assert success == False
    assert "invalid patron id" in message.lower()

def test_return_book_invalid_book_id():
    """Test returning a book with a non-existent book ID."""
    success, message = return_book_by_patron("999999", 999)

    assert success == False
    assert "book not found" in message.lower()

def test_return_book_not_borrowed():
    """Test returning a book that the patron has not borrowed."""
    success, message = return_book_by_patron("999999", 2)

    assert success == False
    assert "no active borrow record found for this patron and book." in message.lower()
