from django.db import models
from django.contrib.auth.hashers import make_password
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone

# Create your models here.
class Customer(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    password = models.CharField(max_length=128)  # Store hashed passwords
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
    
    def save(self, *args, **kwargs):
        # Hash password if it's not already hashed
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['email']),
        ]


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    image = models.ImageField(upload_to='books/', blank=True, null=True)
    published_date = models.DateField()
    stock_quantity = models.PositiveIntegerField(default=0)
    isbn = models.CharField(max_length=13, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    @property
    def in_stock(self):
        return self.stock_quantity > 0
    
    class Meta:
        ordering = ['title']
        indexes = [
            models.Index(fields=['isbn']),
            models.Index(fields=['author']),
        ]


class Testimonial(models.Model):
    author = models.CharField(max_length=100)
    content = models.TextField()
    rating = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MinValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f'Testimonial by {self.author}'
    
    class Meta:
        ordering = ['-created_at']


class Cart(models.Model):
    customer = models.OneToOneField(
        Customer, 
        on_delete=models.CASCADE,
        related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'Cart for {self.customer.full_name()}'
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())
    
    def clear(self):
        """Remove all items from the cart"""
        self.items.all().delete()


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart, 
        related_name='items', 
        on_delete=models.CASCADE
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    added_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.quantity} x {self.book.title}'
    
    @property
    def total_price(self):
        return Decimal(str(self.quantity)) * self.book.price
    
    class Meta:
        unique_together = ['cart', 'book']
        ordering = ['-added_at']


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.CASCADE,
        related_name='orders'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0
    )
    shipping_address = models.TextField(blank=True)
    billing_address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f'Order #{self.id} - {self.customer.full_name()}'
    
    def calculate_total(self):
        """Calculate and return the total price of all items"""
        total = sum(item.total_price for item in self.items.all())
        return total
    
    def save(self, *args, **kwargs):
        if self.pk:  # Only calculate if the order already exists
            self.total_price = self.calculate_total()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, 
        related_name='items', 
        on_delete=models.CASCADE
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Price at the time of purchase"
    )
    
    def __str__(self):
        return f'{self.quantity} x {self.book.title} (Order #{self.order.id})'
    
    @property
    def total_price(self):
        return Decimal(str(self.quantity)) * self.price
    
    def save(self, *args, **kwargs):
        # Set the price from the book if not already set
        if not self.price:
            self.price = self.book.price
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['id']

class Merchandise(models.Model):
    CATEGORY_CHOICES = [
        ('clothing', 'Clothing'),
        ('accessories', 'Accessories'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    image = models.ImageField(upload_to='merchandise/')

    # Optional: for clothing sizes
    has_sizes = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} ({self.category})"

class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)   # prevent duplicates
    date_subscribed = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.email
