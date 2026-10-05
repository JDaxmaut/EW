from django import forms

from .models import ContactSubmission

INPUT = (
    "w-full bg-white border border-mint-line rounded-xl px-4 py-3 text-[15px] "
    "font-light text-ink outline-none placeholder:text-ink-60/70 "
    "focus:border-turquoise focus:ring-4 focus:ring-turquoise/20 "
    "transition-colors duration-200 font-sans"
)

TEXTAREA = INPUT + " resize-none"

SELECT = (
    "w-full bg-white border border-mint-line rounded-xl px-4 py-3 text-[15px] "
    "font-light text-ink outline-none focus:border-turquoise "
    "focus:ring-4 focus:ring-turquoise/20 transition-colors duration-200 font-sans"
)


class ContactForm(forms.ModelForm):
    """Заявка с сайта. Подписи человеческие — их видит менеджер и клиент."""

    class Meta:
        model = ContactSubmission
        fields = ["name", "phone", "email", "destination", "departure_date", "message"]
        labels = {
            "name": "Как к вам обращаться",
            "phone": "Телефон или Telegram",
            "email": "Почта",
            "destination": "Направление",
            "departure_date": "Дата выезда",
            "message": "Комментарий",
        }
        help_texts = {
            "name": "Например: Анна",
            "phone": "Номер телефона или @ник в Telegram",
            "destination": "Если вы уже выбрали направление",
            "departure_date": "Если хотите конкретную дату",
            "message": "Вопросы, пожелания, состав группы",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT, "placeholder": "Анна"}),
            "phone": forms.TextInput(
                attrs={"class": INPUT, "placeholder": "+7 999 000-00-00 или @anna"}
            ),
            "email": forms.EmailInput(
                attrs={"class": INPUT, "placeholder": "anna@example.com"}
            ),
            "destination": forms.TextInput(
                attrs={"class": INPUT, "placeholder": "Ханская"}
            ),
            "departure_date": forms.TextInput(
                attrs={"class": INPUT, "placeholder": "например, 12 июня"}
            ),
            "message": forms.Textarea(
                attrs={"class": TEXTAREA, "rows": 4, "placeholder": "Напишите пару слов"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.required = name in {"name", "phone"}
            css = "border-coral-deep focus:border-coral-deep focus:ring-coral/20"
            if name in {"name", "phone"}:
                field.widget.attrs["class"] += " " + css