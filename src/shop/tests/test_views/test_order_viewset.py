import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from shop.models import Order, User


def test_customer_can_create_order(user_customer, product_factory):
    client = APIClient()
    product = product_factory()
    client.force_authenticate(user=user_customer)
    response = client.post(
        reverse('order-list'), 
        data = {
        "customer": user_customer.id,
        "order_items": [
            {
                "product": product.id,
                "quantity": 1
            }
        ],
        "status": Order.PENDING
    },
    format='json'
    
)
    assert response.status_code == status.HTTP_201_CREATED


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


def test_customer_can_view_own_order(user_customer, order_factory):
    client = APIClient()
    order = order_factory(customer=user_customer)
    client.force_authenticate(user=user_customer)
    response = client.get(
        reverse('order-detail', args=[order.id])
        )
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_customer_cannot_access_another_customers_order(user_customer, order_factory):
    """Ensure customers cannot access another customer's orders"""
    client = APIClient()
    user_customer2 = User.objects.create(email="customer2@example.com", role=User.CUSTOMER)
    order = order_factory(customer=user_customer2)
    client.force_authenticate(user_customer)

    response = client.get(reverse('order-detail', args=[order.id]))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    
@pytest.mark.django_db
def test_admin_can_access_all_orders(user_admin, order_factory):
    """Ensure customers cannot access another customer's orders"""
    client = APIClient()
    user_customer2 = User.objects.create(email="customer2@example.com", role=User.CUSTOMER)
    order1 = order_factory() # created by user_customer
    order2 = order_factory(customer=user_customer2)
    
    client.force_authenticate(user_admin)

    response = client.get(reverse('order-list'))

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2
    

def test_admin_cannot_delete_order(user_admin, order_factory):
    client = APIClient()
    order = order_factory()
    client.force_authenticate(user_admin)
    response = client.delete(reverse('order-detail', args=[order.id]))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_unauthorized_user_cannot_access_orders(order_factory):
    """Ensure unauthenticated users cannot access any orders"""
    client = APIClient()
    order = order_factory()

    response = client.get(reverse('order-detail', args=[order.id]))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
