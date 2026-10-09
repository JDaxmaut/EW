# -*- coding: utf-8 -*-
"""Вкладки редактора — по-русски и с подсказками.

Подключены в trips/models.py:
    Destination.edit_handler = TabbedInterface(DESTINATION_TABS)
    LegalPage.edit_handler = TabbedInterface(LEGAL_TABS)

Названия полей соответствуют моделям trips. Если поле переименуешь —
удали строку с ним, лишнее поле Wagtail покажет отдельной вкладкой само.
"""

from wagtail.admin.panels import (
    FieldPanel,
    FieldRowPanel,
    HelpPanel,
    InlinePanel,
    MultiFieldPanel,
    ObjectList,
)

DESTINATION_TABS = [
    ObjectList(
        [
            HelpPanel(
                "Главное: как тур называется и в каком формате проходит. "
                "Формат меняет заголовок программы на странице."
            ),
            FieldPanel(
                "title",
                heading="Название тура",
                help_text="Коротко и по-русски: «Ханская», «Майкоп».",
            ),
            FieldPanel(
                "eyebrow",
                heading="Надпись над заголовком",
                help_text="Например: «Краснодарский край · выезды: пт, сб, вс».",
            ),
            FieldPanel(
                "subtitle",
                heading="Подзаголовок",
                help_text="Одна строка под названием: «Дикий пляж в сосновом бору».",
            ),
            FieldRowPanel(
                [
                    FieldPanel(
                        "kind",
                        heading="Тип места",
                        help_text="Пляж, дикий пляж, горы или город. По нему фильтр в каталоге.",
                    ),
                    FieldPanel(
                        "format",
                        heading="Формат поездки",
                        help_text="Однодневный, с ночёвкой или экскурсия.",
                    ),
                ]
            ),
        ],
        heading="Основное",
    ),
    ObjectList(
        [
            HelpPanel("Эти пять полей клиент видит на карточке в каталоге."),
            FieldPanel(
                "cover",
                heading="Обложка",
                help_text="Главное фото. Без него карточка в каталоге будет пустой.",
            ),
            FieldRowPanel(
                [
                    FieldPanel(
                        "price_from",
                        heading="Цена «от», ₽",
                        help_text="Только число, можно с пробелом: 1 900. Без знака ₽.",
                    ),
                    FieldPanel(
                        "duration",
                        heading="Длительность",
                        help_text="Например: «1 день» или «2 дня / 1 ночь».",
                    ),
                ]
            ),
            FieldPanel(
                "distance",
                heading="Расстояние",
                help_text="Например: «120 км». Число отсюда попадёт в фильтр каталога.",
            ),
            FieldRowPanel(
                [
                    FieldPanel(
                        "travel_time",
                        heading="Время в пути",
                        help_text="Например: «2,5 ч».",
                    ),
                    FieldPanel(
                        "ew_type",
                        heading="Тип в фильтре каталога",
                        help_text="Отдельно от «Типа места»: у микропляжа и дикого пляжа тип места один, а чипы в фильтре разные.",
                    ),
                ]
            ),
            FieldPanel(
                "parking",
                heading="Парковка",
                help_text="Например: «платная, 300 ₽/день».",
            ),
        ],
        heading="Карточка в каталоге",
    ),
    ObjectList(
        [
            HelpPanel(
                "Коротко — это попадёт в сниппет и на карточку. "
                "Подробно — откроется при прокрутке страницы."
            ),
            FieldPanel(
                "summary",
                heading="Коротко о туре",
                help_text="Одно-два предложения: что это и зачем сюда ехать.",
            ),
            FieldPanel("description", heading="Подробное описание"),
            FieldPanel(
                "highlights",
                heading="Особенности",
                help_text="Короткие пункты с точками: «Бухта на 30 шагов», «Рассвет без людей».",
            ),
        ],
        heading="Описание",
    ),
    ObjectList(
        [
            HelpPanel(
                "Программа — одним текстом: набирайте как удобно, "
                "можно списками и с выделением. Для многодневки начинайте "
                "каждый день с абзаца «День 1», «День 2» и так далее."
            ),
            FieldPanel(
                "program_text",
                heading="Программа выезда (текст)",
                help_text=(
                    "Например: «6:40 Сбор в Краснодаре...», «8:30 Приезд...». "
                    "Заголовки, списки и выделение — из панели редактора."
                ),
            ),
        ],
        heading="Программа",
    ),
    ObjectList(
        [
            HelpPanel(
                "Нужно только турам с форматом «С ночёвкой». "
                "Для однодневных и экскурсий обе вкладки можно не трогать."
            ),
            FieldPanel(
                "stay",
                heading="Где остановиться",
                help_text="Гостиница, апартаменты, коттедж: название, тип и описание.",
            ),
        ],
        heading="Поездки с ночёвкой",
    ),
    ObjectList(
        [
            HelpPanel("Честные списки удерживают от лишних вопросов на связи."),
            FieldPanel(
                "included",
                heading="Что входит",
                help_text="Пункты с галочкой на странице тура.",
            ),
            FieldPanel(
                "excluded",
                heading="Что не входит",
                help_text="Честный список: алкоголь, аренда, личные покупки.",
            ),
            FieldPanel(
                "packing",
                heading="Что взять с собой",
                help_text="6–10 пунктов: купальник, полотенце, деньги на парковку.",
            ),
            FieldPanel(
                "faq",
                heading="Частые вопросы",
                help_text="3–4 вопроса-ответа, отвечайте как в чате.",
            ),
        ],
        heading="Что входит и что взять",
    ),
    ObjectList(
        [
            HelpPanel(
                "Загружайте сразу в слоты: обложка 4:3, галерея — любые. "
                "Сайт сам сожмёт в WebP."
            ),
            FieldPanel(
                "gallery_hero",
                heading="Фото для первого экрана",
                help_text="3–6 широких фотографий. Первая идёт на первый экран.",
            ),
            FieldPanel("gallery", heading="Галерея тура"),
        ],
        heading="Фотографии",
    ),
    ObjectList(
        [
            HelpPanel(
                "Каждая строка — один выезд на сайте. "
                "«Свободно мест = 0» включает лист ожидания."
            ),
            FieldPanel(
                "ew_days",
                heading="Дни выездов",
                help_text="Через запятую: «пт,сб,вс». Попадает в подзаголовок на странице тура.",
            ),
            InlinePanel(
                "departures",
                heading="Расписание выездов",
                label="Выезд",
                help_text="Даты, цена, всего мест, свободно мест, статус.",
            ),
        ],
        heading="Выезды",
    ),
    ObjectList(
        [
            HelpPanel("Служебное. Адрес страницы меняем руками, чтобы не сломать ссылки."),
            FieldPanel(
                "slug",
                heading="Адрес страницы",
                help_text="Латиницей, через дефис: hanskaya.",
            ),
            FieldPanel(
                "search_description",
                heading="Описание для поисковиков",
                help_text="До 160 символов: суть и цена.",
            ),
            FieldPanel("tags", heading="Метки"),
            FieldPanel("owner", heading="Ответственный редактор"),
            MultiFieldPanel(
                [
                    FieldPanel("show_in_menus", heading="Показывать в меню"),
                    FieldPanel("seo_title", heading="Заголовок для поисковиков"),
                ],
                heading="Публикация",
            ),
        ],
        heading="Настройки и SEO",
    ),
]


