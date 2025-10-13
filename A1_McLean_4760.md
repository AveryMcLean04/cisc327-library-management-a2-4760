A1_McLean_4760

Name: Avery McLean
ID: 20354760
Group: 3

2.
| Function Name | Implementation Status | What is Missing/Notes |
|---------------|-----------------------|------------------------|
| R1 | Partial    | The ISBN will accept any string of length 13, not just digits |
| R2 | Complete   | All the required information is displayed on the page         |
| R3 | Partial    | Because the code uses "> 5", each user can borrow 6 books     |
| R4 | Incomplete | R4 is not implemented at all                                  |
| R5 | Incomplete | R5 is not implemented at all                                  |
| R6 | Incomplete | R6 is not implemented at all                                  |
| R7 | Incomplete | R7 is not implemented at all                                  |

3. R1_test.py:
The first unit test, test_add_book_valid_input, works successfully to add a new book, but if we run the test again, it will fail, this is correct because the ISBN needs to be unique for each book that is added, the next three tests are intentionally missing fields or have fields that are incorrect, and all pass, by returning false, as they should. The final test attempts to add a book with an ISBN containing two letters, but is still of length 13, it fails the test because the application will accept an ISBN of length 13, regardless if it is digits, so it fails the test because of this bug.

R3_test.py:
The first test is testing borring a book, it works properly and the tests will pass, except for when a book is not available, then the test fails, but that is expected. The next two tests attempt to borrow a book using an invalid patron ID, and then a book that is unavailable, they return false as expected. The final test has a user try to borrow a book after already borrowing 5 books, this should return false, but on the first try running the test it will fail the best, there is a bug in the code where each user can actually borrow 6 books. Before running the tests I manually borrowed 5 books under one patron ID on the web app, and then ran the test for them to borrow the sixth book, but running it again will not achieve the same results, as when you run it again the patron ID now has six borrowed books, and it will fail, "passing" the test.

R4_test.py:
R4 is incomplete so all four test cases fail, which is to be expected since R4 is not implemented at all. The first test tries to return a book which has been borrowed, which would return true if the code was complete but instead it fails the test. The remaining tests are all supposed to fail, they attempt to use an invalid patron ID, to return a book that isn't borrowed, and return an invalid book ID. These tests all fail because we aren't getting the expected output as this section isn't implemented. Although adding a fake output message is not necessary, and will ensure that the test fails I decided to keep consistent with the other testing in which we assert the output to make sure it is accurate. The final line of any of these tests can be commented, which leads to the tests passing, but that is only because the test returns False and we have asserted False, rather than the functionality working properly.

R5_test.py:
The first test attempts to test a calculate the fee for a book that is not overdue. The next is an attempt to get the late fee for an overdue book. We are just using two book ID's that have been borrowed, not specifically ones that are overdue or not. The next two test are attempts to try to calculate the late fee with a book that has not been returned and for an invalid patron ID. All of these tests fail because this functionality isn't implemented at all. We get a Nonetype error for every test because we are asserting a returned value "result", but since the function returns nothing, we get the error.

R6_test.py:
The first test is to get a partial match on the title that we are searching, we should get any title containing harry potter, and we do the same for the second test but with the author. Next we try to search using the ISBN to get a match, and the final test we try to search with a partial ISBN and it should not match. I used the strategy of asserting an output that wont match, because as currently configured the function will return an empty list and pass the test, we should be looking for an error message of some kind, which we do not get.  Once again all of these tests fail as we have not implemented any part of R6 yet, and we also get lots of errors.

R7_test.py:
The first test attempts to get the status of a valid patron id. The second test attempts to get the status of an invalid patron ID, which also fails. The last two tests attempt to get the status of a valid patron ID with no borrowed books, and then to calculate the late fees of a patron with borrowed books, and what the late fees are. These tests all fail because nothing is implemented for this feature, so that is to be expected.