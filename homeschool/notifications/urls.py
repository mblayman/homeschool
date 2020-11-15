from django.urls import path

from . import views

app_name = "notifications"
urlpatterns = [path("whats-new/", views.send_whats_new, name="whats_new")]
