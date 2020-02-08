from django.urls import path

from . import views

app_name = "courses"
urlpatterns = [
    path("<uuid:uuid>/", views.CourseDetailView.as_view(), name="detail"),
    path("tasks/<uuid:uuid>/", views.CourseTaskUpdateView.as_view(), name="task_edit"),
]
