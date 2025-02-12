import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from shop.models import Order

@pytest.mark.django_db
def test_customer_cannot_modify_status(user_customer, order_factory):
    client = APIClient()
    order = order_factory(customer=user_customer)
    client.force_authenticate(user=user_customer)
    
    response = client.patch(
        reverse('order-detail', args=[order.id]), 
        data={'status': Order.COMPLETED},
        format='json'
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert order.status == Order.PENDING

@pytest.mark.django_db
def test_admin_can_modify_status(user_admin, order_factory):
    client = APIClient()
    order = order_factory()
    client.force_authenticate(user=user_admin)
    
    # Valid transition: PENDING -> COMPLETED
    response = client.patch(
        reverse('order-detail', args=[order.id]), 
        {'status': Order.COMPLETED}, 
        format='json'
    )
    assert response.status_code == status.HTTP_200_OK
    order.refresh_from_db()
    assert order.status == Order.COMPLETED

@pytest.mark.django_db
def test_invalid_status_transition(user_admin, order_factory):
    client = APIClient()
    
    order = order_factory(status=Order.COMPLETED)
    client.force_authenticate(user=user_admin)
    
    # Invalid transition: COMPLETED -> PENDING
    response = client.patch(
        reverse('order-detail', args=[order.id]), 
        {'status': Order.PENDING}, 
        format='json'
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    order.refresh_from_db()
    assert order.status == Order.COMPLETED
    assert "Cannot change status back to PENDING" in str(response.data)
