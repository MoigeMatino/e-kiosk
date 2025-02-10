import pytest
from rest_framework.exceptions import ValidationError
from shop.serializers import ProductSerializer
from shop.models import Product, Category

@pytest.fixture
def category():
    return Category.objects.create(name="Electronics")

@pytest.fixture
def product(category):
    return Product.objects.create(
        name="Smartphone",
        category=category,
        price=1000,
        stock=10,
        discount_price=900
    )

# Test for serialization
@pytest.mark.django_db
def test_product_serializer_serialization(product):
    serializer = ProductSerializer(product)
    expected_data = {
        "id": product.id,
        "name": "Smartphone",
        "category": {"id": product.category.id, "name": "Electronics"},
        "price": "1000.00",
        "stock": 10,
        "discount_price": "900.00"
    }
    assert serializer.data == expected_data

# Test for deserialization with valid data
@pytest.mark.django_db
def test_product_serializer_deserialization(category):
    data = {
        "name": "Laptop",
        "category": {"id": category.id, "name": "Electronics"},
        "price": 1500,
        "stock": 5,
        "discount_price": 1200
    }
    serializer = ProductSerializer(data=data)
    assert serializer.is_valid()
    product = serializer.save()
    assert product.name == "Laptop"
    assert product.category == category
    assert product.price == 1500
    assert product.discount_price == 1200

# Test for validation error when discount_price > price
@pytest.mark.django_db
def test_product_serializer_validation_error(category):
    data = {
        "name": "Tablet",
        "category": {"id": category.id, "name": "Electronics"},
        "price": 800,
        "stock": 3,
        "discount_price": 900  # Invalid: discount_price > price
    }
    serializer = ProductSerializer(data=data)
    with pytest.raises(ValidationError) as excinfo:
        serializer.is_valid(raise_exception=True)
    assert "must be lower than the regular price" in str(excinfo.value)

# Test for updating a product
@pytest.mark.django_db
def test_product_serializer_update(product):
    data = {
        "name": "Updated Smartphone",
        "category": {"id": product.category.id, "name": "Electronics"},
        "price": 1100,
        "stock": 8,
        "discount_price": 950
    }
    serializer = ProductSerializer(instance=product, data=data)
    assert serializer.is_valid()
    updated_product = serializer.save()
    assert updated_product.name == "Updated Smartphone"
    assert updated_product.price == 1100
    assert updated_product.stock == 8
    assert updated_product.discount_price == 950
