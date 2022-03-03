from django.urls import path

from . import views

app_name = "pdfs"
urlpatterns = [
    path("dashboard/", views.pdfs_dashboard, name="dashboard"),
    path("resource/", views.resource_report, name="resource"),
]
