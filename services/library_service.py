"""
Library Service Module - Business Logic Functions
Contains all the core business logic for the Library Management System
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import (
    get_book_by_id, get_book_by_isbn, get_patron_borrow_count,
    insert_book, insert_borrow_record, update_book_availability,
    update_borrow_record_return_date, get_all_books
)
from services.payment_service import PaymentGateway

def add_book_to_catalog(title: str, author: str, isbn: str, total_copies: int) -> Tuple[bool, str]:
    """
    Add a new book to the catalog.
    Implements R1: Book Catalog Management
    
    Args:
        title: Book title (max 200 chars)
        author: Book author (max 100 chars)
        isbn: 13-digit ISBN
        total_copies: Number of copies (positive integer)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Input validation
    if not title or not title.strip():
        return False, "Title is required."
    
    if len(title.strip()) > 200:
        return False, "Title must be less than 200 characters."
    
    if not author or not author.strip():
        return False, "Author is required."
    
    if len(author.strip()) > 100:
        return False, "Author must be less than 100 characters."
    
    if len(isbn) != 13 or not isbn.isdigit(): #making sure it all all digits, can't contain letters
        return False, "ISBN must be exactly 13 digits."
    
    if not isinstance(total_copies, int) or total_copies <= 0:
        return False, "Total copies must be a positive integer."
    
    # Check for duplicate ISBN
    existing = get_book_by_isbn(isbn)
    if existing:
        return False, "A book with this ISBN already exists."
    
    # Insert new book
    success = insert_book(title.strip(), author.strip(), isbn, total_copies, total_copies)
    if success:
        return True, f'Book "{title.strip()}" has been successfully added to the catalog.'
    else:
        return False, "Database error occurred while adding the book."

def borrow_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Allow a patron to borrow a book.
    Implements R3 as per requirements  
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book to borrow
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."
    
    # Check if book exists and is available
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."
    
    if book['available_copies'] <= 0:
        return False, "This book is currently not available."
    
    # Check patron's current borrowed books count
    current_borrowed = get_patron_borrow_count(patron_id)
    
    if current_borrowed >= 5: #Eliminating the bug where a user with 5 borrwed books can still borrow one more.
        return False, "You have reached the maximum borrowing limit of 5 books."
    
    # Create borrow record
    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=14)
    
    # Insert borrow record and update availability
    borrow_success = insert_borrow_record(patron_id, book_id, borrow_date, due_date)
    if not borrow_success:
        return False, "Database error occurred while creating borrow record."
    
    availability_success = update_book_availability(book_id, -1)
    if not availability_success:
        return False, "Database error occurred while updating book availability."
    
    return True, f'Successfully borrowed "{book["title"]}". Due date: {due_date.strftime("%Y-%m-%d")}.'

def return_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Process book return by a patron (R4).
    - verify active borrow exists
    - set return date
    - increment availability
    - calculate & display late fee
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."

    # Verify book exists
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."

    # Get active borrow record (return_date IS NULL)
    try:
        from database import get_active_borrow_record
    except Exception:
        return False, "Database function missing."

    record = get_active_borrow_record(patron_id, book_id)
    if not record:
        return False, "No active borrow record found for this patron and book."

    now = datetime.now()

    # Compute late fee using the shared helper from R5
    fee_amount, days_overdue = _compute_late_fee(record['borrow_date'], now)

    # Update DB: set return date
    if not update_borrow_record_return_date(patron_id, book_id, now):
        return False, "Database error occurred while recording the return."

    # Update DB: increment availability
    if not update_book_availability(book_id, +1):
        return False, "Database error occurred while updating book availability."

    # Build user-facing message
    if fee_amount > 0:
        return True, (
            f'Returned "{book["title"]}". '
            f'Late by {days_overdue} day(s). Fee owed: ${fee_amount:.2f}.'
        )
    else:
        return True, f'Returned "{book["title"]}". No late fee.'


