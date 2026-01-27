from django.urls import path
from .views import home, product_detail
from .import views


urlpatterns = [
    path('', home, name='home'),
    path('product/<int:product_id>/', product_detail, name='product_detail'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
]