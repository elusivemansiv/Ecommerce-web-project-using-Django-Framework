from rest_framework import serializers
from .models import Order, OrderItem, Payment
from products.models import ProductVariant

class OrderItemSerializer(serializers.ModelSerializer):
    product_variant_id = serializers.IntegerField(write_only=True)
    product_name = serializers.CharField(source='product_variant.product.name', read_only=True)
    product_image = serializers.CharField(source='product_variant.product.image_url', read_only=True)
    amount = serializers.CharField(source='product_variant.amount', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product_variant_id', 'product_name', 'product_image', 'amount', 'quantity', 'unit_price']
        read_only_fields = ['unit_price']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'payment_type', 'payment_status', 'transaction_id', 'paid_at']
        read_only_fields = ['payment_status', 'paid_at']

    def validate_payment_type(self, value):
        if value != 'COD':
            raise serializers.ValidationError("Currently only Cash on Delivery is processable. bKash and Card will be implemented later.")
        return value

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, min_length=1)
    payment = PaymentSerializer()

    class Meta:
        model = Order
        fields = ['id', 'customer', 'shipping_name', 'shipping_address', 'shipping_phone', 
                  'order_date', 'total_amount', 'payment_method', 'order_status', 
                  'created_by', 'items', 'payment']
        read_only_fields = ['customer', 'order_date', 'total_amount', 'order_status', 
                            'created_by', 'payment_method']

    def validate(self, data):
        # Requirements: Name, Address, Phone must be required
        if not data.get('shipping_name'):
            raise serializers.ValidationError({"shipping_name": "Name is required for checkout."})
        if not data.get('shipping_address'):
            raise serializers.ValidationError({"shipping_address": "Address is required for checkout."})
        if not data.get('shipping_phone'):
            raise serializers.ValidationError({"shipping_phone": "Phone number is required for checkout."})
        return data

    def create(self, validated_data):
        from django.db import transaction
        
        items_data = validated_data.pop('items')
        payment_data = validated_data.pop('payment')
        
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        
        # Determine customer (if admin creating for customer vs customer creating)
        customer_id = self.initial_data.get('customer')
        if user and user.role in ['ADMIN', 'STAFF'] and customer_id:
            from users.models import User
            customer = User.objects.get(id=customer_id)
            created_by = user
        elif user:
            customer = user
            created_by = None
        else:
            # Fallback for cases without request context (e.g. some internal tests/scripts)
            if customer_id:
                from users.models import User
                customer = User.objects.get(id=customer_id)
            else:
                raise serializers.ValidationError("Customer is required.")
            created_by = None
            
        validated_data['customer'] = customer
        validated_data['created_by'] = created_by
        validated_data['payment_method'] = payment_data.get('payment_type')
        
        with transaction.atomic():
            order = Order.objects.create(**validated_data)
            
            total_amount = 0
            for item_data in items_data:
                variant_id = item_data.pop('product_variant_id')
                variant = ProductVariant.objects.get(id=variant_id)
                quantity = item_data.get('quantity', 1)
                
                # STOCK MANAGEMENT: Decrease stock when order is submitted
                if variant.stock_quantity < quantity:
                    raise serializers.ValidationError({
                        "items": f"Not enough stock for {variant.product.name} ({variant.amount}). Available: {variant.stock_quantity}"
                    })
                
                variant.stock_quantity -= quantity
                variant.save()
                
                unit_price = variant.price
                OrderItem.objects.create(
                    order=order,
                    product_variant=variant,
                    quantity=quantity,
                    unit_price=unit_price
                )
                total_amount += (unit_price * quantity)
                
            order.total_amount = total_amount
            order.save()
            
            # Create Payment record
            Payment.objects.create(order=order, **payment_data)
            
        return order
