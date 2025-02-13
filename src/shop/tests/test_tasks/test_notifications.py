from unittest.mock import patch

import pytest

from shop.models import Notification
from shop.tasks import send_email_task, send_sms_task


@patch("shop.tasks.send_sms_task")
def test_send_sms_task_order_placed(mock_task, order_factory):
    """Test SMS sending task"""
    order = order_factory()
    mock_task.return_value = None
    response = send_sms_task("+254799887766", "order_placed", order_id=order.id)
    assert response is None
    # Assert a notification was created
    assert Notification.objects.filter(message__contains="has been placed successfully").exists()


@patch("shop.tasks.send_sms_task")
def test_send_sms_task_order_approved(mock_task, order_factory):
    """Test SMS sending task"""
    order = order_factory()
    mock_task.return_value = None
    response = send_sms_task("+254799887766", "order_approved", order_id=order.id)
    assert response is None
    # Assert a notification was created
    assert Notification.objects.filter(message__contains="has been approved.").exists()


@patch("shop.tasks.send_sms_task")
def test_send_sms_task_order_cancelled(mock_task, order_factory):
    """Test SMS sending task"""
    order = order_factory()
    mock_task.return_value = None
    response = send_sms_task("+254799887766", "order_cancelled", order_id=order.id)
    assert response is None
    # Assert a notification was created
    assert Notification.objects.filter(message__contains="has been cancelled.").exists()


@pytest.mark.django_db
@patch("shop.tasks.send_email_task")
def test_send_email_task(mock_task):
    """Test email sending task"""
    mock_task.return_value = None  # send_mail returns None on success
    response = send_email_task("New Order", "Test message", ["admin@ekiosk.com"])
    assert response is None
    # Assert a notification was created
    assert Notification.objects.filter(message__contains="Test message").exists()
