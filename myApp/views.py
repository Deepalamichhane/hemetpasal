from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from django.shortcuts import render
from .models import Product, TeamMember, AboutPageStats, ContactMessage, Cart, CartItem, Wishlist, WishlistItem

def index(request):
    featured_products = Product.objects.filter(is_featured=True)[:4]  # Get 4 featured products
    new_arrivals = Product.objects.order_by('-created_at')[:4]  # Get 4 newest products
    
    context = {
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
    }
    return render(request, 'index.html', context)

def about(request):
    stats = AboutPageStats.objects.first()
    if not stats:
        stats = AboutPageStats.objects.create()
        
    team = TeamMember.objects.all()
    
    context = {
        'stats': stats,
        'team': team
    }
    return render(request, 'about.html', context)

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Create contact message
        ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        
        messages.success(request, 'Your message has been sent. We will get back to you soon!')
        return redirect('contact')
    
    return render(request, 'contact.html')

def products(request):
    # Get all categories for filtering
    categories = Product.CATEGORY_CHOICES
    
    # Get filter parameter
    category = request.GET.get('category')
    
    # Filter products based on category if provided
    if category:
        products_list = Product.objects.filter(category=category)
    else:
        products_list = Product.objects.all()
    
    context = {
        'products': products_list,
        'categories': categories,
        'selected_category': category
    }
    
    return render(request, 'product.html', context)

def product_detail(request, product_id):
    # Get the product or return 404
    product = get_object_or_404(Product, id=product_id)
    
    # Get related products in the same category
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products
    }
    
    return render(request, 'productdetails.html', context)

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = auth.authenticate(username=username, password=password)
        
        if user is not None:
            auth.login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('login')
    
    return render(request, 'login.html')

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        # Check if passwords match
        if password != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('signup')
        
        # Check if username exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('signup')
        
        # Check if email exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('signup')
        
        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        
        # Create cart and wishlist for the user
        Cart.objects.create(user=user)
        Wishlist.objects.create(user=user)
        
        messages.success(request, 'Account created successfully. Please log in.')
        return redirect('login')
        
    return render(request, 'signup.html')

@login_required
def logout(request):
    auth.logout(request)
    return redirect('index')

@login_required
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    buy_now = request.POST.get('buy_now', False)
    redirect_after = request.POST.get('redirect', 'true').lower() != 'false'
    
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            quantity = 1
    except ValueError:
        quantity = 1
    
    # Get or create user's cart
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Try to get existing cart item
    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        if not buy_now:
            # If product already exists in cart and not buy_now, increase quantity
            cart_item.quantity += quantity
            cart_item.save()
        else:
            # For buy_now, just store the ID in session and redirect
            # Don't modify the cart for buy_now
            request.session['buy_now_product_id'] = product_id
            request.session['buy_now_quantity'] = quantity
            messages.success(request, f"Proceeding to checkout with {product.name}")
            return redirect('checkout')
    except CartItem.DoesNotExist:
        if not buy_now:
            # Only create a cart item if NOT buy_now
            cart_item = CartItem(
                cart=cart,
                product=product,
                quantity=quantity,
                extra_price=0
            )
            cart_item.save()
        else:
            # For buy_now, just store the ID in session and redirect
            request.session['buy_now_product_id'] = product_id
            request.session['buy_now_quantity'] = quantity
            messages.success(request, f"Proceeding to checkout with {product.name}")
            return redirect('checkout')
    
    # If AJAX request or redirect=false, return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or not redirect_after:
        return JsonResponse({
            'success': True,
            'message': f"{product.name} added to cart",
            'cart_count': cart.get_cart_items_count
        })
    
    if buy_now:
        # Redirect to checkout page if buy_now is true
        request.session['buy_now_product_id'] = product_id
        request.session['buy_now_quantity'] = quantity
        messages.success(request, f"Proceeding to checkout with {product.name}")
        return redirect('checkout')
    else:
        messages.success(request, f"{product.name} added to cart")
        # Clear buy_now flag if exists
        if 'buy_now_product_id' in request.session:
            del request.session['buy_now_product_id']
        if 'buy_now_quantity' in request.session:
            del request.session['buy_now_quantity']
        return redirect('cart')

@login_required
@require_POST
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Get or create user's wishlist
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    # Check if product is already in wishlist
    wishlist_item, created = WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)
    
    # If AJAX request return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"{product.name} added to wishlist",
            'created': created,
            'wishlist_count': wishlist.get_wishlist_count
        })
    
    if created:
        messages.success(request, f"{product.name} added to wishlist")
    else:
        messages.info(request, f"{product.name} is already in your wishlist")
    
    return redirect('wishlist')

