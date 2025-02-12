import pytest
from decimal import Decimal
from shop.serializers import OrderSerializer
from shop.models import Product, Category, Order, User

# Fixture to create a sample customer user

@pytest.fixture
def user_customer(db):
    return User.objects.create_user(email="customer@example.com", password="testpassword123", role=User.CUSTOMER)


@pytest.fixture
def category():
    return Category.objects.create(name="Electronics")

@pytest.fixture
def product1(category):
    return Product.objects.create(
        name="Laptop",
        category=category,
        price=Decimal('1000.00'),
        stock=10,
        discount_price=Decimal('900.00')
    )

@pytest.fixture
def product2(category):
    return Product.objects.create(
        name="Phone",
        category=category,
        price=Decimal('500.00'),
        stock=5,
        discount_price=Decimal('450.00')
    )

@pytest.mark.django_db
def test_order_serializer_valid(user_customer, product1, product2):
    """
    order serializer validates and creates an order correctly with a customer.
    """
    data = {
        "customer": user_customer.id,
        "order_items": [
            {"product": product1.id, "quantity": 2},
            {"product": product2.id, "quantity": 1}
        ]
    }
    serializer = OrderSerializer(data=data)
    assert serializer.is_valid(), serializer.errors

    order = serializer.save()
    assert order.customer == user_customer
    assert order.total_price == Decimal('2250.00')
    assert order.order_items.count() == 2


@pytest.mark.django_db
def test_order_status_defaults_to_pending(user_customer, product1, product2):
    """
    Ensure that the status of a newly created order is PENDING.
    """
    data = {
        "customer": user_customer.id,
        "order_items": [
            {"product": product1.id, "quantity": 1},
            {"product": product2.id, "quantity": 2}
        ]
    }
    serializer = OrderSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    order = serializer.save()
    assert order.status == Order.PENDING

@pytest.mark.django_db
def test_order_serializer_invalid_stock(user_customer, product1):
    """
    order serializer fails when stock is insufficient.
    """
    data = {
        "customer": user_customer.id,
        "order_items": [
            {"product": product1.id, "quantity": 20} 
        ]
    }
    serializer = OrderSerializer(data=data)
    assert not serializer.is_valid()
    assert f"{product1.name} is out of stock for the requested quantity" in str(serializer.errors)

@pytest.mark.django_db
def test_order_serializer_duplicate_products(user_customer, product1):
    """
    order serializer fails when the same product is added twice.
    """
    data = {
        "customer": user_customer.id,
        "order_items": [
            {"product": product1.id, "quantity": 1},
            {"product": product1.id, "quantity": 2}  # Duplicate product
        ]
    }
    serializer = OrderSerializer(data=data)
    assert not serializer.is_valid()
    assert "You cannot order the same product twice in the same order." in str(serializer.errors)

@pytest.mark.django_db
def test_order_readonly_fields(user_customer):
    """
    readonly fields like status and total_price cannot be updated.
    """
    order = Order.objects.create(
        customer=user_customer,
        # status=Order.PENDING,
        total_price=Decimal('500.00')
        )
    
    data = {
        "customer": user_customer.id,
        "total_price": Decimal('1000.00')  # Attempt to change total_price
    }
    serializer = OrderSerializer(order, data=data, partial=True)
    assert not serializer.is_valid()
    assert "This field is read-only." in str(serializer.errors['total_price'])
    
