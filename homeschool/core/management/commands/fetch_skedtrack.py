import os

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Fetch courses from Homeschool Skedtrack"

    def handle(self, *args, **kwargs):
        session = self.get_authenticated_session()
        self.get_download_ids(session)

    def get_download_ids(self, session):
        display_downloads_url = (
            "http://www.homeschoolskedtrack.com/HomeSchool/displayDownloads.do"
        )
        # response = session.get(display_downloads_url)
        # response_text = response.text
        # with open("downloads.html", "w") as f:
        #     f.write(response_text)
        with open("downloads.html", "r") as f:
            response_text = f.read()
        soup = BeautifulSoup(response_text, "html.parser")
        inputs = soup.find_all("input", attrs={"name": "download"})
        for input_tag in inputs:
            print(input_tag["value"])

    def get_authenticated_session(self):
        """Get a session to use to communicate with Homeschool Skedtrack."""
        self.stdout.write("Get session token")
        username = os.environ["SKEDTRACK_USER"]
        password = os.environ["SKEDTRACK_PASSWORD"]

        session = requests.Session()

        login_url = "http://www.homeschoolskedtrack.com/HomeSchool/login.do"
        # session.post(login_url, data={"userName": username, "password": password})
        return session
