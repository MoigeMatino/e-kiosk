# views.py
from rest_framework import viewsets
from .models import Product, Category, Order
from .serializers import ProductSerializer, CategorySerializer, OrderSerializer

class ProductViewSet(viewsets.ModelViewSet):
    """
    viewset for listing and editing products.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
class CategoryViewSet(viewsets.ModelViewSet):
    """
    viewset for listing and editing categories
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
class OrderViewSet(viewsets.ModelViewSet):
    """
    viewset for listing and managing orders.
    """
    queryset = Order.objects.select_related('customer').prefetch_related(
        'order_items__product'
    ).all() 
    serializer_class = OrderSerializer
