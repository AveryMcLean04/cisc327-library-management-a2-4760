import pytest
from services.library_service import (
    add_book_to_catalog
)

def test_add_book_valid_input():
    """Test adding a book with valid input."""
    success, message = add_book_to_catalog("Test Book2", "Test Author", "2234567890108", 20)
    
    assert success == True
    assert "successfully added" in message.lower()

def test_add_book_no_title():
    """Test adding a book with no title."""
    success, message = add_book_to_catalog("", "Test Author", "3234567890123", 5)
    
    assert success == False
    assert "title is required." in message.lower()

def test_add_book_author_too_long():
    """Test adding a book where author name exceeds 100 characters."""
    long_author = "A" * 101
    success, message = add_book_to_catalog("Valid Title", long_author, "1234567890123", 3)

    assert success == False
    assert "author must be less than 100 characters" in message.lower()

def test_add_book_invalid_isbn_length():
    """Test adding a book with ISBN shorter than 13 digits."""
    success, message = add_book_to_catalog("Valid Title", "Valid Author", "12345", 2)

    assert success == False
    assert "isbn must be exactly 13 digits" in message.lower()

def test_add_book_invalid_isbn_non_digits():
    """Test adding a book with letters in ISBN (should fail but currently passes)."""
    success, message = add_book_to_catalog("Buggy Book", "Buggy Author", "12345678901AB", 5)

    # should fail but doesn't
    assert success == False
    assert "isbn must be exactly 13 digits" in message.lower()

