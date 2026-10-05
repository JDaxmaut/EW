from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

from trips.sitemaps import sitemap
from trips.views import (
    contact_submit,
    cookie_accept,
    legal_index_view,
    robots_txt,
    schedule_view,
    search as search_view,
)

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("cms/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("sitemap.xml", sitemap, name="wagtail_sitemap"),
    path("search/", search_view, name="search"),
    path("schedule/", schedule_view, name="schedule"),
    path("legal/", legal_index_view, name="legal_index"),
    path("cookie-accept/", cookie_accept, name="cookie_accept"),
    path("api/contact/", contact_submit, name="contact_submit"),
    path(
        "robots.txt",
        robots_txt,
        name="robots_txt",
    ),
    path("", include(wagtail_urls)),
] + [
    re_path(r"^media/(?P<path>.+)$", serve, {"document_root": settings.MEDIA_ROOT}),
]