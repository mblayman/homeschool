from django.contrib import admin


class AdminSite(admin.AdminSite):
    index_title = "Office"
    site_header = "School Desk"
    site_title = "School Desk"