def calculate_late_fee_for_book(patron_id: str, book_id: int) -> Dict:
    """
    Calculate late fees for a specific book (R5).
    Returns dict: {'fee_amount': float, 'days_overdue': int, 'status': str}
    """
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return {'fee_amount': 0.00, 'days_overdue': 0, 'status': 'Invalid patron ID'}

    book = get_book_by_id(book_id)
    if not book:
        return {'fee_amount': 0.00, 'days_overdue': 0, 'status': 'Book not found'}

    try:
        from database import get_active_borrow_record
    except Exception:
        return {'fee_amount': 0.00, 'days_overdue': 0, 'status': 'Database function missing'}

    record = get_active_borrow_record(patron_id, book_id)
    if not record:
        return {'fee_amount': 0.00, 'days_overdue': 0, 'status': 'No active borrow found'}

    borrow_date = record.get('borrow_date')
    if not borrow_date:
        return {'fee_amount': 0.00, 'days_overdue': 0, 'status': 'Borrow date missing'}

    fee, days = _compute_late_fee(borrow_date, datetime.now())
    return {'fee_amount': fee, 'days_overdue': days, 'status': 'ok'}

def _compute_late_fee(borrow_date: datetime, as_of: datetime) -> tuple[float, int]:
    """
    Return (fee_amount, days_overdue) using R5 rules.
    - Due 14 days after borrow_date
    - $0.50/day for first 7 days overdue
    - $1.00/day each day after 7
    - Max $15.00
    """
    due_date = borrow_date + timedelta(days=14)
    days_overdue = max(0, (as_of.date() - due_date.date()).days)
    if days_overdue == 0:
        return 0.00, 0

    first_seven = min(days_overdue, 7)
    remaining = max(days_overdue - 7, 0)
    fee = first_seven * 0.50 + remaining * 1.00
    fee = min(fee, 15.00)
    return round(fee, 2), days_overdue

def search_books_in_catalog(search_term: str, search_type: str) -> List[Dict]:
    """
    Search for books in the catalog.
    
    TODO: Implement R6 as per requirements
    """
    q = (search_term or "").strip()
    if not q:
        return []

    stype = (search_type or "title").lower()
    if stype not in {"title", "author", "isbn"}:
        stype = "title"

    # Fetch all books (same shape the catalog uses)
    books = get_all_books() or []

    # ISBN: exact match, must be exactly 13 digits
    if stype == "isbn":
        if len(q) != 13 or not q.isdigit():
            return []
        return [b for b in books if str(b.get("isbn", "")) == q]

    # Title/Author: partial (substring), case-insensitive
    field = "title" if stype == "title" else "author"
    q_lower = q.lower()
    return [b for b in books if q_lower in str(b.get(field, "")).lower()]

