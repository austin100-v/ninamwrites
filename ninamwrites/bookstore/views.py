from django.shortcuts import render, redirect
from django.contrib import messages, admin
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .models import Testimonial, Order, Book, Merchandise, NewsletterSubscriber # assuming you track purchases via an Order model
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail

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


def cart(request):
    return render(request, 'bookstore/cart.html')

def checkout(request):
    return render(request, 'bookstore/checkout.html')

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
    total = 0
    for book_id, qty in cart.items():
        try:
            book = Book.objects.get(id=book_id)
            total += book.price * qty
        except Book.DoesNotExist:
            pass
    return total


def remove_from_cart(request, book_id):
    if request.method == "POST":
        cart = request.session.get("cart", {})
        if str(book_id) in cart:
            del cart[str(book_id)]
            request.session["cart"] = cart
            total = calculate_cart_total(cart)
            is_empty = (len(cart) == 0)
            return JsonResponse({"success": True, "total": total, "empty": is_empty})
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

        cart = request.session.get("cart", {})
        if str(book_id) in cart:
            cart[str(book_id)] = quantity
            request.session["cart"] = cart
            total = calculate_cart_total(cart)
            is_empty = (len(cart) == 0)
            return JsonResponse({"success": True, "total": total, "empty": is_empty})
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
