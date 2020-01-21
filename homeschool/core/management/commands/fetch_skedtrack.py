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
        self.get_authenticated_session()
        ids = self.get_download_ids()

        # TODO: Select student.

        out_dir = "courses_exports"
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)

        for course_id in ids:
            time.sleep(5)
            self.fetch_course(course_id, out_dir)

    def get_authenticated_session(self):
        """Get a session to use to communicate with Homeschool Skedtrack."""
        self.stdout.write("Get session token")
        username = os.environ["SKEDTRACK_USER"]
        password = os.environ["SKEDTRACK_PASSWORD"]

        session = requests.Session()

        login_url = f"{self.url}/login.do"
        session.post(login_url, data={"userName": username, "password": password})
        self.session = session

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

        # Yeah, it's a side effect. Whatever.
        enrollment_option = soup.find(id="enrollmentId").find("option", selected=True)
        self.enrollment_id = enrollment_option["value"]

        inputs = soup.find_all("input", attrs={"name": "download"})
        return [input_tag["value"] for input_tag in inputs]

    def fetch_course(self, course_id, out_dir):
        """Fetch a course and write it to a CSV file."""
        self.stdout.write(f"Fetch course data for {course_id}")
        download_url = f"{self.url}/download.do?fileType=csv"
        response = self.session.post(
            download_url,
            data={"download": course_id, "enrollmentId": self.enrollment_id},
        )

        csv_data = io.StringIO(response.text)
        course_name = csv_data.readline().split(":")[1].strip()
        csv_file_name = f"{out_dir}/{course_name}.csv"
        self.stdout.write(f"Writing out CSV at {csv_file_name}")
        with open(csv_file_name, "w") as f:
            f.write(response.text)
