from django.shortcuts import render, redirect
from django.contrib import messages, admin
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .models import Testimonial, Order, Book, Merchandise, NewsletterSubscriber, Cart, CartItem, Customer # assuming you track purchases via an Order model
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
import stripe
from django.conf import settings
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# views.py
def auth_view(request):
    if request.method == "POST":
        form_type = request.POST.get("form_type")

        # LOGIN
        if form_type == "login":
            email = request.POST.get("email")
            password = request.POST.get("password")

            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")  # feedback message
                return redirect("bookstore:index")
            else:
                messages.error(request, "Invalid login credentials")
                return redirect("bookstore:auth")

        # REGISTER
        elif form_type == "register":
            name = request.POST.get("name")
            email = request.POST.get("email")
            password = request.POST.get("password")
            confirm = request.POST.get("password_confirm")

            if password != confirm:
                messages.error(request, "Passwords do not match")
                return redirect("bookstore:auth")

            if User.objects.filter(email=email).exists():
                messages.error(request, "Email already exists")
                return redirect("bookstore:auth")

            username = email.split("@")[0]
            user = User.objects.create_user(username=username, email=email, password=password)
            user.first_name = name
            user.save()
            messages.success(request, "Account created successfully! Please login.")
            return redirect("bookstore:auth")

    # 👇 correct render
    return render(request, "bookstore/auth.html")



def logout_view(request):
    logout(request)
    return redirect("bookstore:auth")

def auth(request):
    return render(request, "bookstore/auth.html")


# Define views for the bookstore application
def index(request):
    return render(request, 'bookstore/index.html')

@login_required
def submit_testimonial(request):
    user = request.user
    has_purchased = Order.objects.filter(user=user, status="completed").exists()

    if not has_purchased:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"error": "You must purchase a book before leaving a testimonial."}, status=403)
        return redirect("bookstore:home")  # fallback

    if request.method == "POST":
        content = request.POST.get("content")
        if content:
            testimonial = Testimonial.objects.create(
                author=user.get_full_name() or user.username,
                content=content
            )
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({
                    "author": testimonial.author,
                    "content": testimonial.content
                })
            return redirect("bookstore:home")

    return JsonResponse({"error": "Invalid request"}, status=400)


def books(request):
    all_books = Book.objects.all()
    return render(request, 'bookstore/books.html', {'books': all_books})

def shop(request):
    return books(request)   # reuse books view


def book_detail(request, book_id):
    # Logic to get book details by book_id
    return render(request, 'bookstore/book_detail.html', {'book_id': book_id})

def merchandise_view(request):
    merch_clothing_items = Merchandise.objects.filter(category="clothing")
    merch_accessories = Merchandise.objects.filter(category="accessories")

    return render(request, "bookstore/merch.html", {
        "merch_clothing_items": merch_clothing_items,
        "merch_accessories": merch_accessories,
    })

def about(request):
    return render(request, 'bookstore/about.html')

def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        subject = f"New contact form message from {name}"
        body = f"""
        You have received a new message from your website contact form.

        Name: {name}
        Email: {email}

        Message:
        {message}
        """

        try:
            send_mail(
                subject,
                body,
                email,  # from email (the sender)
                ['your_email@gmail.com'],  # to email (your inbox)
                fail_silently=False,
            )
            messages.success(request, "Your message was sent successfully!")
        except Exception as e:
            messages.error(request, f"Message not sent. Error: {e}")

        return redirect("bookstore:contact")

    return render(request, "bookstore/contact.html")




def get_or_create_cart(request):
    """Get or create cart for user (session-based or database-based)"""
    if request.user.is_authenticated:
        # Database cart for authenticated users
        try:
            customer = Customer.objects.get(email=request.user.email)
            cart, created = Cart.objects.get_or_create(customer=customer)
            return cart
        except Customer.DoesNotExist:
            pass
    
    # Session cart for anonymous users
    if 'cart' not in request.session:
        request.session['cart'] = {}
    return None  # We'll use session