@login_required
def cart(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.cartitem_set.all()
    except Cart.DoesNotExist:
        cart = None
        cart_items = []
    
    context = {
        'cart': cart,
        'cart_items': cart_items
    }
    
    return render(request, 'cart.html', context)

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    
    messages.success(request, f"{cart_item.product.name} removed from cart")
    return redirect('cart')

@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        next_page = request.POST.get('next', '')
        
        if quantity > 0:
            cart_item.quantity = quantity
            # Make sure extra_price is kept
            if not hasattr(cart_item, 'extra_price') or cart_item.extra_price is None:
                cart_item.extra_price = 0
            cart_item.save()
        else:
            cart_item.delete()
    
        if next_page == 'checkout':
            return redirect('checkout')
            
    return redirect('cart')

@login_required
def wishlist(request):
    try:
        wishlist = Wishlist.objects.get(user=request.user)
        wishlist_items = wishlist.wishlistitem_set.all()
    except Wishlist.DoesNotExist:
        wishlist = None
        wishlist_items = []
    
    context = {
        'wishlist': wishlist,
        'wishlist_items': wishlist_items
    }
    
    return render(request, 'wishlist.html', context)

@login_required
def remove_from_wishlist(request, item_id):
    wishlist_item = get_object_or_404(WishlistItem, id=item_id, wishlist__user=request.user)
    wishlist_item.delete()
    
    messages.success(request, f"{wishlist_item.product.name} removed from wishlist")
    return redirect('wishlist')

@login_required
def move_to_cart(request, item_id):
    wishlist_item = get_object_or_404(WishlistItem, id=item_id, wishlist__user=request.user)
    product = wishlist_item.product
    
    # Get or create user's cart
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Try to get existing cart item
    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        # If product already exists in cart, increase quantity
        cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        # Create new cart item with all required fields explicitly set
        cart_item = CartItem(
            cart=cart,
            product=product,
            quantity=1,
            extra_price=0
        )
        cart_item.save()
    
    # Remove from wishlist
    wishlist_item.delete()
    
    messages.success(request, f"{product.name} moved to cart")
    return redirect('cart')

@login_required
def checkout(request):
    # Check if we're in buy_now mode
    buy_now_product_id = request.session.get('buy_now_product_id')
    
    if buy_now_product_id:
        # We're in buy_now mode, only show the selected product
        try:
            # Get the product
            product = get_object_or_404(Product, id=buy_now_product_id)
            quantity = request.session.get('buy_now_quantity', 1)
            
            # Create a cart item just for display (not saved to DB)
            class SingleProductItem:
                def __init__(self, product, quantity):
                    self.product = product
                    self.quantity = quantity
                    self.id = None  # No DB ID since it's not stored
                
                def get_item_total(self):
                    if self.product.discount_price:
                        return self.product.get_discounted_price * self.quantity
                    return self.product.price * self.quantity
            
            # Create cart items list with just this product
            cart_item = SingleProductItem(product, quantity)
            
            # Calculate totals
            subtotal = cart_item.get_item_total()
            shipping = 50  # Example shipping cost
            total = subtotal + shipping
            
            context = {
                'single_product': product,
                'quantity': quantity,
                'subtotal': subtotal,
                'shipping': shipping, 
                'total': total,
                'is_buy_now': True
            }
            
            if request.method == 'POST':
                # Process buy now checkout
                # In a real app, this would connect to payment processing
                messages.success(request, "Your order has been placed successfully!")
                # Clear buy_now flags
                if 'buy_now_product_id' in request.session:
                    del request.session['buy_now_product_id']
                if 'buy_now_quantity' in request.session:
                    del request.session['buy_now_quantity']
                return redirect('index')
            
            return render(request, 'checkout.html', context)
            
        except (Product.DoesNotExist, ValueError):
            # If product doesn't exist, clear buy_now flag and proceed to normal checkout
            if 'buy_now_product_id' in request.session:
                del request.session['buy_now_product_id']
            if 'buy_now_quantity' in request.session:
                del request.session['buy_now_quantity']
    
    # Normal checkout process with cart
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.cartitem_set.all().order_by('created_at')
        
        if not cart_items:
            messages.error(request, "Your cart is empty. Please add items to checkout.")
            return redirect('products')
            
    except Cart.DoesNotExist:
        cart = None
        cart_items = []
        messages.error(request, "Your cart is empty. Please add items to checkout.")
        return redirect('products')
    
    # Calculate totals
    subtotal = cart.get_cart_total
    shipping = 50  # Example shipping cost
    total = subtotal + shipping
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
        'is_buy_now': False
    }
    
    if request.method == 'POST':
        # Process checkout (this would connect to a payment gateway in a real app)
        # For demonstration, just clear the cart and show success
        cart.cartitem_set.all().delete()
        messages.success(request, "Your order has been placed successfully!")
        return redirect('index')
    
    return render(request, 'checkout.html', context)

