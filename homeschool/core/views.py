from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView


class IndexView(TemplateView):
    template_name = "core/index.html"


class AppView(LoginRequiredMixin, TemplateView):
    template_name = "core/app.html"
