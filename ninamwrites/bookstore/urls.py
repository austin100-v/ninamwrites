from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

app_name = 'bookstore'

urlpatterns = [
    path('', views.index, name='index'),

    # Auth
    path("auth/", views.auth_view, name="auth"),
    path("logout/", views.logout_view, name="logout"),

    # Testimonials
    path("testimonials/", views.submit_testimonial, name="testimonial"),

    # Books & Shop
    path('books/', views.books, name='books'),  # 👈 keep this one
    # path('books/', views.shop, name='shop'),  # ❌ removed duplicate
    path('books/<int:book_id>/', views.book_detail, name='book_detail'),

    # Other pages
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # Cart
    path('cart/', views.cart, name='cart'),
    path("cart/update/<int:book_id>/", views.update_cart, name="update_cart"),
    path("cart/remove/<int:book_id>/", views.remove_from_cart, name="remove_from_cart"),

    # Checkout
    path('checkout/', views.checkout, name='checkout'),

    # Merch & Subscribe
    path('merch/', views.merchandise_view, name='merchandise'),
    path('subscribe/', views.subscribe, name='subscribe'),

    # Policies
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('cookie-policy/', views.cookie_policy, name='cookie_policy'),
    path('shipping-policy/', views.shipping_policy, name='shipping_policy'),
    path('return-policy/', views.return_policy, name='return_policy'),
    path('refund-policy/', views.refund_policy, name='refund_policy'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



