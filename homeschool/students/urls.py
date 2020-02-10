from django.urls import path

from . import views

app_name = "students"
urlpatterns = [
    path(
        "<uuid:uuid>/courses/<uuid:course_uuid>/",
        views.StudentCourseView.as_view(),
        name="course",
    )
]
