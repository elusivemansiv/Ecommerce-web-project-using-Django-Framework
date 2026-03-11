from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Order, OrderItem
from .serializers import OrderSerializer
from products.models import ProductVariant

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['ADMIN', 'STAFF']:
            return Order.objects.all()
        return Order.objects.filter(customer=user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def confirm(self, request, pk=None):
        order = self.get_object()
        
        if request.user.role not in ['ADMIN', 'STAFF']:
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
            
        if order.order_status != 'Pending':
            return Response({"detail": "Order can only be confirmed if it is pending."}, status=status.HTTP_400_BAD_REQUEST)
            
        order.order_status = 'Confirmed'
        order.save()
            
        return Response({"status": "Order confirmed. Stock was already reduced at creation."})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def cancel(self, request, pk=None):
        order = self.get_object()
        
        if request.user.role not in ['ADMIN', 'STAFF']:
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
            
        if order.order_status == 'Canceled':
            return Response({"detail": "Order is already canceled."}, status=status.HTTP_400_BAD_REQUEST)
            
        order.order_status = 'Canceled'
        order.save()
            
        return Response({"status": "Order status set to Canceled. Stock has been restored."})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def return_order(self, request, pk=None):
        order = self.get_object()
        
        if request.user.role not in ['ADMIN', 'STAFF']:
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
            
        if order.order_status == 'Returned':
            return Response({"detail": "Order is already marked as returned."}, status=status.HTTP_400_BAD_REQUEST)
            
        order.order_status = 'Returned'
        order.save()
            
        return Response({"status": "Order status set to Returned. Stock has been restored."})

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def update_payment(self, request, pk=None):
        order = self.get_object()
        
        if request.user.role not in ['ADMIN', 'STAFF']:
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
            
        if not hasattr(order, 'payment'):
            return Response({"detail": "No payment record found for this order."}, status=status.HTTP_404_NOT_FOUND)
            
        payment = order.payment
        payment_status = request.data.get('payment_status')
        transaction_id = request.data.get('transaction_id')
        
        if payment_status:
            payment.payment_status = payment_status
        if transaction_id:
            payment.transaction_id = transaction_id
            
        if payment_status == 'Paid' and not payment.paid_at:
            from django.utils import timezone
            payment.paid_at = timezone.now()
            
        payment.save()
        return Response({"status": "Payment updated successfully."})
