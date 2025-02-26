import csv
import io

from django.contrib.auth import get_user_model
from django.db.models import Avg, Q
from django.shortcuts import redirect
from mozilla_django_oidc.views import OIDCAuthenticationCallbackView
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Order, Product
from .permissions import IsAdminOrReadOnly, IsOrderOwnerOrAdminWithLimitedUpdate
from .serializers import CategorySerializer, OrderSerializer, ProductSerializer

User = get_user_model()


class ProductViewSet(viewsets.ModelViewSet):
    """
    viewset for listing and editing products.
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    @action(detail=False, methods=["post"], parser_classes=[MultiPartParser])
    def bulk_upload(self, request):
        """Bulk upload products from a CSV file."""
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        if not file.name.endswith(".csv"):
            return Response({"error": "Please upload a valid CSV file."}, status=status.HTTP_400_BAD_REQUEST)

        if file.size == 0:
            return Response({"error": "The uploaded file is empty."}, status=status.HTTP_400_BAD_REQUEST)

        products_created = 0
        errors = []

        try:
            decoded_file = io.TextIOWrapper(file, encoding="utf-8")
            reader = csv.DictReader(decoded_file)

            for row in reader:
                category_name = row.pop("category").strip()  # Get the category name from the row
                category = Category.objects.filter(name=category_name).first()
                if not category:
                    category = Category.objects.create(name=category_name)

                row["category"] = {
                    "id": category.id,
                    "name": category.name,
                }  # pass a dictionary to serializer

                serializer = ProductSerializer(data=row)
                if serializer.is_valid():
                    serializer.save()
                    products_created += 1
                else:
                    errors.append({"row": row, "errors": serializer.errors})

        except Exception as e:
            return Response(
                {"error": f"An error occurred while processing the file: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_data = {
            "products_created": products_created,
            "errors": errors,
        }

        # if some products were created and some were not(had errors)
        if products_created > 0 and errors:
            return Response(response_data, status=status.HTTP_207_MULTI_STATUS)
        elif products_created > 0:
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    viewset for listing and editing categories
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

    @action(detail=True, methods=["get"])
    def calculate_average_price(self, request, pk):
        """
        Custom action to calculate the average price of products in the given category
        and all its immediate and nested subcategories.
        """
        category = self.get_object()

        # Gets the current category and its subcategories (up to two levels deep)
        subcategories = Category.objects.filter(
            Q(id=category.id) | Q(parent=category) | Q(parent__parent=category)
        )

        # Gets all products under the current category and its subcategories
        products = Product.objects.filter(
            Q(category=category) | Q(category__parent=category) | Q(category__parent__parent=category)
        )

        if not products.exists():
            return Response(
                {"message": "No products found in this category or its subcategories."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Calculate the average price
        average_price = products.aggregate(avg_price=Avg("price"))["avg_price"]

        return Response(
            {
                "category": category.name,
                "average_price": average_price,
                "products_count": products.count(),
                "subcategory_count": subcategories.count() - 1,
            },
            status=status.HTTP_200_OK,
        )


class OrderViewSet(viewsets.ModelViewSet):
    """
    Viewset for listing and managing orders.
    """

    queryset = Order.objects.select_related("customer").prefetch_related("order_items__product").all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOrderOwnerOrAdminWithLimitedUpdate]

    def get_queryset(self):
        """Filter orders based on user role"""
        user = self.request.user
        if user.role == User.CUSTOMER:
            # Customers can only see the orders they created
            return Order.objects.filter(customer=user)

        # Admins can see all orders
        return Order.objects.all()


class CustomOIDCCallbackView(OIDCAuthenticationCallbackView):
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        # Ensure the user is authenticated
        user = request.user
        if user.is_authenticated:
            # Check if phone number is missing
            if not user.phone_number:
                return redirect("update_profile")

        return response


class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    # TODO add validation for phone number on view level, maybe just add user.clean() here, before user.save()
    def patch(self, request):
        user = request.user
        phone_number = request.data.get("phone_number")

        if not phone_number:
            return Response({"error": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Update user's phone number
        user.phone_number = phone_number
        user.save()

        return Response({"message": "Profile updated successfully."}, status=status.HTTP_200_OK)
