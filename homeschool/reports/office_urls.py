from django.urls import path

from . import views

app_name = "pdfs"
urlpatterns = [
    path("dashboard/", views.office_pdfs_dashboard, name="dashboard"),
    path("attendance/", views.office_attendance_report, name="attendance"),
    path("coursework/", views.office_coursework_report, name="coursework"),
    path("progress/", views.office_progress_report, name="progress"),
    path("resource/", views.office_resource_report, name="resource"),
]
