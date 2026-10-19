from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return [
            "marketing_home", "marketing_about", "marketing_services",
            "marketing_inventory", "marketing_testimonials", "marketing_contact",
        ]

    def location(self, item):
        return reverse(item)