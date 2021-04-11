from django.urls import path

from . import views

app_name = "courses"
urlpatterns = [
    path("", views.CourseCreateView.as_view(), name="create"),
    path("<uuid:uuid>/", views.CourseDetailView.as_view(), name="detail"),
    path("<uuid:uuid>/edit/", views.CourseEditView.as_view(), name="edit"),
    path("copy/", views.CourseCopySelectView.as_view(), name="copy"),
    path(
        "<uuid:uuid>/tasks/", views.CourseTaskCreateView.as_view(), name="task_create"
    ),
    path(
        "<uuid:uuid>/tasks/bulk/",
        views.bulk_create_course_tasks,
        name="task_create_bulk",
    ),
    path(
        "<uuid:uuid>/tasks/bulk/partial/<int:last_form_number>/",
        views.get_course_task_bulk_hx,
        name="task_create_bulk_hx",
    ),
    path(
        "<uuid:uuid>/tasks/<uuid:task_uuid>/delete/",
        views.CourseTaskDeleteView.as_view(),
        name="task_delete",
    ),
    path(
        "tasks/<uuid:uuid>/delete/", views.course_task_hx_delete, name="task_hx_delete"
    ),
    path("tasks/<uuid:uuid>/", views.CourseTaskUpdateView.as_view(), name="task_edit"),
    path("tasks/<uuid:uuid>/down/", views.move_task_down, name="task_down"),
    path("tasks/<uuid:uuid>/up/", views.move_task_up, name="task_up"),
    path(
        "<uuid:uuid>/resources/",
        views.CourseResourceCreateView.as_view(),
        name="resource_create",
    ),
    path(
        "resources/<uuid:uuid>/",
        views.CourseResourceUpdateView.as_view(),
        name="resource_edit",
    ),
    path(
        "resources/<uuid:uuid>/delete/",
        views.CourseResourceDeleteView.as_view(),
        name="resource_delete",
    ),
]
