from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def ru_plural(value, forms):
    """Русские окончания: {{ count|ru_plural:"место,места,мест" }}"""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return forms.split(",")[-1]

    forms = forms.split(",")
    n10 = n % 10
    n100 = n % 100
    if n10 == 1 and n100 != 11:
        return forms[0]
    if 2 <= n10 <= 4 and not (12 <= n100 <= 14):
        return forms[1]
    return forms[2] if len(forms) > 2 else forms[1]


@register.filter
def month_key(value):
    """Ключ месяца для группировки: YYYY-MM"""
    try:
        return value.strftime("%Y-%m")
    except AttributeError:
        return ""


@register.filter
def take(queryset, count):
    """Ограничить количество элементов QuerySet числом из блока."""
    try:
        return queryset[: int(count)]
    except (TypeError, ValueError):
        return queryset


@register.filter
def price(value):
    """1900 → «1 900»"""
    try:
        return f"{int(value):,}".replace(",", " ")
    except (TypeError, ValueError):
        return value

# В шаблонах фильтр зовётся короче: {{ n|ruplural:"место,места,мест" }}
ruplural = ru_plural
register.filter("ruplural", ru_plural)


import re

# Абзац-маркер дня в программе: <p><strong>День 1</strong></p>
_DAY_MARKER_RE = re.compile(
    r"<p[^>]*>\s*<strong[^>]*>\s*День\s*(\d+)\s*</strong>\s*</p>",
    re.IGNORECASE,
)


@register.filter
def program_days(value):
    """Разбить программу (одно текстовое поле) на дни по абзацам «День N».

    Возвращает [] меньше двух дней — тогда шаблон рендерит текст целиком.
    Для многодневки получается список {"number": int, "html": str} —
    по нему собирается аккордеон «День 1 / День 2 / …».
    """
    html = str(value or "")
    marks = list(_DAY_MARKER_RE.finditer(html))
    if len(marks) < 2:
        return []
    days = []
    for i, m in enumerate(marks):
        start = m.end()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(html)
        days.append({"number": int(m.group(1)), "html": html[start:end].strip()})
    return days
