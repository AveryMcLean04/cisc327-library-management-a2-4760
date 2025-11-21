from playwright.sync_api import expect, sync_playwright
from datetime import datetime, timedelta

def test_launch_app():
    # just my first test to ensure opening the browser works
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("http://localhost:5000/")

        print(page.title())

        expect(page).to_have_title("Library Management System")

        browser.close()

def test_add_and_borrow_book():
    with sync_playwright() as p:
        # book info for reference
        bookTitle = "The Playwright Book"
        author = "Shilliam Wakespeare"
        copies = "25"
        isbn = "1231231231231"
        patronId = "123456"

        #opening the browser
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("http://localhost:5000/")
        #making sure we land on the right page
        expect(page).to_have_title("Library Management System")
        #clicking the add book button
        page.click("text=➕ Add Book")
        #verifying the add_book page loaded properly
        expect(page).to_have_url("http://localhost:5000/add_book")

        #filling out the form and submitting it
        page.fill("#title", bookTitle)
        page.fill("#author", author)
        page.fill("#isbn", isbn)
        page.fill("#total_copies", copies)
        page.click("button[type=submit]")

        #checking the book was added successfully
        expect(page).to_have_url("http://localhost:5000/catalog")
        add_message = f'Book "{bookTitle}" has been successfully added to the catalog.'
        expect(page.locator(".flash-success")).to_have_text(add_message)

        #finding the row with the right book title
        row = page.locator(f'text="{bookTitle}"').locator('xpath=..')
        #filling the patron id and clicking borrow
        row.locator('input[name="patron_id"]').fill(patronId)
        row.locator('button:has-text("Borrow")').click()

        #checking the verification message
        borrow_date = datetime.now()
        due_date = borrow_date + timedelta(days=14)
        #only includign the year month and day
        due_date = due_date.strftime("%Y-%m-%d")
        borrow_message = f'Successfully borrowed "{bookTitle}". Due date: {due_date}.'
        expect(page.locator(".flash-success")).to_have_text(borrow_message)
        #closing the browser
        browser.close()

