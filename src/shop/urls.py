from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    CustomOIDCCallbackView,
    OrderViewSet,
    ProductViewSet,
    UpdateProfileView,
)

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"orders", OrderViewSet, basename="order")

urlpatterns = [
    path("", include(router.urls)),
    path("oidc/callback/", CustomOIDCCallbackView.as_view(), name="oidc_callback"),
    path("oidc/", include("mozilla_django_oidc.urls")),
    path("update-profile/", UpdateProfileView.as_view(), name="update_profile"),
]
