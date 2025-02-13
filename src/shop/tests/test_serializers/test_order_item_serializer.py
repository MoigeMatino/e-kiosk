import pytest

from shop.models import Category, OrderItem, Product
from shop.serializers import OrderItemSerializer


@pytest.fixture
def product():
    category = Category.objects.create(name="Electronics")
    return Product.objects.create(name="Laptop", category=category, price=1000, discount_price=900, stock=50)


@pytest.mark.django_db
def test_order_item_serialization(product):
    """
    Test that OrderItemSerializer serializes data correctly.
    """
    order_item = OrderItem(product=product, quantity=2, price_at_time_of_order=900)
    serializer = OrderItemSerializer(order_item)
    expected_data = {
        "id": order_item.id,
        "product": product.id,
        "quantity": 2,
        "price_at_time_of_order": "900.00",
    }
    assert serializer.data == expected_data


@pytest.mark.django_db
def test_order_item_deserialization_valid_data(product):
    """
    Test deserialization with valid data.
    """
    data = {"product": product.id, "quantity": 3}
    serializer = OrderItemSerializer(data=data)
    assert serializer.is_valid()
    assert serializer.validated_data["product"] == product
    assert serializer.validated_data["quantity"] == 3


@pytest.mark.django_db
def test_order_item_deserialization_invalid_quantity(product):
    """
    Test that deserialization fails when quantity is zero or negative.
    """
    data = {"product": product.id, "quantity": 0}  # Quantity cannot be zero or negative
    serializer = OrderItemSerializer(data=data)
    assert not serializer.is_valid()
    assert "quantity" in serializer.errors


@pytest.mark.django_db
def test_order_item_read_only_fields(product):
    """
    Test that price_at_time_of_order is a read-only field.
    """
    data = {"product": product.id, "quantity": 5, "price_at_time_of_order": 1000}
    serializer = OrderItemSerializer(data=data)
    assert serializer.is_valid()
    assert "price_at_time_of_order" not in serializer.validated_data
