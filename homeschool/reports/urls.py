from django.urls import path

from . import views

app_name = "reports"
urlpatterns = [
    path("", views.reports_index, name="index"),
    path("bundle/<hashid:pk>/", views.get_bundle, name="bundle"),
    path("attendance/<hashid:pk>/", views.attendance_report, name="attendance"),
    path("progress/<hashid:pk>/", views.progress_report, name="progress"),
    path("resources/<hashid:pk>/", views.resource_report, name="resource"),
]
