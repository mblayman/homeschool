from django.urls import path

from . import views

app_name = "courses"
urlpatterns = [
    path("<uuid:uuid>/", views.CourseDetailView.as_view(), name="detail"),
    path(
        "<uuid:uuid>/tasks/", views.CourseTaskCreateView.as_view(), name="task_create"
    ),
    path("tasks/<uuid:uuid>/", views.CourseTaskUpdateView.as_view(), name="task_edit"),
]
