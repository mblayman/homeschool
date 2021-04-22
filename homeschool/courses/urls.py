from django.urls import path

from . import views

app_name = "courses"
urlpatterns = [
    path("", views.CourseCreateView.as_view(), name="create"),
    path("copy/", views.CourseCopySelectView.as_view(), name="copy"),
    path("<hashid:pk>/", views.CourseDetailView.as_view(), name="detail"),
    path("<hashid:pk>/edit/", views.CourseEditView.as_view(), name="edit"),
    path("<hashid:pk>/delete/", views.CourseDeleteView.as_view(), name="delete"),
    path(
        "<hashid:pk>/tasks/", views.CourseTaskCreateView.as_view(), name="task_create"
    ),
    path(
        "<hashid:pk>/tasks/bulk/",
        views.bulk_create_course_tasks,
        name="task_create_bulk",
    ),
    path(
        "<hashid:pk>/tasks/bulk/partial/<int:last_form_number>/",
        views.get_course_task_bulk_hx,
        name="task_create_bulk_hx",
    ),
    path(
        "<hashid:course_id>/tasks/<hashid:pk>/delete/",
        views.CourseTaskDeleteView.as_view(),
        name="task_delete",
    ),
    path(
        "tasks/<hashid:pk>/delete/", views.course_task_hx_delete, name="task_hx_delete"
    ),
    path("tasks/<hashid:pk>/", views.CourseTaskUpdateView.as_view(), name="task_edit"),
    path("tasks/<hashid:pk>/down/", views.move_task_down, name="task_down"),
    path("tasks/<hashid:pk>/up/", views.move_task_up, name="task_up"),
    path(
        "<hashid:pk>/resources/",
        views.CourseResourceCreateView.as_view(),
        name="resource_create",
    ),
    path(
        "resources/<hashid:pk>/",
        views.CourseResourceUpdateView.as_view(),
        name="resource_edit",
    ),
    path(
        "resources/<hashid:pk>/delete/",
        views.CourseResourceDeleteView.as_view(),
        name="resource_delete",
    ),
]
