from django.contrib import admin, messages

# Register your models here.

from django.urls import reverse, NoReverseMatch, path
from .models import Book, Testimonial, Order, NewsletterSubscriber, Merchandise, Testimonial
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from .forms import NewsletterForm
from .admin_site import NinamWritesAdminSite

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'price', 'published_date')
    search_fields = ('title', 'author')
    list_filter = ('published_date',)

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('author',)
    search_fields = ('author', 'content')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'total_price', 'created_at')
    search_fields = ('id',)
    readonly_fields = ('created_at',)

    def save_model(self, request, obj, form, change):
        if not change:  # Only calculate total on creation
            obj.calculate_total()
        super().save_model(request, obj, form, change)
        # Ensure the total price is calculated when saving the order
        obj.calculate_total()
        obj.save()
        # Redirect to the order detail page after saving
        try:
            self.message_user(request, "Order saved successfully.")
        except NoReverseMatch:
            self.message_user(request, "Order saved successfully, but could not redirect to detail page.")
        return reverse('admin:bookstore_order_change', args=[obj.id])
        # Note: The above line assumes you have a URL pattern for the order detail page.
        # Adjust the URL name as necessary based on your project's URL configuration.   


@admin.register(Merchandise)
class MerchandiseAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "price", "has_sizes")
    list_filter = ("category",)
    search_fields = ("title",)


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "date_subscribed")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("send-newsletter/", self.admin_site.admin_view(self.send_newsletter_view), name="send-newsletter"),
        ]
        return custom_urls + urls

    def send_newsletter_view(self, request):
        if request.method == "POST":
            form = NewsletterForm(request.POST)
            if form.is_valid():
                subject = form.cleaned_data["subject"]
                message = form.cleaned_data["message"]
                from_email = settings.EMAIL_HOST_USER
                recipient_list = NewsletterSubscriber.objects.values_list("email", flat=True)

                if recipient_list:
                    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
                    self.message_user(request, f"Newsletter sent to {len(recipient_list)} subscribers.", level=messages.SUCCESS)
                    return redirect("..")  # Go back to admin
        else:
            form = NewsletterForm()

        context = {
            "form": form,
            "title": "Send Newsletter",
        }
        return render(request, "admin/send_newsletter.html", context)



# Create instance of custom admin site
ninamwrites_admin = NinamWritesAdminSite(name="ninamwrites_admin")

# Register models
ninamwrites_admin.register(Book)
ninamwrites_admin.register(Merchandise)
ninamwrites_admin.register(Order)
ninamwrites_admin.register(NewsletterSubscriber)
ninamwrites_admin.register(Testimonial)



