from django.urls import path

from . import views

app_name = "teachers"
urlpatterns = [
    path(
        "checklist/<int:year>/<int:month>/<int:day>/", views.checklist, name="checklist"
    ),
    path(
        "checklist/<int:year>/<int:month>/<int:day>/edit/",
        views.edit_checklist,
        name="edit_checklist",
    ),
]
