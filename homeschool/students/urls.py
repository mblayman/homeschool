from django.urls import path

from . import views

app_name = "students"
urlpatterns = [
    path("", views.StudentIndexView.as_view(), name="index"),
    path(
        "<uuid:uuid>/courses/<uuid:course_uuid>/",
        views.StudentCourseView.as_view(),
        name="course",
    ),
    path("grade/", views.GradeView.as_view(), name="grade"),
]
