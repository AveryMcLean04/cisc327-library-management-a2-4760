"""
Comprehensive Test Suite for Library Management System
Tests all 7 functional requirements (R1-R7) with 4-5 test cases each
Generated for CISC 327 Assignment 2

IMPORTANT: This test suite is designed to work with a FRESH database.
Delete library.db before running tests for consistent, repeatable results.

RUN WITH: pytest test_library_service.py -v
"""

import pytest
from datetime import datetime, timedelta
from library_service import (
    add_book_to_catalog,
    borrow_book_by_patron,
    return_book_by_patron,
    calculate_late_fee_for_book,
    search_books_in_catalog,
    get_patron_status_report
)
from database import (
    init_database,
    get_db_connection,
    get_book_by_isbn,
    insert_book,
    insert_borrow_record,
    get_all_books
)


# ============================================================================
# FIXTURES AND SETUP
# ============================================================================

@pytest.fixture(scope="function")
def setup_test_db():
    """
    Setup fixture that initializes the database before each test.
    This ensures a clean state for each test.
    """
    init_database()
    yield
    # Cleanup after test if needed


# ============================================================================
# R1: ADD BOOK TO CATALOG - Testing add_book_to_catalog()
# Tests input validation, duplicate detection, and successful insertion
# ============================================================================

def test_r1_add_book_valid_input(setup_test_db):
    """R1.1: Test adding a book with all valid inputs."""
    success, message = add_book_to_catalog(
        "Clean Code", 
        "Robert C. Martin", 
        "9780132350884", 
        3
    )
    
    assert success == True
    assert "successfully added" in message.lower()
    
    # Verify book exists in database
    book = get_book_by_isbn("9780132350884")
    assert book is not None
    assert book['title'] == "Clean Code"
    assert book['available_copies'] == 3


def test_r1_add_book_empty_title(setup_test_db):
    """R1.2: Test that empty or whitespace-only title is rejected."""
    success, message = add_book_to_catalog("", "Author Name", "1234567890123", 5)
    assert success == False
    assert "title is required" in message.lower()
    
    # Test whitespace only
    success, message = add_book_to_catalog("   ", "Author Name", "1234567890124", 5)
    assert success == False
    assert "title is required" in message.lower()


def test_r1_add_book_title_too_long(setup_test_db):
    """R1.3: Test that title exceeding 200 characters is rejected."""
    long_title = "A" * 201  # 201 characters
    success, message = add_book_to_catalog(
        long_title, 
        "Author Name", 
        "1234567890125", 
        5
    )
    
    assert success == False
    assert "200 characters" in message.lower()


def test_r1_add_book_invalid_isbn_formats(setup_test_db):
    """R1.4: Test various invalid ISBN formats are rejected."""
    # ISBN too short
    success, message = add_book_to_catalog("Book Title", "Author", "12345", 5)
    assert success == False
    assert "13 digits" in message.lower()
    
    # ISBN too long
    success, message = add_book_to_catalog("Book Title", "Author", "12345678901234", 5)
    assert success == False
    assert "13 digits" in message.lower()
    
    # ISBN with letters
    success, message = add_book_to_catalog("Book Title", "Author", "123456789012A", 5)
    assert success == False
    assert "13 digits" in message.lower()


def test_r1_add_book_duplicate_isbn(setup_test_db):
    """R1.5: Test that duplicate ISBN is rejected."""
    # Add first book
    success1, _ = add_book_to_catalog(
        "First Book", 
        "First Author", 
        "9781234567890", 
        3
    )
    assert success1 == True
    
    # Try to add another book with same ISBN
    success2, message2 = add_book_to_catalog(
        "Different Book", 
        "Different Author", 
        "9781234567890", 
        5
    )
    assert success2 == False
    assert "already exists" in message2.lower()


def test_r1_add_book_invalid_copies(setup_test_db):
    """R1.6: Test that invalid total_copies values are rejected."""
    # Zero copies
    success, message = add_book_to_catalog(
        "Book Title", 
        "Author", 
        "9781234567891", 
        0
    )
    assert success == False
    assert "positive integer" in message.lower()
    
    # Negative copies
    success, message = add_book_to_catalog(
        "Book Title", 
        "Author", 
        "9781234567892", 
        -5
    )
    assert success == False
    assert "positive integer" in message.lower()


# ============================================================================
# R3: BOOK BORROWING - Testing borrow_book_by_patron()
# Tests patron validation, availability checks, and borrowing limits
# ============================================================================

