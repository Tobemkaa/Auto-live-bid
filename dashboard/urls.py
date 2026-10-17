from django.urls import path
from . import views

urlpatterns = [
    path("home", views.home, name="dashboard_home")
]
