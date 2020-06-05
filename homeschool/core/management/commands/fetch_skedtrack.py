import io
import os
import time

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Fetch courses from Homeschool Skedtrack"
    url = "http://www.homeschoolskedtrack.com/HomeSchool"

    def handle(self, *args, **kwargs):
        self.students: dict = {}
        self.get_authenticated_session()

        out_dir = "courses_exports"
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)

        for student_name, enrollment_id in self.students.items():
            student_out_dir = os.path.join(out_dir, student_name)
            if not os.path.exists(student_out_dir):
                os.mkdir(student_out_dir)

            self.set_session_for(enrollment_id)
            time.sleep(5)
            ids = self.get_download_ids()
            for course_id in ids:
                time.sleep(5)
                self.fetch_course(course_id, enrollment_id, student_out_dir)

    def get_authenticated_session(self):
        """Get a session to use to communicate with Homeschool Skedtrack."""
        self.stdout.write("Get session token")
        username = os.environ["SKEDTRACK_USER"]
        password = os.environ["SKEDTRACK_PASSWORD"]

        session = requests.Session()

        login_url = f"{self.url}/login.do"
        response = session.post(
            login_url, data={"userName": username, "password": password}
        )
        self.set_students(response.text)
        self.session = session

    def set_students(self, login_response_text):
        """Get the students and the their enrollment ID from the login response."""
        soup = BeautifulSoup(login_response_text, "html.parser")
        enrollment_select = soup.find(id="enrollmentId")
        for option in enrollment_select.find_all("option"):
            self.students[option.text.split(",")[0]] = option["value"]

    def set_session_for(self, enrollment_id):
        """Set the Homeschool Skedtrack session to the provided enrollment."""
        self.stdout.write(f"Set session for {enrollment_id}")
        select_student_url = (
            f"{self.url}/selectTeacherStudent.do?enrollmentId={enrollment_id}"
        )
        self.session.get(select_student_url)

    def get_download_ids(self):
        self.stdout.write("Get download ids")
        display_downloads_url = f"{self.url}/displayDownloads.do"
        response = self.session.get(display_downloads_url)
        response_text = response.text

        # with open("downloads.html", "w") as f:
        #     f.write(response_text)
        # with open("downloads.html", "r") as f:
        #     response_text = f.read()

        soup = BeautifulSoup(response_text, "html.parser")
        inputs = soup.find_all("input", attrs={"name": "download"})
        return [input_tag["value"] for input_tag in inputs]

    def fetch_course(self, course_id, enrollment_id, out_dir):
        """Fetch a course and write it to a CSV file."""
        self.stdout.write(f"Fetch course data for {course_id}")
        download_url = f"{self.url}/download.do?fileType=csv"
        response = self.session.post(
            download_url, data={"download": course_id, "enrollmentId": enrollment_id}
        )

        csv_data = io.StringIO(response.text)
        course_name = csv_data.readline().split(":")[1].strip()

        # Some of the IDs are for resources and not courses.
        # If there is no course name, then it was one of those special files.
        if not course_name:
            return

        csv_file_name = f"{out_dir}/{course_name}.csv"
        self.stdout.write(f"Writing out CSV at {csv_file_name}")
        with open(csv_file_name, "w") as f:
            f.write(response.text)
