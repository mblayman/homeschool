from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic.base import TemplateView


class IndexView(TemplateView):
    template_name = "core/index.html"


@login_required
def app(request):
    context = {}
    return render(request, "core/app.html", context)
