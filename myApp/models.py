from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('full_face', 'Full Face Helmet'),
        ('half_face', 'Half Face Helmet'),
        ('modular', 'Modular Helmet'),
        ('open_face', 'Open Face Helmet'),
        ('sports', 'Sports Helmet'),
        ('motorcross', 'Motocross Helmet'),
        ('visor', 'Helmet Visor'),
        ('accessories', 'Helmet Accessories'),
        ('racing', 'Racing Helmet'),
        ('cruiser', 'Cruiser Helmet'),
        ('scooter', 'Scooter Helmet'),
        ('kids', 'Kids Helmet'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image = models.FileField(upload_to='products/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url
    
    @property
    def get_discounted_price(self):
        if self.discount_price:
            return round(float(self.price) - (float(self.price) * (float(self.discount_price) / 100)), 2)
        return self.price
    
    def get_discount_percentage(self):
        if self.discount_price:
            return int(self.discount_price)
        return 0

class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    bio = models.TextField()
    image = models.ImageField(upload_to='team/')
    facebook = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        
    def __str__(self):
        return self.name

class AboutPageStats(models.Model):
    customers = models.IntegerField(default=50000)
    products = models.IntegerField(default=100)
    years = models.IntegerField(default=7)
    awards = models.IntegerField(default=25)
    
    class Meta:
        verbose_name = 'About Page Statistics'
        verbose_name_plural = 'About Page Statistics'
        
    def __str__(self):
        return 'About Page Statistics'

class ContactMessage(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
    
    def __str__(self):
        return f"{self.name} - {self.subject}"

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cart for {self.user.username}"
    
    @property
    def get_cart_total(self):
        cart_items = self.cartitem_set.all()
        total = sum(item.get_total for item in cart_items)
        return total
        
    @property
    def get_cart_items_count(self):
        cart_items = self.cartitem_set.all()
        return cart_items.count()

class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    extra_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.quantity} of {self.product.name}"
    
    @property
    def get_total(self):
        if self.product.discount_price:
            return self.quantity * self.product.get_discounted_price + float(self.extra_price)
        return self.quantity * self.product.price + float(self.extra_price)

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Wishlist for {self.user.username}"
    
    @property
    def get_wishlist_count(self):
        return self.wishlistitem_set.count()

class WishlistItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.product.name
    
    class Meta:
        unique_together = ('wishlist', 'product')