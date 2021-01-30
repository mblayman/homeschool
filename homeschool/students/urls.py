from django.urls import path

from . import views

app_name = "students"
urlpatterns = [
    path("", views.StudentIndexView.as_view(), name="index"),
    path("create/", views.StudentCreateView.as_view(), name="create"),
    path(
        "<uuid:uuid>/courses/<uuid:course_uuid>/",
        views.StudentCourseView.as_view(),
        name="course",
    ),
    path(
        "<uuid:uuid>/tasks/<uuid:course_task_uuid>/",
        views.CourseworkFormView.as_view(),
        name="coursework",
    ),
    path("grade/", views.GradeView.as_view(), name="grade"),
    path(
        "enroll/<uuid:school_year_uuid>/",
        views.EnrollmentCreateView.as_view(),
        name="enrollment_create",
    ),
    path(
        "<uuid:uuid>/enroll/<uuid:school_year_uuid>/",
        views.StudentEnrollmentCreateView.as_view(),
        name="student_enrollment_create",
    ),
]