def test_r3_borrow_book_valid(setup_test_db):
    """R3.1: Test successful book borrowing with valid inputs."""
    # Add a book to borrow
    add_book_to_catalog("Test Book", "Test Author", "1111111111111", 5)
    book = get_book_by_isbn("1111111111111")
    
    success, message = borrow_book_by_patron("999999", book['id'])
    
    assert success == True
    assert "successfully borrowed" in message.lower()
    assert "due date" in message.lower()


def test_r3_borrow_book_invalid_patron_id_formats(setup_test_db):
    """R3.2: Test that invalid patron ID formats are rejected."""
    # Too short
    success, message = borrow_book_by_patron("12345", 1)
    assert success == False
    assert "6 digits" in message.lower()
    
    # Too long
    success, message = borrow_book_by_patron("1234567", 1)
    assert success == False
    assert "6 digits" in message.lower()
    
    # Contains letters
    success, message = borrow_book_by_patron("12345A", 1)
    assert success == False
    assert "6 digits" in message.lower()


def test_r3_borrow_nonexistent_book(setup_test_db):
    """R3.3: Test borrowing a book that doesn't exist."""
    success, message = borrow_book_by_patron("123456", 99999)
    
    assert success == False
    assert "not found" in message.lower()


def test_r3_borrow_unavailable_book(setup_test_db):
    """R3.4: Test borrowing a book with 0 available copies."""
    # Create a book with 1 copy and make it unavailable
    add_book_to_catalog("Popular Book", "Famous Author", "2222222222222", 1)
    book = get_book_by_isbn("2222222222222")
    
    # First patron borrows it (making it unavailable)
    borrow_book_by_patron("111111", book['id'])
    
    # Second patron tries to borrow (should fail)
    success, message = borrow_book_by_patron("222222", book['id'])
    
    assert success == False
    assert "not available" in message.lower()


def test_r3_borrow_at_max_limit(setup_test_db):
    """R3.5: Test that patron with 5 borrowed books cannot borrow more."""
    # Create 6 books
    for i in range(6):
        isbn = f"300000000000{i}"
        add_book_to_catalog(f"Book {i}", "Author", isbn, 2)
    
    # Patron borrows 5 books (reaching the limit)
    books = get_all_books()
    for i in range(5):
        borrow_book_by_patron("555555", books[i]['id'])
    
    # Try to borrow a 6th book (should fail)
    success, message = borrow_book_by_patron("555555", books[5]['id'])
    
    assert success == False
    assert "maximum" in message.lower() or "limit" in message.lower()
    assert "5" in message


# ============================================================================
# R4: BOOK RETURN - Testing return_book_by_patron()
# Tests return validation, late fee calculation, and availability updates
# ============================================================================

def test_r4_return_book_valid_no_late_fee(setup_test_db):
    """R4.1: Test successful book return with no late fee."""
    # Add and borrow a book
    add_book_to_catalog("Return Test", "Author", "3333333333333", 2)
    book = get_book_by_isbn("3333333333333")
    borrow_success, borrow_msg = borrow_book_by_patron("777777", book['id'])
    
    # Verify borrow was successful first
    assert borrow_success == True, f"Borrow failed: {borrow_msg}"
    
    # Return immediately (within 14 days)
    success, message = return_book_by_patron("777777", book['id'])
    
    assert success == True, f"Return failed: {message}"
    assert "returned" in message.lower()
    assert "no late fee" in message.lower()


def test_r4_return_book_with_late_fee(setup_test_db):
    """R4.2: Test book return with late fee calculation."""
    # Create a book and manually insert an overdue borrow record
    add_book_to_catalog("Overdue Book", "Author", "4444444444444", 1)
    book = get_book_by_isbn("4444444444444")
    
    # Create overdue borrow (borrowed 20 days ago, due 6 days ago)
    conn = get_db_connection()
    borrow_date = datetime.now() - timedelta(days=20)
    due_date = borrow_date + timedelta(days=14)
    
    conn.execute(
        'INSERT INTO borrow_records (patron_id, book_id, borrow_date, due_date) VALUES (?, ?, ?, ?)',
        ("666666", book['id'], borrow_date.isoformat(), due_date.isoformat())
    )
    conn.execute('UPDATE books SET available_copies = 0 WHERE id = ?', (book['id'],))
    conn.commit()
    conn.close()
    
    success, message = return_book_by_patron("666666", book['id'])
    
    assert success == True
    assert "late" in message.lower()
    assert "fee" in message.lower()


