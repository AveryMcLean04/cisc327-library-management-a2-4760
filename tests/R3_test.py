import pytest
from database import init_database

@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """Automatically initialize a clean database before each test."""
    init_database()
from services.library_service import (
    add_book_to_catalog,
    borrow_book_by_patron,
    get_book_by_isbn,
    get_all_books
)

def test_borrow_book_valid_input():
    """Test borrowing a book with valid input."""
    # Add a book so it exists
    add_book_to_catalog("Test Book", "Test Author", "1111111111111", 3)
    book = get_book_by_isbn("1111111111111")

    success, message = borrow_book_by_patron("999999", book['id'])

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
    # Add a book with 1 copy and borrow it to make it unavailable
    add_book_to_catalog("Unavailable Book", "Author", "2222222222222", 1)
    book = get_book_by_isbn("2222222222222")

    # Borrow once to make it unavailable
    borrow_book_by_patron("111111", book['id'])

    # Try borrowing again
    success, message = borrow_book_by_patron("999999", book['id'])

    assert success == False
    assert "not available" in message.lower()


def test_borrow_book_limit_reached():
    """Test borrowing a 6th book after already borrowing 5."""
    patron_id = "777777"

    # Add 6 books
    for i in range(6):
        isbn = f"333333333333{i}"
        add_book_to_catalog(f"Book {i}", "Author", isbn, 2)

    books = get_all_books()

    # Patron borrows first 5 books
    for i in range(5):
        borrow_book_by_patron(patron_id, books[i]['id'])

    # Try to borrow 6th book
    success, message = borrow_book_by_patron(patron_id, books[5]['id'])

    assert success == False
    assert "maximum borrowing limit" in message.lower()
