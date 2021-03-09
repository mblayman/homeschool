from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    """The sitemap for static pages template views delivered by the app.

    Other static content is managed by other sitemaps (e.g., blog and docs)
    """

    changefreq = "daily"

    def items(self):
        return ["core:index", "core:about", "core:terms", "core:privacy", "core:help"]

    def location(self, item):
        return reverse(item)


sitemaps = {"static": StaticViewSitemap}
