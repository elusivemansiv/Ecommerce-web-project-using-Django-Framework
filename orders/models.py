from django.db import models
from users.models import User
from products.models import ProductVariant

class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Canceled', 'Canceled'),
        ('Returned', 'Returned'),
    )
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    shipping_name = models.CharField(max_length=255, default='', help_text="Name of the person receiving the order")
    shipping_address = models.TextField(default='', help_text="Address where the order should be delivered")
    shipping_phone = models.CharField(max_length=20, default='', help_text="Phone number for delivery contact")
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_method = models.CharField(max_length=50) # e.g., COD, bKash
    order_status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_orders', help_text="Admin who created the order")

    def __str__(self):
        return f"Order #{self.id} by {self.customer.username}"

    def save(self, *args, **kwargs):
        if self.pk:
            old_order = Order.objects.get(pk=self.pk)
            # If status changes from a non-restored status to Canceled or Returned, restore stock
            restored_statuses = ['Canceled', 'Returned']
            active_statuses = ['Pending', 'Confirmed', 'Shipped', 'Delivered']
            
            if old_order.order_status in active_statuses and self.order_status in restored_statuses:
                from django.db import transaction
                with transaction.atomic():
                    for item in self.items.all():
                        if item.product_variant:
                            item.product_variant.stock_quantity += item.quantity
                            item.product_variant.save()
            
            # If status changes back from restored to active, decrease stock again (to handle accidental cancel)
            if old_order.order_status in restored_statuses and self.order_status in active_statuses:
                 from django.db import transaction
                 with transaction.atomic():
                    for item in self.items.all():
                        if item.product_variant:
                             # Check if enough stock (since it was restored)
                             # but here it's more complex if stock changed in between.
                             # For now, let's keep it simple as per request (restore for cancelled/returned)
                             item.product_variant.stock_quantity -= item.quantity
                             item.product_variant.save()
                             
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product_variant} for Order #{self.order.id}"

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
    )
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    payment_type = models.CharField(max_length=50, choices=(('COD', 'Cash On Delivery'), ('bKash', 'bKash'), ('Card', 'Card')))
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Payment for Order #{self.order.id} - {self.payment_status}"
