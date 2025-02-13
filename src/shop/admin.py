from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _  # For i18n

from .models import Category, Notification, Order, OrderItem, Product, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "phone_number", "role", "is_active")
    search_fields = ("email", "phone_number")
    list_filter = ("role", "is_active")

    fieldsets = (
        (None, {"fields": ("email", "openid_sub")}),
        (_("Personal info"), {"fields": ("phone_number",)}),
        (
            _("Permissions"),
            {"fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "phone_number",
                    "role",
                    "openid_sub",
                    "is_active",
                    "is_staff",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    ordering = ("email",)

    #  to handle superuser permissions
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser

        if not is_superuser:
            form.base_fields["is_superuser"].disabled = True

        return form

    def save_model(self, request, obj, form, change):
        if not change:  # Only for new users
            # so that no password is required for the user to log in(because customers are using oidc)
            obj.set_unusable_password()
        super().save_model(request, obj, form, change)


admin.site.register(Order)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(OrderItem)
admin.site.register(Notification)