@require_POST
def add_to_cart(request):
    """Add book to cart"""
    try:
        data = json.loads(request.body)
        book_id = data.get('book_id')
        quantity = int(data.get('quantity', 1))
        
        print(f"Received book_id: {book_id}, quantity: {quantity}")  # Debug
        
        book = Book.objects.get(id=book_id)
        
        if request.user.is_authenticated:
            # Database cart - Create customer if doesn't exist
            customer, created = Customer.objects.get_or_create(
                email=request.user.email,
                defaults={
                    'first_name': request.user.first_name or request.user.username,
                    'last_name': request.user.last_name or '',
                    'password': 'set_via_django_auth'  # Placeholder
                }
            )
            
            cart, _ = Cart.objects.get_or_create(customer=customer)
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                book=book,
                defaults={'quantity': quantity}
            )
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            cart_count = sum(item.quantity for item in cart.items.all())
        else:
            # Session cart
            cart = request.session.get('cart', {})
            book_id_str = str(book_id)
            
            print(f"Adding to session cart - book_id: {book_id_str}, quantity: {quantity}")
            print(f"Current cart before adding: {cart}")
            
            if book_id_str in cart:
                cart[book_id_str] += quantity
            else:
                cart[book_id_str] = quantity
            
            request.session['cart'] = cart
            request.session.modified = True
            cart_count = sum(cart.values())
            
            print(f"Cart after adding: {cart}")
            print(f"Cart count: {cart_count}")
        
        return JsonResponse({
            'success': True,
            'message': f'{book.title} added to cart',
            'cart_count': cart_count
        })
        
    except Book.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Book not found'}, status=404)
    except Exception as e:
        print(f"Error in add_to_cart: {str(e)}")  # Debug
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def get_cart_count(request):
    """Get cart item count"""
    if request.user.is_authenticated:
        try:
            customer = Customer.objects.get(email=request.user.email)
            cart = Cart.objects.filter(customer=customer).first()
            count = cart.total_items if cart else 0
        except Customer.DoesNotExist:
            count = 0
    else:
        cart = request.session.get('cart', {})
        count = sum(cart.values())
    
    return JsonResponse({'cart_count': count})


