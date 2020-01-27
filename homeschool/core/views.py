from dateutil.relativedelta import MO, SU, relativedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic.base import TemplateView

from homeschool.schools.models import SchoolYear


class IndexView(TemplateView):
    template_name = "core/index.html"


class AppView(LoginRequiredMixin, TemplateView):
    template_name = "core/app.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        today = timezone.now().date()
        context["monday"], context["sunday"] = self.get_week_boundaries(today)

        school_year = (
            SchoolYear.objects.filter(start_date__lte=today, end_date__gte=today)
            .prefetch_related("grade_levels", "grade_levels__courses")
            .first()
        )

        context["schedules"] = self.get_schedules(
            school_year, context["monday"], context["sunday"]
        )
        return context

    def get_week_boundaries(self, today):
        """Get the Monday and Sunday that bound today."""
        monday = today + relativedelta(weekday=MO(-1))
        sunday = today + relativedelta(weekday=SU(+1))
        return monday, sunday

    def get_schedules(self, school_year, monday, sunday):
        """Get the schedules for each student."""
        schedules = []
        if school_year is None:
            return schedules

        for student in self.request.user.school.students.all():
            courses = student.get_courses(school_year)
            schedule = {"student": student, "courses": courses}
            schedules.append(schedule)

        return schedules
