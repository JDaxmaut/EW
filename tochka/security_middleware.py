from django.conf import settings

ADMIN_PREFIXES = ("/tochka-cms/", "/django-admin/", "/documents/")


def _csp_header():
    extra_script = ""
    if getattr(settings, "CSP_EXTRA_SCRIPT_SRC", None):
        extra_script = " " + " ".join(settings.CSP_EXTRA_SCRIPT_SRC)
    return "; ".join([
        "default-src 'self'",
        f"script-src 'self' 'unsafe-inline' 'unsafe-eval'"
        f" https://cdn.jsdelivr.net https://mc.yandex.ru{extra_script}",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com",
        "img-src 'self' data: https://mc.yandex.ru",
        "connect-src 'self' https://mc.yandex.ru https://mc.yandex.com",
        "media-src 'self'",
        "object-src 'none'",
        "frame-src 'none'",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "upgrade-insecure-requests",
    ])


class SecurityHeadersMiddleware:
    """Добавляет CSP и Permissions-Policy на публичные HTML-страницы.

    Админка (Wagtail/Django) использует много инлайн-стилей и сторонних
    ресурсов, поэтому CSP на неё не вешаем — иначе она может сломаться.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        path = request.path

        if path.startswith(ADMIN_PREFIXES):
            return response
        if response.get("Content-Security-Policy"):
            return response
        if not response.get("Content-Type", "").startswith("text/html"):
            return response

        response["Content-Security-Policy"] = _csp_header()
        response["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
        )
        return response
