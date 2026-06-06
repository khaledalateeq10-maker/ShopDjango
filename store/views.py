from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Product, Category, Order, OrderItem

def product_list(request):
    products = Product.objects.filter(available=True)
    categories = Category.objects.all()
    category_slug = request.GET.get('category')
    query = request.GET.get('q')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    if query:
        products = products.filter(name__icontains=query)
    return render(request, 'store/product_list.html', {
        'products': products,
        'categories': categories,
        'query': query,
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    return render(request, 'store/product_detail.html', {'product': product})

def cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        subtotal = product.price * quantity
        total += subtotal
        cart_items.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})
    return render(request, 'store/cart.html', {'cart_items': cart_items, 'total': total})

def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_id = str(product_id)
    cart[product_id] = cart.get(product_id, 0) + 1
    request.session['cart'] = cart
    return redirect('cart')

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_id = str(product_id)
    if product_id in cart:
        del cart[product_id]
    request.session['cart'] = cart
    return redirect('cart')

def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('cart')
    if request.method == 'POST':
        order = Order.objects.create(
            first_name=request.POST['first_name'],
            last_name=request.POST['last_name'],
            email=request.POST['email'],
            address=request.POST['address'],
        )
        total = 0
        for product_id, quantity in cart.items():
            product = get_object_or_404(Product, id=product_id)
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price,
            )
            total += product.price * quantity
        order.total_price = total
        order.save()
        request.session['cart'] = {}
        return redirect('order_success')
    return render(request, 'store/checkout.html')

def order_success(request):
    return render(request, 'store/order_success.html')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('product_list')
    else:
        form = UserCreationForm()
    return render(request, 'store/register.html', {'form': form})

@login_required
def profile(request):
    orders = Order.objects.filter(email=request.user.email).order_by('-created')
    return render(request, 'store/profile.html', {'orders': orders})