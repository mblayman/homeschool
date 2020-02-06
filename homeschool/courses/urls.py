from django.urls import path

from . import views

app_name = "courses"
urlpatterns = [
    path(
        "tasks/<uuid:uuid>/",
        views.CourseTaskUpdateView.as_view(),
        name="course_task_edit",
    )
]
