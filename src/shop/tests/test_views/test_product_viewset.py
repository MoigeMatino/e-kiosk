import io

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from shop.models import Product


@pytest.mark.django_db
def test_admin_can_update_product(user_admin, product_factory):
    client = APIClient()
    product = product_factory()
    client.force_authenticate(user=user_admin)

    response = client.patch(
        reverse("product-detail", args=[product.id]), {"price": 200, "stock": 50}, format="json"
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

    response = client.patch(reverse("product-detail", args=[product.id]), {"price": 200}, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_admin_can_delete_product(user_admin, product_factory):
    client = APIClient()
    product = product_factory()
    client.force_authenticate(user=user_admin)

    response = client.delete(reverse("product-detail", args=[product.id]))
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Product.objects.filter(id=product.id).exists()


@pytest.mark.django_db
def test_customer_cannot_delete_product(user_customer, product_factory):
    client = APIClient()
    product = product_factory()
    client.force_authenticate(user=user_customer)

    response = client.delete(reverse("product-detail", args=[product.id]))
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Product.objects.filter(id=product.id).exists()


@pytest.mark.django_db
def test_authenticated_customer_can_view_products(user_customer, product_factory):
    client = APIClient()
    client.force_authenticate(user=user_customer)

    response = client.get(reverse("product-list"))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_unauthenticated_user_cannot_modify_product(product_factory):
    client = APIClient()
    product = product_factory()

    response = client.patch(reverse("product-detail", args=[product.id]), {"price": 200}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_bulk_upload_products_success(user_admin):
    """Test bulk upload of products using a CSV file"""
    client = APIClient()
    client.force_authenticate(user=user_admin)

    # Mock a CSV file content
    csv_content = """name,stock,price,category
    Product 1,10,100.0,Category A
    Product 2,20,200.0,Category B"""

    csv_file = io.BytesIO(csv_content.encode("utf-8"))
    csv_file.name = "products.csv"  # Simulate an uploaded CSV file

    response = client.post(reverse("product-bulk-upload"), {"file": csv_file}, format="multipart")

    assert response.status_code == status.HTTP_201_CREATED
    assert Product.objects.count() == 2
    assert response.data["products_created"] == 2
    assert len(response.data["errors"]) == 0


@pytest.mark.django_db
def test_bulk_upload_products_partial_failures(user_admin):
    """Test bulk upload of products with some rows missing"""
    client = APIClient()
    client.force_authenticate(user=user_admin)

    # Mock a CSV file content with one valid and one invalid row
    csv_content = """name,stock,price,category
    Product 1,10,100,Category A
    ,20,200,Category B"""  # Missing name in the second row

    csv_file = io.BytesIO(csv_content.encode("utf-8"))
    csv_file.name = "products.csv"

    response = client.post(reverse("product-bulk-upload"), {"file": csv_file}, format="multipart")

    assert response.status_code == status.HTTP_207_MULTI_STATUS
    assert Product.objects.count() == 1
    assert response.data["products_created"] == 1
    assert len(response.data["errors"]) == 1
    assert "This field may not be blank." in response.data["errors"][0]["errors"]["name"][0]
