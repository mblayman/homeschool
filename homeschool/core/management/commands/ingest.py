import csv
import datetime
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from homeschool.courses.models import Course, CourseTask, GradedWork
from homeschool.schools.models import GradeLevel, School, SchoolYear
from homeschool.students.models import Coursework, Enrollment, Grade, Student

User = get_user_model()

COURSE_DAYS = {
    "Art 2": 1,
    "Art K": 1,
    "Bible 2": 0,
    "Bible K": 21,
    "Bible OT": 21,
    "Handwriting 2": 18,
    "Health 2": 17,
    "Health K": 17,
    "History 2": 11,
    "History K": 25,
    "Math 2": 31,
    "Math K": 31,
    "Math 1": 31,
    "Music 2": 19,
    "Music K": 2,
    "PE 2": 4,
    "PE K": 4,
    "Penmanship 1": 18,
    "Reading 2": 31,
    "Reading Aloud K": 31,
    "Reading Instruction K": 31,
    "Science 2": 26,
    "Science K": 26,
    "Spelling 2": 18,
    "Sustained Silent Reading 2": 10,
    "Sustained Silent Reading K": 10,
    "Wiggle Room": 31,
    "Writing & Grammar 2": 25,
}


class Command(BaseCommand):
    help = "Ingest CSV data from Homeschool Skedtrack"

    def add_arguments(self, parser):
        parser.add_argument("email")

    def handle(self, *args, **options):
        self.stdout.write("Check for user")
        user = User.objects.get(email=options["email"])

        school_year = self.persist_school_year(user)

        grades = {"Faye": "Kindergarten", "Mark": "2nd Grade"}
        self.stdout.write("Read in CSV data")
        for dirpath, dirnames, filenames in os.walk("courses_exports"):
            # Skip the root directory.
            if dirnames:
                continue

            courses = []
            student = dirpath.split("/")[-1]
            for filename in filenames:
                course_name = filename.strip(".csv")
                courses.append(
                    self.process_course(course_name, f"{dirpath}/{filename}")
                )

            self.persist_grade(
                school_year, grades[student], f"{student} Layman", courses
            )

    def process_course(self, course_name, file_path):
        self.stdout.write(f"Processing {course_name}...")
        with open(file_path) as csv_file:
            reader = csv.reader(csv_file.readlines())

        searching_tasks = True
        sequence = 1
        tasks = []
        row_length = 1
        for row in reader:
            if searching_tasks:
                # Stop searching after finding the task column labels.
                if row and row[0] == "Sequence":
                    searching_tasks = False
                    row_length = len(row)
                continue

            # Skip rows that are totally empty.
            if not row:
                continue

            try:
                if sequence == int(row[0]):
                    tasks.append(row)
                    sequence += 1
            except ValueError:
                # Hit extra line from poor description wrapping.
                # Join this to the previous task.
                tasks[-1][-1] = "\n".join([tasks[-1][-1], row[0]])
                tasks[-1].extend(row[1:])

        # Clean up the cases when there were commas in the descriptions.
        description_index = 3
        for task in tasks:
            while len(task) != row_length:
                more_description = task.pop(description_index + 1)
                task[description_index] = ", ".join(
                    [task[description_index], more_description]
                )

        return {"name": course_name, "tasks": tasks}

    def persist_school_year(self, user):
        self.stdout.write("Create school and school year.")
        school = School.objects.create(admin=user)
        start_date = datetime.date(2020, 1, 1)
        end_date = start_date + datetime.timedelta(days=365)
        school_year = SchoolYear.objects.create(
            school=school, start_date=start_date, end_date=end_date
        )
        return school_year

    def persist_grade(self, school_year, grade_level_name, student_full_name, courses):
        """Create a school with all its records."""
        # Create all school related instances.
        grade_level = GradeLevel.objects.create(
            name=grade_level_name, school_year=school_year
        )

        # Create student.
        student_name = student_full_name.split()
        student = Student.objects.create(
            school=school_year.school,
            first_name=student_name[0],
            last_name=student_name[1],
        )
        Enrollment.objects.create(student=student, grade_level=grade_level)

        for course_dict in courses:
            days_of_week = None
            if course_dict["name"] in COURSE_DAYS:
                days_of_week = COURSE_DAYS[course_dict["name"]]
            else:
                self.stdout.write(
                    "Failed to find course days for {}".format(course_dict["name"])
                )
            course = Course.objects.create(
                name=course_dict["name"], days_of_week=days_of_week
            )
            course.grade_levels.add(grade_level)

            for task in course_dict["tasks"]:
                course_task = CourseTask.objects.create(
                    course=course, description=task[3], duration=int(task[2])
                )
                if task[1]:
                    completed_date = datetime.datetime.strptime(task[1], "%m/%d/%Y")
                    Coursework.objects.create(
                        student=student,
                        course_task=course_task,
                        completed_date=completed_date,
                    )
                if task[4] != "Regular":
                    graded_work = GradedWork.objects.create(course_task=course_task)
                    if task[5]:
                        score = None
                        try:
                            score = int(task[5])
                        except ValueError:
                            # This should handle the small edge case
                            # when there are commas in an optional grade description.
                            # Start from the end and look for the grade number.
                            # The CSV output is so bad that it could be
                            # in various places depending on the number of commas.
                            index = len(task) - 1
                            # If it's not found by the description at index 3,
                            # something is very wrong.
                            while index >= 3:
                                try:
                                    score = int(task[index].split(",")[-1].strip())
                                    break
                                except ValueError:
                                    pass
                                index -= 1
                        if score is None:
                            raise Exception("Failed to find grade.")
                        Grade.objects.create(
                            student=student, graded_work=graded_work, score=score
                        )
