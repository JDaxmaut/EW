from pathlib import Path
try:
    from decouple import config
except ImportError:
    def config(key, default=None, cast=None):
        import os
        val = os.environ.get(key, default)
        return cast(val) if (cast and val is not None) else val

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="django-insecure-dev-key-change-in-production")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="http://localhost:8000").split(",")

# ── Безопасность транспорта ────────────────────────────────────
# За прокси (nginx) отдаётся только HTTPS, поэтому считаем запросы
# пришедшими по HTTPS, если nginx проставил X-Forwarded-Proto.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# HSTS — браузер запоминает «только HTTPS» на год.
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

# ── Куки ───────────────────────────────────────────────────────
# Secure-куки работают только по HTTPS. На локальной разработке по HTTP
# они не сохраняются — и логин в админку падает с 403. Поэтому включаем
# их только когда DEBUG выключен (то есть на боевом сервере за nginx).
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = not DEBUG
# CSRF_COOKIE_HTTPONLY сознательно НЕ включаем — Wagtail admin читает
# csrftoken из куки для AJAX-запросов (X-Csrftoken).
CSRF_COOKIE_SAMESITE = "Lax"

INSTALLED_APPS = [
    # Wagtail
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.contrib.sitemaps",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    # Third-party
    "modelcluster",
    "taggit",
    "tailwind",
    "theme",
    "admin_ui",
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
    # Project
    "trips",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "tochka.security_middleware.SecurityHeadersMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

ROOT_URLCONF = "tochka.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "trips" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "trips.context_processors.site_settings",
            ],
        },
    }
]

WSGI_APPLICATION = "tochka.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(config("DB_PATH", default=str(BASE_DIR / "db.sqlite3"))),
        "OPTIONS": {"timeout": 20},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

YANDEX_METRIKA_ID = config("YANDEX_METRIKA_ID", default="")
TELEGRAM_URL = config("TELEGRAM_URL", default="")
WHATSAPP_URL = config("WHATSAPP_URL", default="")
MAX_URL = config("MAX_URL", default="")

# Названия, которые повторяются в шаблонах
SITE_NAME = "Нескучные выходные"
COMPANY_NAME = "ООО ТТЦ «Нескучные выходные»"
COMPANY_INN = "ИНН 2365039032 · ОГРН 1262300039231"
SITE_TAGLINE = "поездки на море"
SITE_REGION = "Краснодарский край"

# Контакты — как в макете EWsite
PHONE = config("PHONE", default="+7 918 363-20-87")
PHONE_HREF = config("PHONE_HREF", default="+79183632087")
EMAIL = config("EMAIL", default="vkilimova@mail.ru")
ADDRESS = config(
    "ADDRESS",
    default=(
        "352630, Краснодарский край, р-н Белореченский, "
        "г. Белореченск, пер. Ломанный, д. 2"
    ),
)
BANK_DETAILS = config(
    "BANK_DETAILS",
    default=(
        "Р/с 40702810720000371364, БИК 044525104"
        "<br>к/с 30101810745374525104"
    ),
)

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# django-tailwind
TAILWIND_APP_NAME = "theme"
NPM_BIN_PATH = r"C:\Program Files\nodejs\npm.cmd"
INTERNAL_IPS = ["127.0.0.1"]

# Wagtail
WAGTAIL_SITE_NAME = "Нескучные выходные"
COMPANY_NAME = "ООО ТТЦ «Нескучные выходные»"
COMPANY_INN = "ИНН 2365039032 · ОГРН 1262300039231"
WAGTAILADMIN_BASE_URL = config("WAGTAILADMIN_BASE_URL", default="http://localhost:8000")

LOGIN_URL = "/cms/login/"
LOGIN_REDIRECT_URL = "/cms/"
WAGTAIL_I18N_ENABLED = False

from PIL import ImageFile as _PILImageFile
_PILImageFile.LOAD_TRUNCATED_IMAGES = True

WAGTAILIMAGES_WEBP_QUALITY = 88
WAGTAILIMAGES_JPEG_QUALITY = 88
WAGTAILIMAGES_FORMAT_CONVERSIONS = {
    "jpeg": "webp",
    "jpg": "webp",
    "png": "webp",
}
