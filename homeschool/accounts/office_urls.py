from django.urls import path

from . import views

app_name = "accounts"
urlpatterns = [
    path("customers/", views.customers_dashboard, name="customers_dashboard"),
    path("customers/<int:id>", views.customer_detail, name="customer_detail"),
]
