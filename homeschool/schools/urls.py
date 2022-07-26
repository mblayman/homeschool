from django.urls import path

from . import views

app_name = "schools"
urlpatterns = [
    path("school-year/", views.current_school_year, name="current_school_year"),
    path(
        "school-years/add/",
        views.SchoolYearCreateView.as_view(),
        name="school_year_create",
    ),
    path(
        "school-years/<hashid:pk>/",
        views.SchoolYearDetailView.as_view(),
        name="school_year_detail",
    ),
    path(
        "school-years/<hashid:pk>/edit/",
        views.SchoolYearEditView.as_view(),
        name="school_year_edit",
    ),
    path(
        "grade-levels/<hashid:pk>/down/",
        views.move_grade_level_down,
        name="grade_level_down",
    ),
    path(
        "grade-levels/<hashid:pk>/up/", views.move_grade_level_up, name="grade_level_up"
    ),
    path(
        "school-years/<hashid:pk>/forecast/",
        views.school_year_forecast,
        name="school_year_forecast",
    ),
    path("school-years/", views.SchoolYearListView.as_view(), name="school_year_list"),
    path(
        "school-years/<hashid:pk>/grade-levels/",
        views.GradeLevelCreateView.as_view(),
        name="grade_level_create",
    ),
    path(
        "grade-levels/<hashid:pk>/",
        views.GradeLevelDetailView.as_view(),
        name="grade_level_detail",
    ),
    path(
        "grade-levels/<hashid:pk>/edit/",
        views.GradeLevelUpdateView.as_view(),
        name="grade_level_edit",
    ),
    path(
        "grade-levels/<hashid:pk>/courses/<hashid:course_id>/down/",
        views.move_course_down,
        name="course_down",
    ),
    path(
        "grade-levels/<hashid:pk>/courses/<hashid:course_id>/up/",
        views.move_course_up,
        name="course_up",
    ),
    path(
        "school-years/<hashid:pk>/breaks/",
        views.SchoolBreakCreateView.as_view(),
        name="school_break_create",
    ),
    path(
        "breaks/<hashid:pk>/",
        views.SchoolBreakUpdateView.as_view(),
        name="school_break_edit",
    ),
    path(
        "breaks/<hashid:pk>/delete/",
        views.SchoolBreakDeleteView.as_view(),
        name="school_break_delete",
    ),
]
