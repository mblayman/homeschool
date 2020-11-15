"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from homeschool.core.views import boom, handle_500

urlpatterns = [
    path("", include("homeschool.core.urls")),
    path("courses/", include("homeschool.courses.urls")),
    path("notifications/", include("homeschool.notifications.urls")),
    path("office/", admin.site.urls),
    path("office/boom/", boom, name="boom"),
    path("office/500/", handle_500, name="handle_500"),
    path("reports/", include("homeschool.schools.report_urls")),
    path("schools/", include("homeschool.schools.urls")),
    path("students/", include("homeschool.students.urls")),
    path("accounts/", include("allauth.urls")),
    path("hijack/", include("hijack.urls")),
    path("tz_detect/", include("tz_detect.urls")),
]

handler500 = handle_500

# Enable the debug toolbar only in DEBUG mode.
if settings.DEBUG and settings.DEBUG_TOOLBAR:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
