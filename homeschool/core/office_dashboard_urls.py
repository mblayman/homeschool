from django.urls import include, path

from .views import boom, handle_500, office_dashboard, office_onboarding, social_image

app_name = "office"
urlpatterns = [
    path("", office_dashboard, name="dashboard"),
    path("onboarding/", office_onboarding, name="onboarding"),
    path("boom/", boom, name="boom"),
    path("pdfs/", include("homeschool.reports.office_urls")),
    path("social-image/", social_image, name="social_image"),
    path("500/", handle_500, name="handle_500"),
]
