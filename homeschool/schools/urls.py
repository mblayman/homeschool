from django.urls import path

from . import views

app_name = "schools"
urlpatterns = [
    path(
        "school-year/",
        views.CurrentSchoolYearView.as_view(),
        name="current_school_year",
    ),
    path(
        "school-years/add/",
        views.SchoolYearCreateView.as_view(),
        name="school_year_create",
    ),
    path(
        "school-years/<uuid:uuid>/",
        views.SchoolYearDetailView.as_view(),
        name="school_year_detail",
    ),
    path(
        "school-years/<uuid:uuid>/edit/",
        views.SchoolYearEditView.as_view(),
        name="school_year_edit",
    ),
    path("school-years/", views.SchoolYearListView.as_view(), name="school_year_list"),
    path(
        "school-years/<uuid:uuid>/grade-levels/",
        views.GradeLevelCreateView.as_view(),
        name="grade_level_create",
    ),
    path(
        "school-years/<uuid:uuid>/breaks/",
        views.SchoolBreakCreateView.as_view(),
        name="school_break_create",
    ),
    path(
        "school-years/breaks/<uuid:uuid>/",
        views.SchoolBreakUpdateView.as_view(),
        name="school_break_edit",
    ),
]
