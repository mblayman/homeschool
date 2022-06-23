import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from homeschool.core.schedules import Week


@login_required
def checklist(request: HttpRequest, year: int, month: int, day: int) -> HttpResponse:
    """Display a checklist of all the student tasks for a week."""
    week_day = datetime.date(year, month, day)
    week = Week(week_day)
    context: dict = {"week": week}
    return render(request, "teachers/checklist.html", context)
