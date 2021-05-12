from django.urls import path

from . import views

app_name = "students"
urlpatterns = [
    path("", views.StudentIndexView.as_view(), name="index"),
    path("create/", views.StudentCreateView.as_view(), name="create"),
    path(
        "<hashid:pk>/tasks/<hashid:course_task_id>/",
        views.CourseworkFormView.as_view(),
        name="coursework",
    ),
    path(
        "<hashid:pk>/tasks/<hashid:course_task_id>/grade/",
        views.GradeFormView.as_view(),
        name="grade_task",
    ),
    path("grade/", views.GradeView.as_view(), name="grade"),
    path(
        "enroll/<hashid:school_year_id>/",
        views.EnrollmentCreateView.as_view(),
        name="enrollment_create",
    ),
    path(
        "<hashid:pk>/enroll/<hashid:school_year_id>/",
        views.StudentEnrollmentCreateView.as_view(),
        name="student_enrollment_create",
    ),
]
