from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def app(request):
    context = {}
    return render(request, "schools/app.html", context)
