from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import validate_email, EmailValidator
from django.core.exceptions import ValidationError

class User(AbstractUser):
    CUSTOMER = 'customer'
    ADMIN = 'admin'

    ROLE_CHOICES = [
        (CUSTOMER, 'Customer'),
        (ADMIN, 'Admin'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True, null=True) #? character vs integer field
    openid_sub = models.CharField(max_length=255, unique=True, blank=True, null=True)  # For OIDC customers
    email = models.EmailField(unique=True, validators=[EmailValidator(message="Invalid email format")])

    def validate_email_format(self):
        """Ensure the email follows a standard format"""
        try:
            validate_email(self.email)
        except ValidationError as e:
            raise ValidationError({"email": "Invalid email format"}) from e
        
    def clean(self):
        super().clean()
        self.validate_email_format()        
    
    def is_admin(self):
        return self.role == self.ADMIN

    def is_customer(self):
        return self.role == self.CUSTOMER

    def __str__(self):
        return self.username
    
class Category(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')

    def __str__(self):
        return self.name
    
class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) # to account for price changes in case of discounts
    
    def is_in_stock(self, quantity):
        """
        Check if the requested quantity is available in stock.
        """
        return self.stock >= quantity
    
    def get_current_price(self):
        """
        In the case of price changes:
        Returns the discounted price if available, else the regular price
        """
        return self.discount_price if self.discount_price else self.price

    def __str__(self):
        return self.name
    
class Order(models.Model):
    PENDING = 'pending'
    COMPLETED = 'completed'
    CANCELED = 'canceled'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
        (CANCELED, 'Canceled'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_at_time_of_order = models.DecimalField(max_digits=10, decimal_places=2)  # Capture price at time of purchase
    

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification to {self.user.username}: {self.message[:20]}..."
    
    def __str__(self):
        user_identifier = self.user.phone_number if self.user.phone_number else self.user.email
        return f"Notification for {user_identifier}: {self.message[:20]}..."

        
