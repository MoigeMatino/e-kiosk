import pytest
from shop.models import Order
from django.db import IntegrityError

@pytest.mark.django_db
def test_approve_order(order_factory, order_item_factory, product_factory):
    """Test that approving an order deducts stock and changes order status to COMPLETED."""
    product = product_factory(stock=5)
    order = order_factory()
    order_item_factory(order=order, product=product, quantity=3)

    assert product.stock == 5
    assert order.status == Order.PENDING

    order.approve_order()

    order.refresh_from_db()
    product.refresh_from_db()

    assert order.status == Order.COMPLETED
    assert product.stock == 2  # Stock reduced by 3

@pytest.mark.django_db
def test_approve_order_insufficient_stock_after_stock_change(order_factory, order_item_factory, product_factory):
    """
    Test that order approval fails if stock becomes insufficient after the order is created
    Stock can become insufficient after order creation if:
    - another admin approves a different order that reduces stock for the same product(orders are placed but not approved immediately)
    - manual stock adjustments(this test simulates this)    
    """
    product = product_factory(stock=5)
    order = order_factory()
    order_item_factory(order=order, product=product, quantity=4)  # Initially, this is a valid order item

    # mimicking another order being approved that reduces the stock
    product.stock = 2  # Now the stock is lower than the order quantity
    product.save(update_fields=['stock'])

    with pytest.raises(IntegrityError, match=f"Insufficient stock for product {product.name}."):
        order.approve_order()  # This should raise an IntegrityError

    # Ensure the status and stock haven't changed
    order.refresh_from_db()
    product.refresh_from_db()

    assert order.status == Order.PENDING
    assert product.stock == 2  # Stock remains unchanged after the failed approval


@pytest.mark.django_db
def test_cancel_order(order_factory):
    """Test that canceling a pending order changes the status to CANCELED."""
    order = order_factory(status=Order.PENDING)

    order.cancel_order()

    order.refresh_from_db()

    assert order.status == Order.CANCELED
