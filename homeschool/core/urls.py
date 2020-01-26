from django.urls import path

from homeschool.core import views

app_name = "core"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("app/", views.AppView.as_view(), name="app"),
]