def cart(request):
    """Display cart page"""
    from decimal import Decimal
    
    cart_items = []
    total_price = Decimal('0.00')
    
    if request.user.is_authenticated:
        try:
            customer = Customer.objects.get(email=request.user.email)
            cart_obj = Cart.objects.filter(customer=customer).first()
            if cart_obj:
                cart_items = cart_obj.items.all()
                total_price = cart_obj.total_price
        except Customer.DoesNotExist:
            pass
    else:
        # Session cart
        cart = request.session.get('cart', {})
        print(f"Session cart: {cart}")
        for book_id, qty in cart.items():
            try:
                book = Book.objects.get(id=book_id)
                item_total = book.price * qty
                cart_items.append({
                    'book': book,
                    'quantity': qty,
                    'total': item_total
                })
                total_price += item_total
                print(f"Added book {book.title} with quantity {qty} to cart items")
            except Book.DoesNotExist:
                print(f"Book with ID {book_id} not found")
                pass
    
    return render(request, 'bookstore/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


def checkout(request):
    """Checkout page view"""
    from decimal import Decimal
    
    cart_items = []
    cart_total = Decimal('0.00')
    
    if request.user.is_authenticated:
        try:
            customer = Customer.objects.get(email=request.user.email)
            cart_obj = Cart.objects.filter(customer=customer).first()
            if cart_obj:
                cart_items = cart_obj.items.all()
                cart_total = cart_obj.total_price
        except Customer.DoesNotExist:
            pass
    else:
        # Session cart
        cart = request.session.get('cart', {})
        for book_id, qty in cart.items():
            try:
                book = Book.objects.get(id=book_id)
                item_total = book.price * qty
                cart_items.append({
                    'book': book,
                    'title': book.title,
                    'price': book.price,
                    'quantity': qty,
                    'total': item_total
                })
                cart_total += item_total
            except Book.DoesNotExist:
                pass
    
    cart_tax = cart_total * Decimal('0.10')  # 10% tax
    shipping = Decimal('5.00')
    cart_grand_total = cart_total + cart_tax + shipping
    
    context = {
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'cart_items': cart_items,
        'cart_total': cart_total,
        'cart_tax': cart_tax,
        'cart_grand_total': cart_grand_total,
    }
    return render(request, 'bookstore/checkout.html', context)


@require_POST
def create_payment_intent(request):
    """Create Stripe Payment Intent"""
    try:
        data = json.loads(request.body)
        amount = float(data.get('amount', 0))
        
        # Convert to cents (Stripe uses smallest currency unit)
        amount_cents = int(amount * 100)
        
        # Create Payment Intent
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency='usd',
            metadata={
                'customer_name': data.get('name'),
                'customer_email': data.get('email'),
                'shipping_address': f"{data.get('address')}, {data.get('city')}, {data.get('state')} {data.get('zip')}"
            }
        )
        
        return JsonResponse({
            'clientSecret': intent.client_secret
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def payment_success(request):
    """Payment success page"""
    payment_intent_id = request.GET.get('payment_intent')
    paypal_order_id = request.GET.get('paypal_order_id')
    
    if payment_intent_id:
        # Verify payment with Stripe
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            if intent.status == 'succeeded':
                # Clear cart and create order
                # Your order creation logic here
                request.session['cart'] = []
                
                context = {
                    'payment_id': payment_intent_id,
                    'amount': intent.amount / 100,  # Convert from cents
                }
                return render(request, 'bookstore/payment_success.html', context)
        except Exception as e:
            return render(request, 'bookstore/payment_error.html', {'error': str(e)})
    
    return render(request, 'bookstore/payment_error.html')


@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        # Handle successful payment
        # Create order, send confirmation email, etc.
    
    return JsonResponse({'status': 'success'})

def privacy_policy(request):
    return render(request, 'bookstore/privacy_policy.html')

def terms_of_service(request):
    return render(request, 'bookstore/terms_of_service.html')

def cookie_policy(request):
    return render(request, 'bookstore/cookie_policy.html')

def shipping_policy(request):
    return render(request, 'bookstore/shipping_policy.html')    

def return_policy(request):
    return render(request, 'bookstore/return_policy.html')

def refund_policy(request):
    return render(request, 'bookstore/refund_policy.html')

def subscribe(request):
    # Handle newsletter subscription logic here
    messages.success(request, "You have successfully subscribed to the newsletter.")
    return redirect('bookstore:index')

def calculate_cart_total(cart):
    from .models import Book
    from decimal import Decimal
    total = Decimal('0.00')
    for book_id, qty in cart.items():
        try:
            book = Book.objects.get(id=book_id)
            total += book.price * qty
        except Book.DoesNotExist:
            pass
    return total


def remove_from_cart(request, book_id):
    if request.method == "POST":
        # Authenticated users: operate on DB-backed cart
        if request.user.is_authenticated:
            try:
                customer = Customer.objects.get(email=request.user.email)
                cart_obj = Cart.objects.filter(customer=customer).first()
                if not cart_obj:
                    return JsonResponse({"success": False, "message": "Cart not found"})

                # Find and delete the specific item
                cart_item = cart_obj.items.filter(book_id=book_id).first()
                if not cart_item:
                    return JsonResponse({"success": False, "message": "Item not in cart"})

                cart_item.delete()

                # Recalculate totals
                total = cart_obj.total_price if hasattr(cart_obj, "total_price") else sum(
                    (ci.book.price * ci.quantity) for ci in cart_obj.items.all()
                )
                is_empty = (cart_obj.items.count() == 0)
                return JsonResponse({"success": True, "total": float(total), "empty": is_empty})
            except Customer.DoesNotExist:
                return JsonResponse({"success": False, "message": "Customer not found"})

        # Anonymous users: operate on session cart
        cart = request.session.get("cart", {})
        if str(book_id) in cart:
            del cart[str(book_id)]
            request.session["cart"] = cart
            total = calculate_cart_total(cart)
            is_empty = (len(cart) == 0)
            return JsonResponse({"success": True, "total": float(total), "empty": is_empty})
        return JsonResponse({"success": False, "message": "Item not in cart"})
    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)


def update_cart(request, book_id):
    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity", 1))
        except ValueError:
            return JsonResponse({"success": False, "message": "Invalid quantity"})

        if quantity < 1:
            return JsonResponse({"success": False, "message": "Quantity must be at least 1"})

        # Authenticated users: update DB-backed cart
        if request.user.is_authenticated:
            try:
                customer = Customer.objects.get(email=request.user.email)
                cart_obj = Cart.objects.filter(customer=customer).first()
                if not cart_obj:
                    return JsonResponse({"success": False, "message": "Cart not found"})

                cart_item = cart_obj.items.filter(book_id=book_id).first()
                if not cart_item:
                    return JsonResponse({"success": False, "message": "Book not in cart"})

                cart_item.quantity = quantity
                cart_item.save()

                total = cart_obj.total_price if hasattr(cart_obj, "total_price") else sum(
                    (ci.book.price * ci.quantity) for ci in cart_obj.items.all()
                )
                is_empty = (cart_obj.items.count() == 0)
                return JsonResponse({"success": True, "total": float(total), "empty": is_empty})
            except Customer.DoesNotExist:
                return JsonResponse({"success": False, "message": "Customer not found"})

        # Anonymous users: update session cart
        cart = request.session.get("cart", {})
        if str(book_id) in cart:
            cart[str(book_id)] = quantity
            request.session["cart"] = cart
            total = calculate_cart_total(cart)
            is_empty = (len(cart) == 0)
            return JsonResponse({"success": True, "total": float(total), "empty": is_empty})
        else:
            return JsonResponse({"success": False, "message": "Book not in cart"})

    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

def subscribe(request):
    if request.method == "POST":
        email = request.POST.get("email")
        if email:
            if NewsletterSubscriber.objects.filter(email=email).exists():
                messages.info(request, "You are already subscribed.")
            else:
                NewsletterSubscriber.objects.create(email=email)
                messages.success(request, "Thank you for subscribing!")
        return redirect(request.META.get("HTTP_REFERER", "bookstore:index"))
    
# for the admin pages
