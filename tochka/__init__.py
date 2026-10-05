"""Compatibility shims for the tochka project.

Django 6.1 removed ``django.utils.cache.cc_delim_re``, but Django REST
Framework (a dependency of Wagtail) still imports it from
``rest_framework/views.py``. We restore the constant until an upstream
fix lands. The value matches what Django 6.0 shipped.
"""

import re

import django.utils.cache as _django_cache

if not hasattr(_django_cache, "cc_delim_re"):
    _django_cache.cc_delim_re = re.compile(r"\s*,\s*")
