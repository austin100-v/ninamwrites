from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = "ninamwrites_admin"

urlpatterns = [
    path("", views.admin_dashboard, name="index"),   # root of /ninamwrites_admin/
    path('login/', auth_views.LoginView.as_view(template_name="ninamwrites_admin/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="ninamwrites_admin:login"), name="logout"),    
    path("books/", views.add_book, name="add_book"),
    path("books/edit/<int:pk>/", views.edit_book, name="edit_book"),
    path("books/delete/<int:pk>/", views.delete_book, name="delete_book"),
    path("merch/", views.add_merch, name="add_merch"),
    path("orders/", views.view_orders, name="view_orders"),
    path("subscribers/", views.view_subscribers, name="view_subscribers"),
    path("testimonials/", views.view_testimonials, name="view_testimonials"),
    path("send-newsletter", views.send_newsletter, name="send_newsletter"),
]