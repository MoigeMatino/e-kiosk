from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.contrib.auth import get_user_model

User = get_user_model()

class IsAdminOrReadOnly(BasePermission):
    """Allow read-only access for everyone, but only admins can modify orders"""

    def has_permission(self, request, view):
        # Allow read-only access for everyone
        if request.method in SAFE_METHODS:
            return True
        
        # Only authenticated admins can modify
        return request.user.is_authenticated and request.user.role == User.ADMIN

    def has_object_permission(self, request, view, obj):
        # Allow admins to modify orders by default
        if request.user.role == User.ADMIN:
            return True
        
        # Deny all other modifications
        return False