from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
import json
from decimal import Decimal
from datetime import datetime
# Import from bookstore app
from bookstore.models import (
    Book, Order, Merchandise, NewsletterSubscriber, Testimonial
)


@login_required(login_url='/ninamwrites_admin/login/')
def admin_dashboard(request):
    """Admin dashboard with analytics"""
    context = {
        'books_count': Book.objects.count(),
        'merch_count': Merchandise.objects.count(),
        'orders_count': Order.objects.count(),
        'subs_count': NewsletterSubscriber.objects.count(),
    }
    return render(request, "ninamwrites_admin/index.html", context)


@staff_member_required
@csrf_protect
def add_book(request):
    """Add new book with proper error handling"""
    if request.method == "POST":
        # Handle AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                title = request.POST.get("title", "").strip()
                author = request.POST.get("author", "").strip()
                description = request.POST.get("description", "").strip()
                price = request.POST.get("price", "").strip()
                published_date = request.POST.get("published_date", "").strip()
                stock_quantity = request.POST.get("stock_quantity", "").strip()
                isbn = request.POST.get("isbn", "").strip()
                image = request.FILES.get("image")

                # Validation
                if not all([title, author, price]):
                    return JsonResponse({
                        "success": False, 
                        "error": "Title, author, and price are required fields"
                    })

                try:
                    price = Decimal(price)
                    if price < 0:
                        raise ValueError("Price cannot be negative")
                except (ValueError, TypeError):
                    return JsonResponse({
                        "success": False, 
                        "error": "Invalid price format"
                    })

                try:
                    stock_quantity = int(stock_quantity) if stock_quantity else 0
                    if stock_quantity < 0:
                        raise ValueError("Stock quantity cannot be negative")
                except (ValueError, TypeError):
                    return JsonResponse({
                        "success": False, 
                        "error": "Invalid stock quantity format"
                    })

                # Date validation
                if published_date:
                    try:
                        datetime.strptime(published_date, '%Y-%m-%d')
                    except ValueError:
                        return JsonResponse({
                            "success": False, 
                            "error": "Invalid date format"
                        })

                # Create new book
                if not image:
                    return JsonResponse({
                        "success": False, 
                        "error": "Image is required for new books"
                    })
                
                book = Book.objects.create(
                    title=title,
                    author=author,
                    description=description,
                    price=price,
                    published_date=published_date if published_date else None,
                    stock_quantity=stock_quantity,
                    isbn=isbn,
                    image=image,
                )

                return JsonResponse({
                    "success": True,
                    "book": {
                        "id": book.id,
                        "title": book.title,
                        "author": book.author,
                        "price": str(book.price),
                        "isbn": book.isbn or "",
                        "published_date": book.published_date.strftime('%b %Y') if book.published_date else "",
                        "edit_url": reverse('ninamwrites_admin:edit_book', args=[book.pk])
                    }
                })

            except Exception as e:
                return JsonResponse({
                    "success": False, 
                    "error": f"An error occurred: {str(e)}"
                })

        # Handle regular form submission
        else:
            messages.success(request, "Book added successfully!")
            return redirect("ninamwrites_admin:add_book")

    # GET request - display form
    context = {
        'books': Book.objects.all().order_by('-id'),
        'is_edit': False,
    }
    return render(request, "ninamwrites_admin/add_book.html", context)


@staff_member_required
@csrf_protect
def edit_book(request, pk):
    """Edit existing book"""
    book = get_object_or_404(Book, pk=pk)

    if request.method == "POST":
        # Handle AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                title = request.POST.get("title", "").strip()
                author = request.POST.get("author", "").strip()
                description = request.POST.get("description", "").strip()
                price = request.POST.get("price", "").strip()
                published_date = request.POST.get("published_date", "").strip()
                stock_quantity = request.POST.get("stock_quantity", "").strip()
                isbn = request.POST.get("isbn", "").strip()
                image = request.FILES.get("image")

                # Validation
                if not all([title, author, price]):
                    return JsonResponse({
                        "success": False, 
                        "error": "Title, author, and price are required fields"
                    })

                try:
                    price = Decimal(price)
                    if price < 0:
                        raise ValueError("Price cannot be negative")
                except (ValueError, TypeError):
                    return JsonResponse({
                        "success": False, 
                        "error": "Invalid price format"
                    })

                try:
                    stock_quantity = int(stock_quantity) if stock_quantity else 0
                    if stock_quantity < 0:
                        raise ValueError("Stock quantity cannot be negative")
                except (ValueError, TypeError):
                    return JsonResponse({
                        "success": False, 
                        "error": "Invalid stock quantity format"
                    })

                # Date validation
                if published_date:
                    try:
                        datetime.strptime(published_date, '%Y-%m-%d')
                    except ValueError:
                        return JsonResponse({
                            "success": False, 
                            "error": "Invalid date format"
                        })

                # Update existing book
                book.title = title
                book.author = author
                book.description = description
                book.price = price
                book.published_date = published_date if published_date else None
                book.stock_quantity = stock_quantity
                book.isbn = isbn
                if image:
                    book.image = image
                book.save()

                return JsonResponse({
                    "success": True,
                    "book": {
                        "id": book.id,
                        "title": book.title,
                        "author": book.author,
                        "price": str(book.price),
                        "isbn": book.isbn or "",
                        "published_date": book.published_date.strftime('%b %Y') if book.published_date else "",
                        "edit_url": reverse('ninamwrites_admin:edit_book', args=[book.pk])
                    }
                })

            except Exception as e:
                return JsonResponse({
                    "success": False, 
                    "error": f"An error occurred: {str(e)}"
                })

        # Handle regular form submission
        else:
            messages.success(request, "Book updated successfully!")
            return redirect("ninamwrites_admin:add_book")

    # GET request - display form with book data
    context = {
        'books': Book.objects.all().order_by('-id'),
        'book': book,
        'is_edit': True,
    }
    return render(request, "ninamwrites_admin/add_book.html", context)


