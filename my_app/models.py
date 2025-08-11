from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Country(models.Model):
    name=models.CharField(max_length=50,null=True,blank=True)
    status=models.CharField(max_length=50,null=True,blank=True)

    def __str__(self):
        return self.name
class Brand(models.Model):
    name=models.CharField(max_length=50,null=True,blank=True)
    image=models.ImageField(upload_to="media",max_length=100,blank=True,null=True)
    status=models.CharField(max_length=50,null=True,blank=True)
    def __str__(self):
        return self.name
class Category(models.Model):
    slug = models.SlugField(unique=True, blank=True, null=True)
    name=models.CharField(max_length=100,blank=True,null=True)
    image=models.ImageField(upload_to="media",null=True,blank=True)
    status=models.CharField(max_length=50,null=True,blank=True)
    def __str__(self):
        return self.name
 
class Product(models.Model):
    country=models.ForeignKey(Country,on_delete=models.CASCADE)
    brand=models.ForeignKey(Brand,on_delete=models.CASCADE,null=True,blank=True)
    category=models.ForeignKey(Category,on_delete=models.CASCADE,related_name='products')
    code=models.CharField(max_length=50,null=True,blank=True)
    name=models.CharField(max_length=100,null=True)
    detail=models.TextField()
    originalprice=models.IntegerField(null=True)
    ourprice=models.IntegerField(null=True)
    taxrate=models.IntegerField(null=True)
    taxamount=models.IntegerField(null=True)
    grosstotal=models.IntegerField(null=True)
    weight=models.IntegerField(null=True)
    openingstock=models.IntegerField(null=True)
    currentstock=models.IntegerField(null=True)
    image=models.ImageField(upload_to="media",null=True)
    status=models.CharField(max_length=50,null=True,blank=True)
    quantity=models.IntegerField(null=False,blank=False)
    createdat=models.DateField(auto_now_add=True)
    updatedat=models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Ensures one cart per user
    session_id = models.CharField(max_length=50, null=True, blank=True)  # Ensures one cart per guest session
    created_at = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.product.ourprice * self.quantity

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"
    class Meta:
        unique_together = ('user', 'session_id', 'product') 
    
class Wishlist(models.Model):   
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key=models.CharField(max_length=50,blank=True,null=True)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} - {self.product.name}" if self.user else f"Guest - {self.product.name}"
    
class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    address = models.TextField()
    mobile = models.CharField(max_length=15,null=True,blank=True)
    email = models.EmailField()
    state = models.CharField(max_length=50,null=True,blank=True)
    pincode=models.IntegerField(null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.address}"

class Order(models.Model):
    ORDER_STATUS_CHOICES=[
        ('Pending','Pending'),
        ('Processing','Processing'),
        ('Out For Delivery','Out For Delivery'),
        ('Delivered','Delivered'),
        ('Cancelled','Cancelled')
        ]
    user=models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True)
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at=models.DateTimeField(auto_now_add=True)
    payment_method=models.CharField(max_length=50)
    payment_status = models.CharField(max_length=100)
    order_status = models.CharField(max_length=100,choices=ORDER_STATUS_CHOICES,default='Pending')           


    def __str__(self):
        return f"Order {self.id} - {self.order_status}"  
class DeliveryStaff(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    name=models.CharField(max_length=100,null=True)
    number=models.CharField(max_length=15,null=True,blank=True)
    is_active=models.BooleanField(default=True)
    def __str__(self):
        return self.name

class OrderItem(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name="items")
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField(default=1)
    price=models.DecimalField(max_digits=10,decimal_places=2)
    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"
    


class Assigned_Order(models.Model):
    delivery_staff = models.ForeignKey(DeliveryStaff, on_delete=models.CASCADE,null=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE,null=True)
    created_at=models.DateTimeField(auto_now_add=True,null=True)
