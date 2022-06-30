import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from homeschool.core.schedules import Week
from homeschool.schools.models import SchoolYear


@login_required
def checklist(request: HttpRequest, year: int, month: int, day: int) -> HttpResponse:
    """Display a checklist of all the student tasks for a week."""
    today = request.user.get_local_today()
    week_day = datetime.date(year, month, day)
    week = Week(week_day)

    school_year = SchoolYear.get_year_for(request.user, week_day)

    schedules = []
    if school_year:
        schedules = school_year.get_schedules(today, week)

    context = {"schedules": schedules, "week": week}
    return render(request, "teachers/checklist.html", context)
