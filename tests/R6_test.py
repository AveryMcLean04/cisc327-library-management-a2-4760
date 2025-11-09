import pytest

from services.library_service import (
    add_book_to_catalog,
    search_books_in_catalog,
    get_book_by_isbn
)

def test_search_title_partial():
    """Title search should support partial, case-insensitive matching."""
    # Add test books
    add_book_to_catalog("Harry Potter and the Sorcerer's Stone", "J.K. Rowling", "1111111111111", 3)
    add_book_to_catalog("Harry Potter and the Chamber of Secrets", "J.K. Rowling", "1111111111112", 3)
    
    results = search_books_in_catalog("harry", "title")
    assert len(results) > 0
    assert any("harry potter" in r["title"].lower() for r in results)


def test_search_author_partial():
    """Author search should support partial, case-insensitive matching."""
    # Add test books
    add_book_to_catalog("The Great Gatsby", "F. Scott Fitzgerald", "2222222222221", 3)
    add_book_to_catalog("Tender Is the Night", "F. Scott Fitzgerald", "2222222222222", 3)
    
    results = search_books_in_catalog("scott", "author")
    assert len(results) > 0
    assert any("f. scott fitzgerald" in r["author"].lower() for r in results)


def test_search_isbn_match():
    """ISBN search must be exact match."""
    # Add test book
    add_book_to_catalog("1984", "George Orwell", "9780451524935", 1)
    
    results = search_books_in_catalog("9780451524935", "isbn") 
    assert len(results) == 1
    assert results[0]["isbn"] == "9780451524935"
    assert "1984" in results[0]["title"]


def test_search_isbn_partial_should_not_match():
    """Partial ISBN must not return results (should be empty list)."""
    # Ensure the book exists in DB
    add_book_to_catalog("1984", "George Orwell", "9780451524935", 1)
    
    results = search_books_in_catalog("978045152", "isbn")

    assert results == []
    assert "[]" in str(results).lower()
