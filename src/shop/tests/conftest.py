import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from shop.models import Category, Order, OrderItem, Product

User = get_user_model()


@pytest.fixture
def user_customer(db):
    """Fixture to create a customer user without a password (OIDC users)"""
    return User.objects.create(email="customer@example.com", role=User.CUSTOMER)


@pytest.fixture
def user_admin(db):
    """Fixture to create an admin user with a password for Django login."""
    return User.objects.create_user(
        email="admin@example.com",
        password="adminpassword123",
        is_staff=True,
        is_superuser=True,
        role=User.ADMIN,
    )


@pytest.fixture
def category_factory(db):
    """Factory fixture for creating categories."""

    def create_category(**kwargs):
        defaults = {"name": "Sample Category"}
        defaults.update(kwargs)
        return Category.objects.create(**defaults)

    return create_category


@pytest.fixture
def product_factory(db, category_factory):
    """Factory fixture for creating products with a default category."""

    def create_product(**kwargs):
        category = kwargs.pop("category", category_factory())
        defaults = {
            "name": "Sample Product",
            "stock": 10,
            "price": 100.00,
            "category": category,
        }
        defaults.update(kwargs)
        return Product.objects.create(**defaults)

    return create_product


@pytest.fixture
def order_factory(db, user_customer):
    """Factory fixture for creating orders."""

    def create_order(**kwargs):
        defaults = {
            "customer": user_customer,
            "status": Order.PENDING,
            "total_price": 0,
        }
        defaults.update(kwargs)
        return Order.objects.create(**defaults)

    return create_order


@pytest.fixture
def order_item_factory(db, product_factory, order_factory):
    """Factory fixture for creating order items."""

    def create_order_item(order=None, product=None, **kwargs):
        if not order:
            order = order_factory()
        if not product:
            product = product_factory()
        defaults = {
            "order": order,
            "product": product,
            "quantity": 1,
            "price_at_time_of_order": product.get_current_price(),
        }
        defaults.update(kwargs)
        return OrderItem.objects.create(**defaults)

    return create_order_item


# Authentication-related fixtures
@pytest.fixture
def client():
    """Fixture for Django test client"""
    return Client()


@pytest.fixture
def oidc_callback_url():
    """Fixture for OIDC callback URL"""
    return reverse("oidc_callback")


@pytest.fixture
def update_profile_url():
    """Fixture for update_profile URL"""
    return reverse("update_profile")
