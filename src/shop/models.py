from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.db import models, transaction
from django.core.validators import validate_email, EmailValidator
from django.core.exceptions import ValidationError

class CustomUserManager(BaseUserManager):  
    def create_user(self, email, password=None, **extra_fields):  
        if not email:  
            raise ValueError('The Email field must be set')  
        email = self.normalize_email(email)  
        user = self.model(email=email, **extra_fields)  
        if password:  
            user.set_password(password)  
        user.save(using=self._db)  
        return user  

    def create_superuser(self, email, password=None, **extra_fields):  
        extra_fields.setdefault('is_staff', True)  
        extra_fields.setdefault('is_superuser', True)  
        extra_fields.setdefault('is_active', True)  
        extra_fields.setdefault('role', 'admin')  # Set default role for superuser  

        if extra_fields.get('is_staff') is not True:  
            raise ValueError('Superuser must have is_staff=True.')  
        if extra_fields.get('is_superuser') is not True:  
            raise ValueError('Superuser must have is_superuser=True.')  

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    CUSTOMER = 'customer'
    ADMIN = 'admin'

    ROLE_CHOICES = [
        (CUSTOMER, 'Customer'),
        (ADMIN, 'Admin'),
    ]
    
    username = None
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True, null=True) #TODO: maybe add format restrictions using regex
    openid_sub = models.CharField(max_length=255, unique=True, blank=True, null=True)  # For OIDC customers
    email = models.EmailField(unique=True, validators=[EmailValidator(message="Invalid email format")])
    
    USERNAME_FIELD = 'email'  
    REQUIRED_FIELDS = ['role']
    
    objects = CustomUserManager()

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
        return self.email
    
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
    # TODO: override save() method to call clean()?
    def clean(self):
        if self.discount_price and self.discount_price >= self.price:
            raise ValidationError("Discount price must be lower than the regular price.")
    
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
    
    def place_order(self, items):
        """
        verifies stock for all items before placing the order
        It checks stock availability and moves the order to PENDING.
        :param items: List of tuples [(product_id, quantity), ...]
        :return: True if order is successfully placed, False if stock is insufficient.
        """
        total = 0
        # Fetch all product instances in one query
        product_ids = [item[0] for item in items]
        
        with transaction.atomic():
            products = Product.objects.filter(id__in=product_ids).select_for_update()
            product_map = {product.id: product for product in products}
            
            # Calculate total price on order creation
            for product_id, quantity in items:
                product = product_map.get(product_id)
                total += product.get_current_price() * quantity 

            # Create order items
            for product_id, quantity in items:
                product = product_map[product_id]
                OrderItem.objects.create(
                    order=self,
                    product=product,
                    quantity=quantity,
                    price_at_time_of_order=product.get_current_price()
                )
                
            # Update total_price and save the order
            self.total_price = total
            
            # Mark order as pending
            self.status = self.PENDING
            self.save()

            # TODO: Notify admin about the new order
            # self.notify_admin()
            
            # TODO: Notify customer that their order has been placed successfully
            # self.notify_customer_order_placed()
        
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_at_time_of_order = models.DecimalField(max_digits=10, decimal_places=2)  # Capture price at time of purchase
    
    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
# TODO: clean up str method
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification to {self.user.username}: {self.message[:20]}..."
    
    def __str__(self):
        user_identifier = self.user.phone_number if self.user.phone_number else self.user.email
        return f"Notification for {user_identifier}: {self.message[:20]}..."

        
