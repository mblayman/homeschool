from denied.decorators import allow
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from homeschool.core import views
from homeschool.core.sitemaps import sitemaps

app_name = "core"
urlpatterns = [
    path("", views.index, name="index"),
    path("robots.txt", views.robots, name="robots"),
    path("sitemapindex.xml", views.sitemapindex, name="sitemapindex"),
    path("sitemap.xml", allow(sitemap), {"sitemaps": sitemaps}, name="sitemap"),
    path("about/", views.about, name="about"),
    path("terms/", views.terms, name="terms"),
    path("privacy/", views.privacy, name="privacy"),
    path("help/", views.help, name="help"),
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
