from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from .models import Product, Category, Order
from .serializers import ProductSerializer, CategorySerializer, OrderSerializer
from mozilla_django_oidc.views import OIDCAuthenticationCallbackView
import logging
#! to remove
logger = logging.getLogger(__name__)

User = get_user_model()

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
    
class CustomOIDCCallbackView(OIDCAuthenticationCallbackView):
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        
        # Ensure the user is authenticated
        user = request.user
        if user.is_authenticated:
            logger.info(f"User {user.email} is authenticated. Checking phone number...")

            # Check if phone number is missing
            if not user.phone_number:
                logger.info("Redirecting to update-profile because phone number is missing.")
                return redirect('update_profile')

            logger.info("No redirection needed. Proceeding with the normal flow.")
        return response

class UpdateProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        user = request.user
        phone_number = request.data.get('phone_number')

        if not phone_number:
            return Response({'error': 'Phone number is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Update user's phone number
        user.phone_number = phone_number
        user.save()

        return Response({'message': 'Profile updated successfully.'}, status=status.HTTP_200_OK)