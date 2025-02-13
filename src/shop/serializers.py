from rest_framework import serializers

from shop.models import Category, Order, OrderItem, Product


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for category, used within the ProductSerializer
    """

    class Meta:
        model = Category
        fields = ["id", "name"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer()  # Nested serializer to display category details

    class Meta:
        model = Product
        fields = ["id", "name", "category", "price", "stock", "discount_price"]

    def validate(self, data):
        """
        Ensure that discount_price is always less than price.
        """
        price = data.get("price")
        discount_price = data.get("discount_price")
        if discount_price and discount_price >= price:
            raise serializers.ValidationError("Discount price must be lower than the regular price.")
        return data

    def create(self, validated_data):
        category_data = validated_data.pop("category")
        category, _ = Category.objects.get_or_create(**category_data)
        product = Product.objects.create(category=category, **validated_data)
        return product

    def update(self, instance, validated_data):
        category_data = validated_data.pop("category", None)
        if category_data:
            category, _ = Category.objects.get_or_create(**category_data)
            instance.category = category

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for order items, used within the OrderSerializer
    """

    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity", "price_at_time_of_order"]
        read_only_fields = ["id", "price_at_time_of_order"]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ["id", "customer", "status", "total_price", "order_items", "created_at"]
        read_only_fields = ["id", "total_price", "created_at"]

    def validate(self, data):
        """
        Custom validation for business rules.
        """

        errors = {}
        if self.instance:
            if "total_price" in self.initial_data:
                errors["total_price"] = "This field is read-only."

            if "created_at" in self.initial_data:
                errors["created_at"] = "This field is read-only."

        if errors:
            raise serializers.ValidationError(errors)

        if not self.instance:  # Check if creating a new order
            order_items = data.get("order_items", [])

            if not order_items:
                raise serializers.ValidationError("An order must contain at least one item.")

            product_ids = [item["product"] for item in order_items]
            if len(product_ids) != len(set(product_ids)):
                raise serializers.ValidationError(
                    "You cannot order the same product twice in the same order."
                )

            # check each order_item product stock availability
            for order_item in order_items:
                product = order_item["product"]
                quantity = order_item["quantity"]
                if not product.is_in_stock(quantity):
                    raise serializers.ValidationError(
                        f"The product {product.name} is out of stock for the requested quantity."
                    )

        return data

    def validate_status(self, value):
        if self.instance:  # when updating an order
            current_status = self.instance.status

            # Prevent changing COMPLETED or CANCELLED back to PENDING
            if current_status in [Order.COMPLETED, Order.CANCELLED] and value == Order.PENDING:
                raise serializers.ValidationError(
                    "Cannot change status back to PENDING from COMPLETED or CANCELLED."
                )
        return value

    def create(self, validated_data):
        order_items_data = validated_data.pop("order_items")
        order = Order.objects.create(**validated_data)

        # store product IDs and their quantities
        items_to_process = [(item["product"].id, item["quantity"]) for item in order_items_data]

        # Use the place_order method to process order items
        order.place_order(items_to_process)

        return order
