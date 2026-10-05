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
