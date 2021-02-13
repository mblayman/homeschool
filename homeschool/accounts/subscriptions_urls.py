from django.urls import path

from . import views

app_name = "subscriptions"
urlpatterns = [path("", views.subscriptions_index, name="index")]
