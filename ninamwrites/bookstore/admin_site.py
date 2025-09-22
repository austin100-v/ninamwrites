# admin_site.py
import json
from django.contrib.admin import AdminSite
from django.db.models.functions import TruncMonth
from django.db.models import Count
from bookstore.models import Book, Order, NewsletterSubscriber, Merchandise, Testimonial



class NinamWritesAdminSite(AdminSite):
    site_header = ("Nina M. Writes Administration")
    site_title = ("Nina M. Writes Admin")
    index_title = ("Dashboard")
    
    index_template = "ninamwrites_admin/index.html"
    base_template = "ninamwrites_admin/base.html"

    def has_permission(self, request):
        # only superusers can log in
        return request.user.is_active and request.user.is_superuser

    def each_context(self, request):
        context = super().each_context(request)

        # Quick counts
        context["books_count"] = Book.objects.count()
        context["merch_count"] = Merchandise.objects.count()
        context["orders_count"] = Order.objects.count()
        context["subs_count"] = NewsletterSubscriber.objects.count()

        # Orders grouped by month
        orders_by_month = (
            Order.objects.annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )

        # Subscribers grouped by month
        subs_by_month = (
            NewsletterSubscriber.objects.annotate(month=TruncMonth("date_subscribed"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )

        # Format months nicely
        orders_data = [
            {"month": o["month"].strftime("%b %Y"), "count": o["count"]}
            for o in orders_by_month
        ]
        subs_data = [
            {"month": s["month"].strftime("%b %Y"), "count": s["count"]}
            for s in subs_by_month
        ]

        # Dump JSON so template can use it safely
        context["orders_by_month_json"] = json.dumps(orders_data)
        context["subs_by_month_json"] = json.dumps(subs_data)

        return context




# Create instance of custom admin site
ninamwrites_admin = NinamWritesAdminSite(name="ninamwrites_admin")

# Register models
ninamwrites_admin.register(Book)
ninamwrites_admin.register(Merchandise)
ninamwrites_admin.register(Order)
ninamwrites_admin.register(NewsletterSubscriber)
ninamwrites_admin.register(Testimonial)

