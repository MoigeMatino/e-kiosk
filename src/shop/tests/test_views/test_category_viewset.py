import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_calculate_average_price_no_products(user_admin, category_factory):
    """Test calculating average price for a category with no products"""
    client = APIClient()
    category = category_factory(name="Empty Category")
    client.force_authenticate(user=user_admin)

    response = client.get(reverse("category-calculate-average-price", args=[category.id]))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data["message"] == "No products found in this category or its subcategories."


@pytest.mark.django_db
def test_calculate_average_price_with_products(user_admin, category_factory, product_factory):
    """Test calculating average price for a category with products"""
    client = APIClient()
    category = category_factory(name="Main Category")
    product_factory(category=category, price=100)
    product_factory(category=category, price=200)
    client.force_authenticate(user=user_admin)

    response = client.get(reverse("category-calculate-average-price", args=[category.id]))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["average_price"] == 150  # (100 + 200) / 2
    assert response.data["products_count"] == 2


@pytest.mark.django_db
def test_calculate_average_price_with_nested_categories(user_admin, category_factory, product_factory):
    """Test calculating average price for a category with nested subcategories"""
    client = APIClient()
    main_category = category_factory(name="Main Category")
    subcategory = category_factory(name="Subcategory", parent=main_category)
    product_factory(category=main_category, price=300)
    product_factory(category=subcategory, price=500)
    client.force_authenticate(user=user_admin)

    response = client.get(reverse("category-calculate-average-price", args=[main_category.id]))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["average_price"] == 400  # (300 + 500) / 2
    assert response.data["products_count"] == 2
    assert response.data["subcategory_count"] == 1


@pytest.mark.django_db
def test_calculate_average_price_nested_beyond_two_levels(user_admin, category_factory, product_factory):
    """Test calculating average price for a category with nested subcategories beyond two levels."""
    client = APIClient()
    main_category = category_factory(name="Main Category")
    subcategory = category_factory(name="Subcategory", parent=main_category)
    nested_subcategory = category_factory(name="Nested Subcategory", parent=subcategory)
    product_factory(category=main_category, price=300)
    product_factory(category=subcategory, price=500)
    product_factory(category=nested_subcategory, price=700)
    client.force_authenticate(user=user_admin)

    response = client.get(reverse("category-calculate-average-price", args=[main_category.id]))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["average_price"] == 500  # (300 + 500 + 700) / 3
    assert response.data["products_count"] == 3
    assert response.data["subcategory_count"] == 2


@pytest.mark.django_db
def test_customer_cannot_create_categories(user_customer):
    """Test that a customer cannot create categories"""
    client = APIClient()
    client.force_authenticate(user=user_customer)

    response = client.post(reverse("category-list"), data={"name": "New Category"}, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN
