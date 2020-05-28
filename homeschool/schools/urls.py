from django.urls import path

from . import views

app_name = "schools"
urlpatterns = [
    path(
        "school-years/<uuid:uuid>/",
        views.SchoolYearDetailView.as_view(),
        name="school_year_detail",
    )
]
