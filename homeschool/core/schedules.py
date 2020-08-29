from dateutil.relativedelta import SA, SU, relativedelta


class Week:
    """A basic data class to represent a week."""

    def __init__(self, day):
        self.first_day = day + relativedelta(weekday=SU(-1))
        self.last_day = day + relativedelta(weekday=SA(+1))
