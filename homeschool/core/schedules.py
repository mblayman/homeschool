from dateutil.relativedelta import MO, SU, relativedelta


class Week:
    """A basic data class to represent a week."""

    def __init__(self, day):
        self.monday = day + relativedelta(weekday=MO(-1))
        self.sunday = day + relativedelta(weekday=SU(+1))