LEGAL_TABS = [
    ObjectList(
        [
            HelpPanel("Шапка документа: заголовок, дата редакции и описание для списка."),
            FieldPanel(
                "title",
                heading="Заголовок на сайте",
                help_text="Дословно из шапки docx — так документ найдут поиском.",
            ),
            FieldPanel(
                "intro",
                heading="Описание для карточки в списке",
                help_text="Одна строка: о чём документ и для кого.",
            ),
            FieldPanel(
                "updated",
                heading="Дата редакции",
                help_text="Например: «октябрь 2026». Видна в шапке страницы.",
            ),
        ],
        heading="Шапка",
    ),
    ObjectList(
        [
            HelpPanel(
                "Текст вставляется дословно из docx. Ничего не теряется "
                "при сохранении — разметка собирается автоматически."
            ),
            FieldPanel(
                "body",
                heading="Текст документа",
                help_text="Правки можно вносить здесь или загрузить новую редакцию docx.",
            ),
        ],
        heading="Текст",
    ),
    ObjectList(
        [
            HelpPanel("На этот адрес ссылается куки-баннер и футер."),
            FieldPanel(
                "slug",
                heading="Адрес страницы",
                help_text="Латиницей: offer, policy, consent-pd…",
            ),
            FieldPanel(
                "search_description",
                heading="Описание для поисковиков",
                help_text="До 160 символов: название и суть.",
            ),
            MultiFieldPanel(
                [
                    FieldPanel("show_in_menus", heading="Показывать в меню"),
                    FieldPanel("seo_title", heading="Заголовок для поисковиков"),
                ],
                heading="Публикация",
            ),
            FieldPanel("owner", heading="Ответственный редактор"),
        ],
        heading="Адрес и SEO",
    ),
]
