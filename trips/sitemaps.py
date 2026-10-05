import re

from django.conf import settings
from wagtail.contrib.sitemaps.views import sitemap as wagtail_sitemap


def _rewrite_host(match):
    path = match.group(1)
    base = settings.WAGTAILADMIN_BASE_URL.rstrip("/")
    return f"<loc>{base}{path}</loc>"


def sitemap(request):
    response = wagtail_sitemap(request)
    if settings.WAGTAILADMIN_BASE_URL and response.status_code == 200:
        response.render()
        content = response.content.decode("utf-8")
        # Только URL внутри <loc>, а не XML-namespace (иначе ломается валидность sitemap)
        content = re.sub(
            r"<loc>https?://(?:[^/]+)(/[^<]*)</loc>",
            _rewrite_host,
            content,
        )
        response.content = content.encode("utf-8")
        response["Content-Length"] = str(len(response.content))
    return response
