
NOTIFICATION_TEMPLATES = {
    "order_placed": "Hello {customer_name}, your order #{order_id} has been placed successfully.",
    "order_approved": "Good news, {customer_name}! Your order #{order_id} has been approved.",
    "order_cancelled": "Sorry, {customer_name}. Your order #{order_id} has been cancelled.",
}

DEFAULT_TEMPLATE_VALUES = {
    "customer_name": "valued customer",
    "order_id": "unknown",
}