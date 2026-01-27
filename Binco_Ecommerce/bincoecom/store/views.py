from django.shortcuts import render, get_object_or_404, redirect
from .models import Product

def home(request):
    products = Product.objects.all()
    return render(request, 'store/home.html', {'products': products})


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'store/product_detail.html', {'product': product})

def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        cart[str(product_id)] += 1
    else:
        cart[str(product_id)] = 1

    request.session['cart'] = cart

    return redirect('cart')

def cart_view(request):
    cart = request.session.get('cart', {})
    products = []
    total = 0

    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        subtotal = product.price * quantity
        total += subtotal

        products.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal
        })

    context = {
        'cart_items': products,
        'total': total
    }

    return render(request, 'store/cart.html', context)