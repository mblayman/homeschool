import csv
import datetime
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from homeschool.courses.models import Course, CourseTask
from homeschool.schools.models import GradeLevel, School, SchoolYear
from homeschool.students.models import Coursework, Enrollment, Student

User = get_user_model()


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
        with open(file_path, "r") as csv_file:
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
        start_date = datetime.date.today()
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
            course = Course.objects.create(
                name=course_dict["name"], grade_level=grade_level
            )
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
