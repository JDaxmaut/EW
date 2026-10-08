from wagtail import blocks
from wagtail.blocks import (
    CharBlock,
    ListBlock,
    RichTextBlock,
    StaticBlock,
    TextBlock,
)
from wagtail.images.blocks import ImageChooserBlock


# ─────────────── Блоки для направления ───────────────

class DayBlock(blocks.StructBlock):
    def __init__(self, **kwargs):
        super().__init__(
            [
                ("day_number", blocks.IntegerBlock(
                    required=False,
                    label="День",
                    help_text="Номер дня. Если не заполнять, день подставится по порядку.",
                )),
                ("title", CharBlock(label="Что происходит", max_length=160)),
                ("text", RichTextBlock(
                    label="Подробности",
                    features=["bold", "italic", "link"],
                )),
                ("image", ImageChooserBlock(label="Фото дня", required=False)),
            ],
            label="День программы",
            icon="date",
            template="blocks/day_block.html",
            **kwargs,
        )


class TimelineStepBlock(blocks.StructBlock):
    """Шаг линии времени: время, что происходит, подробности."""

    def __init__(self, **kwargs):
        super().__init__(
            [
                ("time", CharBlock(
                    label="Время",
                    max_length=20,
                    required=False,
                    help_text="Например: «6:00» или «19:30». Для второго дня "
                              "многодневной поездки допишите «+1»: «6:00 +1» — "
                              "такие шаги собираются в аккордеон «День 1 / День 2». "
                              "Можно оставить пустым.",
                )),
                ("title", CharBlock(
                    label="Что происходит",
                    max_length=160,
                    help_text="Например: «Сбор и отправление».",
                )),
                ("text", RichTextBlock(
                    label="Подробности",
                    features=["bold", "italic", "link"],
                )),
                ("image", ImageChooserBlock(
                    label="Фото шага",
                    required=False,
                    help_text="Необязательно. Обычно хватает фото в галерее.",
                )),
            ],
            label="Шаг линии времени",
            icon="time",
            template="blocks/timeline_step_block.html",
            **kwargs,
        )


class StayBlock(blocks.StructBlock):
    def __init__(self, **kwargs):
        super().__init__(
            [
                ("image", ImageChooserBlock(label="Фото", required=False)),
                ("name", CharBlock(
                    label="Название",
                    max_length=120,
                    help_text="Например: «Гоститель Сутки»",
                )),
                ("kind", CharBlock(
                    label="Тип и ночи",
                    max_length=80,
                    required=False,
                    help_text="Например: «гостиница · 1 ночь у моря»",
                )),
                ("text", TextBlock(label="Описание", required=False)),
            ],
            label="Место ночёвки",
            icon="site",
            template="blocks/stay_block.html",
            **kwargs,
        )


class FigureBlock(blocks.StructBlock):
    def __init__(self, **kwargs):
        super().__init__(
            [
                ("value", CharBlock(
                    label="Число",
                    max_length=20,
                    help_text="Например: 6, 1200, 40+",
                )),
                ("label", CharBlock(label="Подпись под числом", max_length=80)),
            ],
            label="Цифра с подписью",
            icon="pick",
            **kwargs,
        )


class MeetingPointBlock(blocks.StructBlock):
    def __init__(self, **kwargs):
        super().__init__(
            [
                ("city", CharBlock(label="Город", max_length=80)),
                ("address", CharBlock(label="Адрес или ориентир", max_length=200)),
                ("time", CharBlock(label="Время сбора", max_length=40, required=False)),
                ("note", TextBlock(label="Комментарий", required=False)),
            ],
            label="Точка сбора",
            icon="site",
            **kwargs,
        )


class MeetingCityBlock(blocks.StructBlock):
    """Сбор в одном городе — время может отличаться от города к городу."""

    def __init__(self, **kwargs):
        super().__init__(
            [
                ("city", CharBlock(label="Город", max_length=80)),
                ("time", CharBlock(
                    label="Время сбора",
                    max_length=40,
                    required=False,
                    help_text="Например: <6:30>. Если время ещё уточняете — оставьте пустым.",
                )),
                ("place", CharBlock(
                    label="Точка сбора",
                    max_length=160,
                    required=False,
                    help_text="Например: «пл. Урицкого, у памятника».",
                )),
            ],
            label="Город сбора",
            icon="site",
            **kwargs,
        )


class InfoNoteBlock(blocks.StructBlock):
    def __init__(self, **kwargs):
        super().__init__(
            [
                ("title", CharBlock(label="Что учесть", max_length=120)),
                ("text", TextBlock(label="Подробности", required=False)),
            ],
            label="Заметка",
            icon="help",
            **kwargs,
        )


def _pair(value_label, text_label, text_required=False):
    """Пара «заголовок + описание» для списков."""
    return blocks.StructBlock(
        [
            ("title", CharBlock(label=value_label, max_length=120)),
            ("text", TextBlock(label=text_label, required=text_required)),
        ]
    )


def _trio(time_label, title_label, text_label):
    return blocks.StructBlock(
        [
            ("time", CharBlock(label=time_label, max_length=20)),
            ("title", CharBlock(label=title_label, max_length=120)),
            ("text", TextBlock(label=text_label, required=False)),
        ]
    )


def _qa():
    return blocks.StructBlock(
        [
            ("question", CharBlock(label="Вопрос", max_length=200)),
            ("answer", TextBlock(label="Ответ", required=False)),
        ]
    )


def _stat():
    return blocks.StructBlock(
        [
            ("value", CharBlock(label="Значение", max_length=20)),
            ("label", CharBlock(label="Подпись", max_length=80)),
        ]
    )


# ─────────────── Блоки для страниц ───────────────

