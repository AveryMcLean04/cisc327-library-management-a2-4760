import pytest
from library_service import (
    add_book_to_catalog,
    borrow_book_by_patron,
    return_book_by_patron,
    get_book_by_isbn
)

def test_return_book_valid_input():
    """Test returning a book with valid input."""
    # Add and borrow a book
    add_book_to_catalog("Return Test Book", "Author", "4444444444444", 3)
    book = get_book_by_isbn("4444444444444")
    borrow_book_by_patron("999999", book['id'])

    # Now return it
    success, message = return_book_by_patron("999999", book['id'])

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
    # Add a book but do not borrow it
    add_book_to_catalog("Not Borrowed Book", "Author", "5555555555555", 1)
    book = get_book_by_isbn("5555555555555")

    success, message = return_book_by_patron("999999", book['id'])

    assert success == False
    assert "no active borrow record found for this patron and book." in message.lower()
