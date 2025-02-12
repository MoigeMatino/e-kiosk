import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from shop.models import User, Product

@pytest.mark.django_db
def test_admin_can_update_product(user_admin, product_factory):
    client = APIClient()
    product = product_factory()
    client.force_authenticate(user=user_admin)

    response = client.patch(
        reverse('product-detail', args=[product.id]),
        {'price': 200, 'stock': 50},
        format='json'
    )
    assert response.status_code == status.HTTP_200_OK
    product.refresh_from_db()
    assert product.price == 200
    assert product.stock == 50

@pytest.mark.django_db
def test_customer_cannot_modify_product(user_customer, product_factory):
    client = APIClient()
    product = product_factory()
    client.force_authenticate(user=user_customer)

    response = client.patch(
        reverse('product-detail', args=[product.id]),
        {'price': 200},
        format='json'
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
@pytest.mark.django_db
def test_admin_can_delete_product(user_admin, product_factory):
    client = APIClient()
    product = product_factory()
    client.force_authenticate(user=user_admin)

    response = client.delete(reverse('product-detail', args=[product.id]))
    assert response.status_code == status.HTTP_204_NO_CONTENT 
    assert not Product.objects.filter(id=product.id).exists()

    
@pytest.mark.django_db
def test_customer_cannot_delete_product(user_customer, product_factory):
    client = APIClient()
    product = product_factory()
    client.force_authenticate(user=user_customer)

    response = client.delete(reverse('product-detail', args=[product.id]))
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Product.objects.filter(id=product.id).exists()

    
@pytest.mark.django_db
def test_authenticated_customer_can_view_products(user_customer, product_factory):
    client = APIClient()
    product = product_factory()
    client.force_authenticate(user=user_customer)

    response = client.get(reverse('product-list'))
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_unauthenticated_user_cannot_modify_product(product_factory):
    client = APIClient()
    product = product_factory()

    response = client.patch(
        reverse('product-detail', args=[product.id]),
        {'price': 200},
        format='json'
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