def test_r4_return_book_invalid_patron_id(setup_test_db):
    """R4.3: Test return with invalid patron ID."""
    success, message = return_book_by_patron("12345", 1)  # Too short
    
    assert success == False
    assert "invalid patron id" in message.lower()


def test_r4_return_book_not_borrowed(setup_test_db):
    """R4.4: Test returning a book that wasn't borrowed by the patron."""
    # Create a book but don't borrow it
    add_book_to_catalog("Not Borrowed", "Author", "5555555555555", 1)
    book = get_book_by_isbn("5555555555555")
    
    # Try to return without borrowing
    success, message = return_book_by_patron("555555", book['id'])
    
    assert success == False
    assert "no active borrow" in message.lower() or "not found" in message.lower()


def test_r4_return_nonexistent_book(setup_test_db):
    """R4.5: Test returning a book that doesn't exist."""
    success, message = return_book_by_patron("123456", 99999)
    
    assert success == False
    assert "not found" in message.lower()


# ============================================================================
# R5: LATE FEE CALCULATION - Testing calculate_late_fee_for_book()
# Tests fee calculation logic with various overdue scenarios
# ============================================================================

def test_r5_calculate_no_late_fee_on_time(setup_test_db):
    """R5.1: Test late fee calculation for book returned on time."""
    # Create book and borrow it (not overdue)
    add_book_to_catalog("On Time Book", "Author", "6666666666661", 1)
    book = get_book_by_isbn("6666666666661")
    borrow_book_by_patron("111111", book['id'])
    
    # Calculate fee immediately (0 days overdue)
    result = calculate_late_fee_for_book("111111", book['id'])
    
    assert result['status'] == 'ok'
    assert result['fee_amount'] == 0.00
    assert result['days_overdue'] == 0


def test_r5_calculate_late_fee_first_week(setup_test_db):
    """R5.2: Test late fee for book 1-7 days overdue ($0.50/day)."""
    # Create overdue scenario: 3 days overdue
    add_book_to_catalog("Fee Test 1", "Author", "6666666666662", 1)
    book = get_book_by_isbn("6666666666662")
    
    conn = get_db_connection()
    borrow_date = datetime.now() - timedelta(days=17)  # 17 days ago = 3 days overdue
    due_date = borrow_date + timedelta(days=14)
    
    conn.execute(
        'INSERT INTO borrow_records (patron_id, book_id, borrow_date, due_date) VALUES (?, ?, ?, ?)',
        ("444444", book['id'], borrow_date.isoformat(), due_date.isoformat())
    )
    conn.commit()
    conn.close()
    
    result = calculate_late_fee_for_book("444444", book['id'])
    
    assert result['status'] == 'ok'
    assert result['days_overdue'] == 3
    assert result['fee_amount'] == 1.50  # 3 days * $0.50


def test_r5_calculate_late_fee_after_week(setup_test_db):
    """R5.3: Test late fee for book >7 days overdue ($0.50 for first 7, $1.00 after)."""
    # Create overdue scenario: 10 days overdue
    add_book_to_catalog("Fee Test 2", "Author", "6666666666663", 1)
    book = get_book_by_isbn("6666666666663")
    
    conn = get_db_connection()
    borrow_date = datetime.now() - timedelta(days=24)  # 24 days ago = 10 days overdue
    due_date = borrow_date + timedelta(days=14)
    
    conn.execute(
        'INSERT INTO borrow_records (patron_id, book_id, borrow_date, due_date) VALUES (?, ?, ?, ?)',
        ("333333", book['id'], borrow_date.isoformat(), due_date.isoformat())
    )
    conn.commit()
    conn.close()
    
    result = calculate_late_fee_for_book("333333", book['id'])
    
    assert result['status'] == 'ok'
    assert result['days_overdue'] == 10
    # 7 days * $0.50 + 3 days * $1.00 = $3.50 + $3.00 = $6.50
    assert result['fee_amount'] == 6.50


