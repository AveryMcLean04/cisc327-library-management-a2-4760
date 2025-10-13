import pytest
from library_service import (
    search_books_in_catalog
)

def test_search_title_partial():
    """Title search should support partial, case-insensitive matching."""
    results = search_books_in_catalog("harry", "title")
    assert len(results) > 0
    assert any("harry potter" in r["title"].lower() for r in results)

def test_search_author_partial():
    """Author search should support partial, case-insensitive matching."""
    results = search_books_in_catalog("scott", "author")
    assert len(results) > 0
    assert any("f. scott fitzgerald" in r["author"].lower() for r in results)

def test_search_isbn_match():
    """ISBN search must be exact match."""
    results = search_books_in_catalog("9780451524935", "isbn") 
    assert len(results) == 1
    assert results[0]["isbn"] == "9780451524935"
    assert "1984" in results[0]["title"]

def test_search_isbn_partial_should_not_match():
    """Partial ISBN must not return results (should show error message instead of silent empty list)."""
    results = search_books_in_catalog("978045152", "isbn")

    assert results == []
    assert "[]" in str(results).lower()
