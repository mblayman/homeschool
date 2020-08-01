from django.urls import path

from . import views

app_name = "reports"
urlpatterns = [path("", views.ReportsIndexView.as_view(), name="index")]