def test_r5_calculate_late_fee_max_cap(setup_test_db):
    """R5.4: Test late fee caps at $15.00 maximum."""
    # Create overdue scenario: 30 days overdue (should exceed $15)
    add_book_to_catalog("Fee Test 3", "Author", "6666666666664", 1)
    book = get_book_by_isbn("6666666666664")
    
    conn = get_db_connection()
    borrow_date = datetime.now() - timedelta(days=44)  # 44 days ago = 30 days overdue
    due_date = borrow_date + timedelta(days=14)
    
    conn.execute(
        'INSERT INTO borrow_records (patron_id, book_id, borrow_date, due_date) VALUES (?, ?, ?, ?)',
        ("222222", book['id'], borrow_date.isoformat(), due_date.isoformat())
    )
    conn.commit()
    conn.close()
    
    result = calculate_late_fee_for_book("222222", book['id'])
    
    assert result['status'] == 'ok'
    assert result['days_overdue'] == 30
    assert result['fee_amount'] == 15.00  # Capped at maximum


def test_r5_calculate_no_active_borrow(setup_test_db):
    """R5.5: Test late fee calculation when no active borrow exists."""
    result = calculate_late_fee_for_book("999999", 1)
    
    assert result['fee_amount'] == 0.00
    assert result['days_overdue'] == 0
    assert "no active borrow" in result['status'].lower() or "not found" in result['status'].lower()


# ============================================================================
# R6: BOOK SEARCH - Testing search_books_in_catalog()
# Tests title, author, and ISBN search with partial/exact matching
# ============================================================================

def test_r6_search_by_title_partial_match(setup_test_db):
    """R6.1: Test partial, case-insensitive title search."""
    # Add test books with unique titles
    add_book_to_catalog("Python Programming Guide", "Tech Author", "8888888888881", 3)
    add_book_to_catalog("Advanced Python Techniques", "Tech Author", "8888888888882", 3)
    add_book_to_catalog("Java Development", "Tech Author", "8888888888883", 3)
    
    # Search for "python" which should match 2 books
    results = search_books_in_catalog("python", "title")
    
    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    assert all("python" in book['title'].lower() for book in results)


def test_r6_search_by_author_partial_match(setup_test_db):
    """R6.2: Test partial, case-insensitive author search."""
    # Use unique author names
    add_book_to_catalog("Book 1", "Margaret Atwood", "8888888888884", 3)
    add_book_to_catalog("Book 2", "Margaret Mitchell", "8888888888885", 3)
    add_book_to_catalog("Book 3", "Stephen King", "8888888888886", 3)
    
    # Search for "margaret" - should match 2 authors
    results = search_books_in_catalog("margaret", "author")
    
    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    assert all("margaret" in book['author'].lower() for book in results)


def test_r6_search_by_isbn_exact_match(setup_test_db):
    """R6.3: Test exact ISBN search (must match exactly 13 digits)."""
    add_book_to_catalog("ISBN Test", "Author", "9999999999999", 1)
    
    results = search_books_in_catalog("9999999999999", "isbn")
    
    assert len(results) == 1
    assert results[0]['isbn'] == "9999999999999"


def test_r6_search_empty_term(setup_test_db):
    """R6.4: Test that empty search term returns no results."""
    results = search_books_in_catalog("", "title")
    assert len(results) == 0
    
    results = search_books_in_catalog("   ", "author")
    assert len(results) == 0


def test_r6_search_no_matches(setup_test_db):
    """R6.5: Test search with no matching results."""
    results = search_books_in_catalog("NonexistentBookTitle12345XYZ", "title")
    assert len(results) == 0


def test_r6_search_invalid_isbn_format(setup_test_db):
    """R6.6: Test ISBN search with invalid format returns empty."""
    # ISBN search requires exactly 13 digits
    results = search_books_in_catalog("12345", "isbn")  # Too short
    assert len(results) == 0
    
    results = search_books_in_catalog("123456789012A", "isbn")  # Contains letter
    assert len(results) == 0


# ============================================================================
# R7: PATRON STATUS REPORT - Testing get_patron_status_report()
# Tests patron status including borrowed books, fees, and history
# ============================================================================

def test_r7_patron_status_no_borrows(setup_test_db):
    """R7.1: Test status report for patron with no borrowed books."""
    # Query a patron who has never borrowed anything
    result = get_patron_status_report("000000")
    
    assert result['status'] == 'ok'
    assert result['patron_id'] == "000000"
    assert result['num_currently_borrowed'] == 0
    assert result['total_late_fees'] == 0.00
    assert len(result['currently_borrowed']) == 0


