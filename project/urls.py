from denied.decorators import allow
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include, path, register_converter
from sesame.views import LoginView

from homeschool.accounts.views import check_email, signin
from homeschool.core.converters import HashidConverter
from homeschool.core.views import favicon, handle_403, handle_404, handle_500

register_converter(HashidConverter, "hashid")

urlpatterns = [
    path("", include("homeschool.core.urls")),
    path("courses/", include("homeschool.courses.urls")),
    path("notifications/", include("homeschool.notifications.urls")),
    path("office/", allow(admin.site.urls)),
    path("office-dashboard/", include("homeschool.core.office_dashboard_urls")),
    path("reports/", include("homeschool.reports.urls")),
    path("schools/", include("homeschool.schools.urls")),
    path("settings/", include("homeschool.users.settings_urls")),
    path("check-email", check_email, name="check-email"),
    path("login", allow(LoginView.as_view()), name="sesame-login"),
    path("logout", allow(LogoutView.as_view()), name="logout"),
    path("signin", signin, name="signin"),
    path("students/", include("homeschool.students.urls")),
    path("subscriptions/", include("homeschool.accounts.subscriptions_urls")),
    path("teachers/", include("homeschool.teachers.urls")),
    path("hijack/", allow(include("hijack.urls"))),
    path("stripe/", allow(include("djstripe.urls", namespace="djstripe"))),
    path("tz_detect/", allow(include("tz_detect.urls"))),
    path("favicon.ico", favicon, name="favicon"),
]

handler403 = handle_403
handler404 = handle_404
handler500 = handle_500

# Enable the debug toolbar only in DEBUG mode.
if settings.DEBUG and settings.DEBUG_TOOLBAR:
    urlpatterns = [
        path("__debug__/", allow(include("debug_toolbar.urls")))
    ] + urlpatterns
