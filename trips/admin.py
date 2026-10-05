from django.contrib import admin

from .models import ContactSubmission


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ["name", "phone", "destination", "created_at", "handled"]
    list_filter = ["handled", "created_at"]
    search_fields = ["name", "phone", "email", "destination", "message"]
    list_editable = ["handled"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"
    fieldsets = (
        (None, {"fields": ["name", "phone", "email"]}),
        ("Заявка", {"fields": ["destination", "departure_date", "message"]}),
        ("Обработка", {"fields": ["handled", "created_at"]}),
    )