def test_r7_patron_status_with_active_borrows(setup_test_db):
    """R7.2: Test status report for patron with active borrows."""
    # Create books and have patron borrow them
    add_book_to_catalog("Status Book 1", "Author", "7777777777771", 3)
    add_book_to_catalog("Status Book 2", "Author", "7777777777772", 3)
    
    book1 = get_book_by_isbn("7777777777771")
    book2 = get_book_by_isbn("7777777777772")
    
    borrow_book_by_patron("888888", book1['id'])
    borrow_book_by_patron("888888", book2['id'])
    
    result = get_patron_status_report("888888")
    
    assert result['status'] == 'ok'
    assert result['patron_id'] == "888888"
    assert result['num_currently_borrowed'] == 2
    assert len(result['currently_borrowed']) == 2
    assert all('title' in book for book in result['currently_borrowed'])
    assert all('due_date' in book for book in result['currently_borrowed'])


def test_r7_patron_status_with_late_fees(setup_test_db):
    """R7.3: Test status report includes late fees for overdue books."""
    # Create overdue borrow
    add_book_to_catalog("Overdue Status Book", "Author", "7777777777773", 1)
    book = get_book_by_isbn("7777777777773")
    
    conn = get_db_connection()
    borrow_date = datetime.now() - timedelta(days=20)  # 6 days overdue
    due_date = borrow_date + timedelta(days=14)
    
    conn.execute(
        'INSERT INTO borrow_records (patron_id, book_id, borrow_date, due_date) VALUES (?, ?, ?, ?)',
        ("999888", book['id'], borrow_date.isoformat(), due_date.isoformat())
    )
    conn.commit()
    conn.close()
    
    result = get_patron_status_report("999888")
    
    assert result['status'] == 'ok'
    assert result['total_late_fees'] > 0.00  # Should have late fees
    assert result['num_currently_borrowed'] == 1


def test_r7_patron_status_invalid_patron_id(setup_test_db):
    """R7.4: Test status report with invalid patron ID."""
    result = get_patron_status_report("12345")  # Too short
    
    assert result['status'] == 'Invalid patron ID'
    assert result['num_currently_borrowed'] == 0
    assert result['total_late_fees'] == 0.00


def test_r7_patron_status_includes_history(setup_test_db):
    """R7.5: Test that status report includes full borrowing history."""
    # Create a book, borrow and return it
    add_book_to_catalog("History Book", "Author", "7777777777774", 1)
    book = get_book_by_isbn("7777777777774")
    
    borrow_book_by_patron("777888", book['id'])
    return_book_by_patron("777888", book['id'])
    
    result = get_patron_status_report("777888")
    
    assert result['status'] == 'ok'
    assert 'history' in result
    assert isinstance(result['history'], list)
    assert len(result['history']) == 1  # Should have 1 returned book
    
    # Check history record structure
    for record in result['history']:
        assert 'book_id' in record
        assert 'title' in record
        assert 'author' in record
        assert 'borrow_date' in record
        assert 'due_date' in record
        assert 'return_date' in record


# ============================================================================
# ADDITIONAL EDGE CASE TESTS
# ============================================================================

def test_edge_case_whitespace_trimming(setup_test_db):
    """Test that leading/trailing whitespace is properly trimmed."""
    success, message = add_book_to_catalog(
        "  Whitespace Test  ",
        "  Test Author  ",
        "1010101010101",
        3
    )
    
    assert success == True
    book = get_book_by_isbn("1010101010101")
    assert book['title'] == "Whitespace Test"  # Trimmed
    assert book['author'] == "Test Author"  # Trimmed


def test_edge_case_exact_200_char_title(setup_test_db):
    """Test title with exactly 200 characters (boundary test)."""
    exact_200 = "A" * 200
    success, message = add_book_to_catalog(
        exact_200,
        "Author",
        "1212121212121",
        1
    )
    
    assert success == True


def test_edge_case_exact_100_char_author(setup_test_db):
    """Test author with exactly 100 characters (boundary test)."""
    exact_100 = "B" * 100
    success, message = add_book_to_catalog(
        "Title",
        exact_100,
        "1313131313131",
        1
    )
    
    assert success == True


def test_edge_case_case_insensitive_search(setup_test_db):
    """Test that search is truly case-insensitive."""
    add_book_to_catalog("The GREAT Adventure", "SMITH", "1414141414141", 1)
    
    # Search with different cases
    results_lower = search_books_in_catalog("great", "title")
    results_upper = search_books_in_catalog("GREAT", "title")
    results_mixed = search_books_in_catalog("GrEaT", "title")
    
    assert len(results_lower) == 1
    assert len(results_upper) == 1
    assert len(results_mixed) == 1