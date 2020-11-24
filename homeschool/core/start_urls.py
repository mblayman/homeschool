from django.urls import path

from . import views

urlpatterns = [
    path("", views.StartView.as_view(), name="start"),
    path("school-year/", views.StartSchoolYearView.as_view(), name="start-school-year"),
    path("grade-level/", views.StartGradeLevelView.as_view(), name="start-grade-level"),
    path("course/", views.StartCourseView.as_view(), name="start-course"),
    path("task/", views.StartCourseView.as_view(), name="start-course-task"),
]
