from django.urls import path

from . import views

app_name = "reports"
urlpatterns = [
    path("", views.ReportsIndexView.as_view(), name="index"),
    path("bundle/<hashid:pk>/", views.get_bundle, name="bundle"),
    path(
        "attendance/<hashid:pk>/",
        views.AttendanceReportView.as_view(),
        name="attendance",
    ),
    path("progress/<hashid:pk>/", views.ProgressReportView.as_view(), name="progress"),
    path("resources/<hashid:pk>/", views.ResourceReportView.as_view(), name="resource"),
]
