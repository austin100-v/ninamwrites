from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
# ✅ import from bookstore app, not local
from bookstore.models import (
    Book, Order, Merchandise, NewsletterSubscriber, Testimonial
)


@login_required(login_url='/ninamwrites_admin/login/')
def admin_dashboard(request):
    return render(request, "ninamwrites_admin/index.html")



@staff_member_required
def add_merch(request):
    if request.method == "POST":
        title = request.POST.get("title")
        category = request.POST.get("category")
        price = request.POST.get("price")
        has_sizes = request.POST.get("has_sizes")
        image = request.FILES.get("image")  # 👈 better use request.FILES for uploads

        if not title or not category or not price:
            return JsonResponse({"success": False, "error": "Missing fields"})

        merch = Merchandise.objects.create(
            title=title,
            category=category,
            price=price,
            has_sizes=bool(has_sizes),
            image=image
        )
        return JsonResponse({
            "success": True,
            "merch": {
                "title": merch.title,
                "category": merch.category,
                "price": merch.price,
                "has_sizes": merch.has_sizes,
            }
        })
    
    return render(request, "ninamwrites_admin/add_merch.html")
    # return JsonResponse({"success": False, "error": "Invalid request"})


@staff_member_required
def add_book(request, pk=None):
    # If pk is present we are editing
    book = get_object_or_404(Book, pk=pk) if pk else None

    if request.method == "POST":
        title = request.POST.get("title")
        author = request.POST.get("author")
        description = request.POST.get("description")
        price = request.POST.get("price")
        published_date = request.POST.get("published_date")
        stock_quantity = request.POST.get("stock_quantity")
        isbn = request.POST.get("isbn")
        image = request.FILES.get("image")

        if not title or not author or not price:
            return render(
                request,
                "ninamwrites_admin/add_book.html",
                {"error": "Missing fields", "books": Book.objects.all(), "book": book},
            )

        if book:
            # 🔄 Update existing book
            book.title = title
            book.author = author
            book.description = description
            book.price = price
            book.published_date = published_date
            book.stock_quantity = stock_quantity
            book.isbn = isbn
            if image:      # only replace if a new file was uploaded
                book.image = image
            book.save()
        else:
            # ➕ Create a new book
            Book.objects.create(
                title=title,
                author=author,
                description=description,
                price=price,
                published_date=published_date,
                stock_quantity=stock_quantity,
                isbn=isbn,
                image=image,
            )

        return redirect("ninamwrites_admin:add_book")  # back to list

    return render(
        request,
        "ninamwrites_admin/add_book.html",
        {"books": Book.objects.all(), "book": book},  # pass book for editing
    )


@staff_member_required
def view_orders(request):
    orders = Order.objects.all()
    return render(request, "ninamwrites_admin/view_orders.html", {"orders": orders})


@staff_member_required
def view_subscribers(request):
    subs = NewsletterSubscriber.objects.all()
    return render(request, "ninamwrites_admin/view_subscribers.html", {"subs": subs})


@staff_member_required
def view_testimonials(request):
    testimonials = Testimonial.objects.all()
    return render(request, "ninamwrites_admin/view_testimonials.html", {"testimonials": testimonials})


@staff_member_required
def send_newsletter(request):
    return render(request, "ninamwrites_admin/send_newsletter.html")

def logout(request):
    return render(request, "ninamwrites_admin/login.html")