class ManifestBlock(blocks.StructBlock):
    def __init__(self, **kwargs):
        super().__init__(
            [
                ("numeral", CharBlock(
                    label="Крупное число или слово", max_length=8, required=False)),
                ("eyebrow", CharBlock(label="Мелкая подпись", max_length=80, required=False)),
                ("heading", CharBlock(label="Заголовок", max_length=200)),
                ("body", RichTextBlock(
                    label="Текст", features=["bold", "italic", "link"])),
                ("stats", ListBlock(_stat(), label="Цифры", required=False, max_num=4)),
            ],
            label="Блок о клубе",
            icon="doc-full",
            template="blocks/manifest.html",
            **kwargs,
        )


class NearestDeparturesBlock(blocks.StructBlock):
    def __init__(self, **kwargs):
        super().__init__(
            [
                ("heading", CharBlock(
                    label="Заголовок", default="Ближайшие выезды", max_length=120)),
                ("subheading", TextBlock(label="Подпись под заголовком", required=False)),
                ("limit", blocks.IntegerBlock(
                    label="Сколько показать", default=6, min_value=1, max_value=12)),
            ],
            label="Ближайшие выезды",
            icon="date",
            template="blocks/nearest_departures.html",
            **kwargs,
        )


class DestinationGridBlock(blocks.StructBlock):
    def __init__(self, **kwargs):
        super().__init__(
            [
                ("heading", CharBlock(label="Заголовок", default="Куда едем", max_length=120)),
                ("subheading", TextBlock(label="Подпись под заголовком", required=False)),
                ("featured_count", blocks.IntegerBlock(
                    label="Сколько крупных карточек", default=1, min_value=0, max_value=4)),
            ],
            label="Направления плитками",
            icon="image",
            template="blocks/destination_grid.html",
            **kwargs,
        )


class FeaturesBlock(blocks.StructBlock):
    def __init__(self, **kwargs):
        super().__init__(
            [
                ("heading", CharBlock(
                    label="Заголовок", default="Почему с нами", max_length=120)),
                ("items", ListBlock(
                    _pair("Заголовок", "Описание"),
                    label="Пункты",
                    max_num=6,
                )),
            ],
            label="Почему с нами",
            icon="tick",
            template="blocks/features.html",
            **kwargs,
        )


class StepsBlock(blocks.StructBlock):
    def __init__(self, **kwargs):
        super().__init__(
            [
                ("heading", CharBlock(
                    label="Заголовок", default="Как проходит поездка", max_length=120)),
                ("items", ListBlock(
                    _trio("Время", "Что происходит", "Подробности"),
                    label="Шаги",
                    max_num=8,
                )),
            ],
            label="Как проходит поездка",
            icon="tasks",
            template="blocks/steps.html",
            **kwargs,
        )


class PhotoWallBlock(blocks.StructBlock):
    def __init__(self, **kwargs):
        super().__init__(
            [
                ("heading", CharBlock(
                    label="Заголовок", default="Мы там были", max_length=120)),
                ("subheading", TextBlock(label="Подпись под заголовком", required=False)),
                ("images", blocks.StreamBlock(
                    [("image", ImageChooserBlock(label="Фото"))],
                    label="Фотографии",
                )),
            ],
            label="Фото-стена",
            icon="image",
            template="blocks/photo_wall.html",
            **kwargs,
        )


class QuoteBlock(blocks.StructBlock):
    def __init__(self, **kwargs):
        super().__init__(
            [
                ("text", TextBlock(label="Цитата или обещание")),
                ("author", CharBlock(label="Подпись", max_length=120, required=False)),
            ],
            label="Цитата",
            icon="openquote",
            template="blocks/quote.html",
            **kwargs,
        )


class FaqBlock(blocks.StructBlock):
    def __init__(self, **kwargs):
        super().__init__(
            [
                ("heading", CharBlock(
                    label="Заголовок", default="Частые вопросы", max_length=120)),
                ("items", ListBlock(_qa(), label="Вопросы", max_num=10)),
            ],
            label="Частые вопросы",
            icon="help",
            template="blocks/faq.html",
            **kwargs,
        )


class CtaBlock(blocks.StructBlock):
    def __init__(self, **kwargs):
        super().__init__(
            [
                ("heading", CharBlock(
                    label="Заголовок", max_length=200, default="Выходные ещё есть")),
                ("text", TextBlock(label="Текст под заголовком", required=False)),
                ("button_text", CharBlock(
                    label="Текст кнопки", max_length=40, default="Записаться")),
                ("button_url", CharBlock(
                    label="Куда ведёт кнопка",
                    max_length=200,
                    required=False,
                    help_text="Оставьте пустым — кнопка поведёт на страницу контактов.",
                )),
            ],
            label="Призыв записаться",
            icon="link",
            template="blocks/cta.html",
            **kwargs,
        )


# ─────────────── Списки-«галочки» ───────────────

def qa_stream(label, help_text):
    """Вопрос-ответ для страницы направления."""
    return [
        (
            "faq",
            blocks.StructBlock(
                [
                    ("question", CharBlock(label="Вопрос", max_length=200)),
                    ("answer", TextBlock(label="Ответ", required=False)),
                ]
            ),
        )
    ], label, help_text


def bullet_stream(label, help_text):
    """Определение StreamField для списка коротких пунктов.

    Возвращает список блоков, а не сам блок: полем модели может быть
    только StreamField, поэтому оборачиваем в ().
    """
    return [("items", ListBlock(CharBlock(label="Пункт")))], label, help_text


ADMIN_HINT = StaticBlock(
    admin_text=(
        "<p><strong>Подсказка:</strong> заполняйте поля сверху вниз — "
        "так страница дойдёт до «100% готово», и её можно будет опубликовать. "
        "Правая колонка показывает предпросмотр и список того, что осталось.</p>"
    ),
)