import pytest
from unittest.mock import Mock, MagicMock
from services.library_service import pay_late_fees, refund_late_fee_payment
from services.payment_service import PaymentGateway

# test successful payment
def test_pay_late_fees_success(mocker):
    #stub the late fee calculation
    mocker.patch("services.library_service.calculate_late_fee_for_book", return_value={"fee_amount": 5.00, "days_overdue": 3, "status": "ok"},)
    #stub the lookup
    mocker.patch("services.library_service.get_book_by_id", return_value={"id": 1, "title": "1984", "available_copies": 0},)

    #mock paymentgateway
    gateway = Mock(spec=PaymentGateway)

    #simulate successful payment
    gateway.process_payment.return_value = (True, "txn_123", "OK")

    patron_id = "123456"
    book_id = 1

    success, message, txn = pay_late_fees(patron_id, book_id, payment_gateway=gateway)

    assert success is True
    assert txn == "txn_123"
    assert "Payment Successful" in message or "OK" in message

    gateway.process_payment.assert_called_once_with(
        patron_id = "123456",
        amount = 5.00,
        description = "Late fees for '1984'",
    )

    

# payment declined by gateway
def test_payment_declined_by_gateway(mocker):
    #stub the late fee calculation
    mocker.patch("services.library_service.calculate_late_fee_for_book", return_value={"fee_amount": 5.00, "days_overdue": 3, "status": "ok"},)
    #stub the lookup
    mocker.patch("services.library_service.get_book_by_id", return_value={"id": 1, "title": "1984", "available_copies": 0},)

    gateway = Mock(spec=PaymentGateway)

    gateway.process_payment.return_value = (False, None, "declined by gateway")

    success, message, txn = pay_late_fees("123456", 1, payment_gateway=gateway)

    assert success is False
    assert txn is None
    assert "declined by gateway" in message.lower()

    gateway.process_payment.assert_called_once_with(
        patron_id = "123456",
        amount = 5.00,
        description = "Late fees for '1984'",
    )

# invalid patron ID - verify mock not called
def test_pay_late_fees_invalid_id(mocker):
    #stub the late fee calculation
    mocker.patch("services.library_service.calculate_late_fee_for_book", return_value={"fee_amount": 5.00, "days_overdue": 3, "status": "ok"},)
    #stub the lookup
    mocker.patch("services.library_service.get_book_by_id", return_value={"id": 1, "title": "1984", "available_copies": 0},)

    #mock paymentgateway
    gateway = Mock(spec=PaymentGateway)

    patron_id = ""
    book_id = 1

    success, message, txn = pay_late_fees(patron_id, book_id, payment_gateway=gateway)

    assert success is False
    assert txn == None
    assert "Invalid patron ID. Must be exactly 6 digits." in message or "OK" in message

    gateway.process_payment.assert_not_called()

# zero late fees
def test_pay_late_fees_zero_fee(mocker):
    #stub the late fee calculation
    mocker.patch("services.library_service.calculate_late_fee_for_book", return_value={"fee_amount": 0.00, "days_overdue": 0, "status": "ok"},)
    #stub the lookup
    mocker.patch("services.library_service.get_book_by_id", return_value={"id": 1, "title": "1984", "available_copies": 0},)

    #mock paymentgateway
    gateway = Mock(spec=PaymentGateway)

    #simulate successful payment
    gateway.process_payment.return_value = (False, None, "OK")

    patron_id = "123456"
    book_id = 1

    success, message, txn = pay_late_fees(patron_id, book_id, payment_gateway=gateway)

    assert success is False
    assert txn == None
    assert "No late fees to pay for this book." in message

    gateway.process_payment.assert_not_called()

# network error exception handling
def test_pay_late_fees_network_error_handling(mocker):
    #stub the late fee calculation
    mocker.patch("services.library_service.calculate_late_fee_for_book", return_value={"fee_amount": 5.00, "days_overdue": 3, "status": "ok"},)
    #stub the lookup
    mocker.patch("services.library_service.get_book_by_id", return_value={"id": 1, "title": "1984", "available_copies": 0},)

    gateway = Mock(spec=PaymentGateway)
    gateway.process_payment.side_effect = ConnectionError("Gateway not able to be reached")

    success, message, txn = pay_late_fees("123456", 1, payment_gateway=gateway)

    assert success is False
    assert txn is None
    assert "Payment processing error" in message

    gateway.process_payment.assert_called_once_with(
        patron_id = "123456",
        amount = 5.00,
        description = "Late fees for '1984'",
    )

#successful refund
def test_refund_late_fee_payment_success(mocker):
    gateway = Mock(spec=PaymentGateway)
    gateway.refund_payment.return_value = (True, "Refund ok")

    success, message = refund_late_fee_payment("txn_123", 5.00, payment_gateway=gateway)

    assert success is True
    assert message == "Refund ok"
    gateway.refund_payment.assert_called_once_with(
        "txn_123",
        5.00,
    )

#invalid transaction ID rejection
def test_refund_late_fee_payment_invalid_txn(mocker):
    gateway = Mock(spec=PaymentGateway)
    
    success, message = refund_late_fee_payment("", 5.00, payment_gateway=gateway)

    assert success is False
    assert "Invalid transaction ID" in message
    gateway.refund_payment.assert_not_called()

# invalid refund amounts (negative, 0, exceeds $15 maximum)
def test_refund_late_fee_payment_negative(mocker):
    gateway = Mock(spec=PaymentGateway)

    success, message = refund_late_fee_payment("txn_123", -5.00, payment_gateway=gateway)

    assert success is False
    assert "Refund amount must be greater than 0." in message
    gateway.refund_payment.assert_not_called()

def test_refund_late_fee_payment_zero(mocker):
    gateway = Mock(spec=PaymentGateway)

    success, message = refund_late_fee_payment("txn_123", 0.00, payment_gateway=gateway)

    assert success is False
    assert "Refund amount must be greater than 0." in message
    gateway.refund_payment.assert_not_called()

def test_refund_late_fee_payment_over_15(mocker):
    gateway = Mock(spec=PaymentGateway)

    success, message = refund_late_fee_payment("txn_123", 20.00, payment_gateway=gateway)

    assert success is False
    assert "Refund amount exceeds maximum late fee." in message
    gateway.refund_payment.assert_not_called()
