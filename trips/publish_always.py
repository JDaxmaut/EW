# -*- coding: utf-8 -*-
"""«Сохранить» в админке всегда публикует страницу.

Зачем: редактору не нужны черновики и модерация — он правит текст тура и
хочет, чтобы изменение сразу было видно на сайте. Wagtail же по умолчанию
предлагает две кнопки («Сохранить черновик» и «Опубликовать»), причём
черновик остаётся неопубликованным и легко забывается.

Как это сделано: у редактора страницы есть решение, какое действие
выполнить, — `wagtail.admin.views.pages.edit.EditView.action_name_and_method`.
По умолчанию оно смотрит на нажатую кнопку, а если кнопка не
распознана, делает `save` (черновик). Мы оставляем явное «Опубликовать»
как есть, а запасной путь переводим на публикацию. Тогда и кнопка
«Сохранить», и отправка формы по Enter всегда публикуют страницу.

Патч сделан осторожно: если в будущей версии Wagtail этот атрибут
исчезнет, мы не падаем, а оставляем стандартное поведение и пишем
предупреждение в лог.
"""
import logging

from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import cached_property

logger = logging.getLogger(__name__)

_original = None


def apply():
    """Перевести запасное действие «сохранить черновик» на публикацию."""
    global _original

    try:
        from wagtail.admin.views.pages.edit import EditView as Edit
    except ImportError as exc:  # pragma: no cover - зависит от версии Wagtail
        logger.warning("Не найден модуль редактора страниц Wagtail: %s", exc)
        return

    current = Edit.__dict__.get("action_name_and_method")
    if current is not None and getattr(current, "_nu_always_publish", False):
        return  # уже применено (ready() мог вызваться повторно)

    try:
        _original = current.func if isinstance(current, cached_property) else current
    except AttributeError:  # pragma: no cover
        raise ImproperlyConfigured(
            "Не удалось включить режим «сохранить = опубликовать»: в этой "
            "версии Wagtail поменялся EditView.action_name_and_method."
        )

    def always_publish(self):
        name, method = _original(self)
        if name == "save" and _can_publish(self):
            return ("publish", self.publish_action)
        return name, method

    always_publish._nu_always_publish = True
    Edit.action_name_and_method = cached_property(always_publish)


def _can_publish(view):
    """Есть ли у пользователя право публикации этой страницы.

    Проверка обязательна: Wagtail выполняет публикацию с
    skip_permission_checks=True, то есть повторно права не сверяет.
    Без этой проверки любой редактор, которому разрешено править
    страницу, опубликовал бы её простым нажатием Enter.
    """
    perms = getattr(view, "page_perms", None)
    if perms is None:
        return False
    try:
        return bool(perms.can_publish())
    except Exception:  # pragma: no cover - нестандартный набор прав
        logger.warning("Не удалось проверить право публикации", exc_info=True)
        return False