def get_patron_status_report(patron_id: str) -> Dict:
    """
    R7: Patron status snapshot.
    - Currently borrowed (with due dates)
    - Total late fees owed (sum over active borrows)
    - Number of books currently borrowed
    - Full borrowing history
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return {
            'patron_id': patron_id,
            'currently_borrowed': [],
            'num_currently_borrowed': 0,
            'total_late_fees': 0.00,
            'history': [],
            'status': 'Invalid patron ID'
        }

    # Import here to avoid circulars
    try:
        from database import get_patron_borrow_history
    except Exception:
        return {
            'patron_id': patron_id,
            'currently_borrowed': [],
            'num_currently_borrowed': 0,
            'total_late_fees': 0.00,
            'history': [],
            'status': 'Database function missing'
        }

    history = get_patron_borrow_history(patron_id) or []

    # Build active list + compute total fees using the same fee logic as R5
    now = datetime.now()
    active = []
    total_fees = 0.0

    for rec in history:
        if rec.get('return_date') is None:  # active borrow
            fee_amt, _days = _compute_late_fee(rec['borrow_date'], now)
            total_fees += fee_amt
            active.append({
                'book_id': rec['book_id'],
                'title': rec['title'],
                'due_date': rec['due_date'].strftime('%Y-%m-%d'),
            })

    # Convert history dates to strings for easy rendering / JSON
    hist_out = []
    for rec in history:
        hist_out.append({
            'book_id': rec['book_id'],
            'title': rec['title'],
            'author': rec['author'],
            'borrow_date': rec['borrow_date'].strftime('%Y-%m-%d'),
            'due_date': rec['due_date'].strftime('%Y-%m-%d'),
            'return_date': rec['return_date'].strftime('%Y-%m-%d') if rec['return_date'] else None,
        })

    return {
        'patron_id': patron_id,
        'currently_borrowed': active,
        'num_currently_borrowed': len(active),
        'total_late_fees': round(total_fees, 2),
        'history': hist_out,
        'status': 'ok'
    }

def pay_late_fees(patron_id: str, book_id: int, payment_gateway: PaymentGateway = None) -> Tuple[bool, str, Optional[str]]:
    """
    Process payment for late fees using external payment gateway.
    
    NEW FEATURE FOR ASSIGNMENT 3: Demonstrates need for mocking/stubbing
    This function depends on an external payment service that should be mocked in tests.
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book with late fees
        payment_gateway: Payment gateway instance (injectable for testing)
        
    Returns:
        tuple: (success: bool, message: str, transaction_id: Optional[str])
        
    Example for you to mock:
        # In tests, mock the payment gateway:
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.process_payment.return_value = (True, "txn_123", "Success")
        success, msg, txn = pay_late_fees("123456", 1, mock_gateway)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits.", None
    
    # Calculate late fee first
    fee_info = calculate_late_fee_for_book(patron_id, book_id)
    
    # Check if there's a fee to pay
    if not fee_info or 'fee_amount' not in fee_info:
        return False, "Unable to calculate late fees.", None
    
    fee_amount = fee_info.get('fee_amount', 0.0)
    
    if fee_amount <= 0:
        return False, "No late fees to pay for this book.", None
    
    # Get book details for payment description
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found.", None
    
    # Use provided gateway or create new one
    if payment_gateway is None:
        payment_gateway = PaymentGateway()
    
    # Process payment through external gateway
    # THIS IS WHAT YOU SHOULD MOCK IN THEIR TESTS!
    try:
        success, transaction_id, message = payment_gateway.process_payment(
            patron_id=patron_id,
            amount=fee_amount,
            description=f"Late fees for '{book['title']}'"
        )
        
        if success:
            return True, f"Payment successful! {message}", transaction_id
        else:
            return False, f"Payment failed: {message}", None
            
    except Exception as e:
        # Handle payment gateway errors
        return False, f"Payment processing error: {str(e)}", None


def refund_late_fee_payment(transaction_id: str, amount: float, payment_gateway: PaymentGateway = None) -> Tuple[bool, str]:
    """
    Refund a late fee payment (e.g., if book was returned on time but fees were charged in error).
    
    NEW FEATURE FOR ASSIGNMENT 3: Another function requiring mocking
    
    Args:
        transaction_id: Original transaction ID to refund
        amount: Amount to refund
        payment_gateway: Payment gateway instance (injectable for testing)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate inputs
    if not transaction_id or not transaction_id.startswith("txn_"):
        return False, "Invalid transaction ID."
    
    if amount <= 0:
        return False, "Refund amount must be greater than 0."
    
    if amount > 15.00:  # Maximum late fee per book
        return False, "Refund amount exceeds maximum late fee."
    
    # Use provided gateway or create new one
    if payment_gateway is None:
        payment_gateway = PaymentGateway()
    
    # Process refund through external gateway
    # THIS IS WHAT YOU SHOULD MOCK IN YOUR TESTS!
    try:
        success, message = payment_gateway.refund_payment(transaction_id, amount)
        
        if success:
            return True, message
        else:
            return False, f"Refund failed: {message}"
            
    except Exception as e:
        return False, f"Refund processing error: {str(e)}"
