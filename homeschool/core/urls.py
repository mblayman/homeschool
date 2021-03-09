from django.urls import include, path
from django.views.generic import TemplateView

from homeschool.core import views

app_name = "core"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path(
        "robots.txt",
        TemplateView.as_view(
            template_name="core/robots.txt", content_type="text/plain"
        ),
        name="robots",
    ),
    path(
        "sitemapindex.xml",
        TemplateView.as_view(
            template_name="core/sitemapindex.xml", content_type="text/xml"
        ),
        name="sitemapindex",
    ),
    path("about/", TemplateView.as_view(template_name="core/about.html"), name="about"),
    path("terms/", TemplateView.as_view(template_name="core/terms.html"), name="terms"),
    path(
        "privacy/",
        TemplateView.as_view(template_name="core/privacy.html"),
        name="privacy",
    ),
    path("help/", views.HelpView.as_view(), name="help"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path(
        "weekly/<int:year>/<int:month>/<int:day>/",
        views.DashboardView.as_view(),
        name="weekly",
    ),
    path("daily/", views.DailyView.as_view(), name="daily"),
    path(
        "daily/<int:year>/<int:month>/<int:day>/",
        views.DailyView.as_view(),
        name="daily_for_date",
    ),
    path("start/", include("homeschool.core.start_urls")),
]
