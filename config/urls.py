"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.views.static import serve
from django.contrib.sitemaps.views import sitemap
from marketing.sitemaps import StaticViewSitemap


admin.site.site_header = "Auto Live-Bid Naija"
admin.site.site_title = "Auto Live-Bid Naija Admin"
admin.site.index_title = "Operations"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("dashboard/", include("dashboard.urls")),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(next_page="marketing_home"), name="logout"),
    path("", include("marketing.urls")),
]


urlpatterns += [
    path("media/<path:path>", serve, {"document_root": settings.MEDIA_ROOT}),
]

urlpatterns += [
    path("sitemap.xml", sitemap, {"sitemaps": {"static": StaticViewSitemap()}}),
]