class FullEnrollmentError(Exception):
    """An error when a school year is fully enrolled."""


class NoGradeLevelError(Exception):
    """An error when no appropriate grade levels are available."""


class NoStudentError(Exception):
    """An error when no appropriate students are available."""
