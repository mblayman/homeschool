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
        "school-years/<uuid:uuid>/",
        views.SchoolYearDetailView.as_view(),
        name="school_year_detail",
    ),
    path("school-years/", views.SchoolYearListView.as_view(), name="school_year_list"),
]