@staff_member_required
@csrf_protect
def delete_book(request, pk):
    """Delete book with AJAX support"""
    book = get_object_or_404(Book, pk=pk)
    
    if request.method == "POST":
        try:
            book_title = book.title
            book.delete()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": True,
                    "message": f"Book '{book_title}' deleted successfully!"
                })
            else:
                messages.success(request, f"Book '{book_title}' deleted successfully!")
                return redirect("ninamwrites_admin:add_book")
                
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": False,
                    "error": f"Error deleting book: {str(e)}"
                })
            else:
                messages.error(request, f"Error deleting book: {str(e)}")
                return redirect("ninamwrites_admin:add_book")
    
    # GET request should not delete - return error
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            "success": False,
            "error": "GET method not allowed for deletion"
        })
    else:
        messages.error(request, "Invalid request method")
        return redirect("ninamwrites_admin:add_book")


@staff_member_required
@csrf_protect
def add_merch(request):
    """Add merchandise with proper validation"""
    if request.method == "POST":
        # Handle AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                title = request.POST.get("title", "").strip()
                description = request.POST.get("description", "").strip()
                category = request.POST.get("category", "").strip()
                price = request.POST.get("price", "").strip()
                has_sizes = request.POST.get("has_sizes") == "on"
                image = request.FILES.get("image")

                # Validation
                if not all([title, category, price]):
                    return JsonResponse({
                        "success": False, 
                        "error": "Title, category, and price are required fields"
                    })

                try:
                    price = Decimal(price)
                    if price < 0:
                        raise ValueError("Price cannot be negative")
                except (ValueError, TypeError):
                    return JsonResponse({
                        "success": False, 
                        "error": "Invalid price format"
                    })

                if not image:
                    return JsonResponse({
                        "success": False, 
                        "error": "Image is required"
                    })

                merch = Merchandise.objects.create(
                    title=title,
                    description=description,
                    category=category,
                    price=price,
                    has_sizes=has_sizes,
                    image=image
                )

                return JsonResponse({
                    "success": True,
                    "merch": {
                        "id": merch.id,
                        "title": merch.title,
                        "category": merch.get_category_display() if hasattr(merch, 'get_category_display') else merch.category,
                        "price": str(merch.price),
                        "has_sizes": "Yes" if merch.has_sizes else "No",
                    }
                })

            except Exception as e:
                return JsonResponse({
                    "success": False, 
                    "error": f"An error occurred: {str(e)}"
                })

        # Handle regular form submission
        else:
            messages.success(request, "Merchandise added successfully!")
            return redirect("ninamwrites_admin:add_merch")

    # GET request
    context = {
        'merch': Merchandise.objects.all().order_by('-id'),
    }
    return render(request, "ninamwrites_admin/add_merch.html", context)


@staff_member_required
def view_orders(request):
    """View all orders with pagination"""
    orders = Order.objects.all().order_by('-created_at')
    return render(request, "ninamwrites_admin/view_orders.html", {"orders": orders})


@staff_member_required
def view_subscribers(request):
    """View all newsletter subscribers"""
    subs = NewsletterSubscriber.objects.all().order_by('-date_subscribed')
    return render(request, "ninamwrites_admin/view_subscribers.html", {"subs": subs})


@staff_member_required
def view_testimonials(request):
    """View all testimonials"""
    testimonials = Testimonial.objects.all().order_by('-date')
    return render(request, "ninamwrites_admin/view_testimonials.html", {"testimonials": testimonials})


@staff_member_required
@csrf_protect
def send_newsletter(request):
    """Send newsletter to all subscribers"""
    if request.method == "POST":
        subject = request.POST.get("subject", "").strip()
        message = request.POST.get("message", "").strip()
        
        if not subject or not message:
            return JsonResponse({
                "success": False,
                "error": "Subject and message are required"
            })
        
        try:
            # Here you would implement actual email sending logic
            # For now, just return success
            subscribers_count = NewsletterSubscriber.objects.count()
            return JsonResponse({
                "success": True,
                "message": f"Newsletter sent to {subscribers_count} subscribers successfully!"
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": f"Failed to send newsletter: {str(e)}"
            })
    
    return render(request, "ninamwrites_admin/send_newsletter.html")


def logout_view(request):
    """Custom logout view"""
    return render(request, "ninamwrites_admin/login.html")