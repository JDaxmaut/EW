"""Реквизиты turоператора читаются прямо из договора-оферты.

Единственный источник истины — раздел «РЕКВИЗИТЫ ТУРОПЕРАТОРА» на странице
/offer/. Пока он есть в базе, сайт показывает те же данные, что и договор:
название, ИНН/ОГРН, адрес, телефон, почту и банковские счета. Значения из .env
используются только как запасной вариант, если раздел не удалось разобрать.
"""

import html
import re

HEADING_RE = re.compile(r"РЕКВИЗИТЫ\s+ТУРОПЕРАТОРА", re.IGNORECASE)
STOP_RE = re.compile(r"Приложение\s+к\s+[Дд]оговору")
PARAGRAPH_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.DOTALL)

# Ключи и их подписи в тексте договора.
FIELDS = {
    "inn": r"ИНН",
    "ogrn": r"ОГРН",
    "address": r"Место\s+нахождения",
    "post_address": r"Почтовый\s+адрес",
    "phone": r"Тел",
    "email": r"e-?mail",
    "site": r"Интернет-сайт",
    "account": r"Р\s*/?\s*с",
    "bik": r"БИК",
    "ks": r"к\s*\.?\s*/?\s*с",
}


def _clean(fragment: str) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", fragment))
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def _section_lines(body: str) -> list[str]:
    """Строки раздела «РЕКВИЗИТЫ ТУРОПЕРАТОРА» — до первого «Приложение к договору»."""
    heading = HEADING_RE.search(body or "")
    if not heading:
        return []
    tail = body[heading.end():]
    stop = STOP_RE.search(tail)
    chunk = tail[:stop.start()] if stop else tail
    return [_clean(p) for p in PARAGRAPH_RE.findall(chunk)]


def parse_requisites(body: str) -> dict:
    """Разбирает тело оферты и возвращает реквизиты по ключам FIELDS."""
    lines = _section_lines(body)
    if not lines:
        return {}

    result: dict[str, str] = {}
    # Название идёт первой строкой без двоеточия — «ООО ТТЦ "НЕСКУЧНЫЕ ВЫХОДНЫЕ"».
    for line in lines:
        if line and ":" not in line and not re.match(rf"^{FIELDS['bik']}|^{FIELDS['ks']}", line):
            result["name"] = line
            break

    for key, label in FIELDS.items():
        pattern = re.compile(rf"^{label}\s*[:.]?\s*(.*)$", re.IGNORECASE)
        for line in lines:
            match = pattern.match(line)
            if match:
                value = match.group(1).strip(" .:")
                if value:
                    result[key] = value
                break

    return result


def inn_line(req: dict) -> str:
    """«ИНН 2365039032 · ОГРН 1262300039231» — только то, что есть в договоре."""
    parts = []
    if req.get("inn"):
        parts.append(f"ИНН {req['inn']}")
    if req.get("ogrn"):
        parts.append(f"ОГРН {req['ogrn']}")
    return " · ".join(parts)


def bank_line(req: dict) -> str:
    """Банковские реквизиты одной строкой. HTML — чтобы перенос строки был явным."""
    parts = []
    if req.get("account"):
        parts.append(f"Р/с {req['account']}, БИК {req.get('bik', '')}".rstrip(" ,"))
    if req.get("ks"):
        parts.append(f"к/с {req['ks']}")
    return "<br>".join(parts)


def phone_href(req: dict) -> str:
    digits = re.sub(r"\D", "", req.get("phone", ""))
    if digits.startswith("8"):
        digits = "7" + digits[1:]
    return f"+{digits}" if digits else ""


def format_phone(phone: str) -> str:
    """+79183632087 -> «+7 918 363-20-87». Неизвестный формат — как есть."""
    raw = (phone or "").strip()
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("8"):
        digits = "7" + digits[1:]
    if len(digits) == 11 and digits.startswith("7"):
        return f"+7 {digits[1:4]} {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    return raw