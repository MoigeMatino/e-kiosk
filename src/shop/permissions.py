from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.contrib.auth import get_user_model

User = get_user_model()

class IsAdminOrReadOnly(BasePermission):
    """Allow read-only access for everyone, but only admins can modify resources."""

    def has_permission(self, request, view):
        # Allow read-only access for everyone
        if request.method in SAFE_METHODS:
            return True
        
        # Only authenticated admins can modify resources
        return request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == User.ADMIN

    def has_object_permission(self, request, view, obj):
        # Ensure the user is authenticated and has a role attribute before checking
        if request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == User.ADMIN:
            return True
        
        # Deny all other modifications
        return False

class IsAdminOrCustomerCreateOnly(BasePermission):
    """
    Custom permission to allow:
    - Admins to perform any action.
    - Customers to create orders and view their own orders, but not update or delete them.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if request.user.role == User.ADMIN:
            return True
        if request.user.role == User.CUSTOMER and request.method == "POST":
            return True
        return False
    
    def has_object_permission(self, request, view, obj):
        # Customers can only access their own orders
        if request.user.role == User.CUSTOMER:
            return obj.customer == request.user

        # Admins can view and partially update (PATCH) orders, but not delete or fully update (PUT)
        if request.user.role == User.ADMIN:
            if request.method == 'DELETE' or request.method == 'PUT':
                return False  # Admins cannot delete or fully update orders
            return True  # Admins can view and partially update orders (PATCH)

        return False
