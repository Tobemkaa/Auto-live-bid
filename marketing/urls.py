from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="marketing_home"),
    path("about/", views.about, name="marketing_about"),
    path("services/", views.services, name="marketing_services"),
    path("inventory/", views.inventory, name="marketing_inventory"),
    path("testimonials/", views.testimonials, name="marketing_testimonials"),
    path("contact/", views.contact, name="marketing_contact"),
]