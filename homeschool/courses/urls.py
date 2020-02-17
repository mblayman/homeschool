from django.urls import path

from . import views

app_name = "courses"
urlpatterns = [
    path("", views.CourseListView.as_view(), name="list"),
    path("<uuid:uuid>/", views.CourseDetailView.as_view(), name="detail"),
    path(
        "<uuid:uuid>/tasks/", views.CourseTaskCreateView.as_view(), name="task_create"
    ),
    path(
        "<uuid:uuid>/tasks/<uuid:task_uuid>/delete/",
        views.CourseTaskDeleteView.as_view(),
        name="task_delete",
    ),
    path("tasks/<uuid:uuid>/", views.CourseTaskUpdateView.as_view(), name="task_edit"),
]
