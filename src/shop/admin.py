from django.contrib import admin

from .models import Order, Category, Product, OrderItem, Notification, User

@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'phone_number', 'role', 'is_active')
    search_fields = ('email', 'phone_number')
    list_filter = ('role', 'is_active')

admin.site.register(Order)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(OrderItem)
admin.site.register(Notification)
