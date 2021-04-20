from django.urls import path

from . import views

app_name = "reports"
urlpatterns = [
    path("", views.ReportsIndexView.as_view(), name="index"),
    path(
        "attendance/<uuid:uuid>/",
        views.AttendanceReportView.as_view(),
        name="attendance",
    ),
    path("progress/<uuid:uuid>/", views.ProgressReportView.as_view(), name="progress"),
    path(
        "resources/<uuid:uuid>/student/<uuid:student_uuid>/",
        views.ResourceReportView.as_view(),
        name="resource",
    ),
]
