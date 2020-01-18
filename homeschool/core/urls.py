from django.urls import path

from homeschool.core import views

app_name = "core"
urlpatterns = [path("app/", views.app, name="app")]
