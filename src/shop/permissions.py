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
