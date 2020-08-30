from dateutil.relativedelta import SA, SU, relativedelta


class Week:
    """A basic data class to represent a week."""

    def __init__(self, day):
        self.first_day = day + relativedelta(weekday=SU(-1))
        self.last_day = day + relativedelta(weekday=SA(+1))

    def __str__(self):
        return f"{self.first_day} - {self.last_day}"

    def __iter__(self):
        """Make it possible to iterate over the week.

        This makes it easy to use the week in a range query.
        """
        yield self.first_day
        yield self.last_day
