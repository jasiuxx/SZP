from django.contrib import admin
from .models import Project

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'code', 'owner', 'description')  # Pola wyświetlane na liście projektów
    search_fields = ('title', 'code', 'owner__user__username')  # Pola umożliwiające wyszukiwanie
    list_filter = ('owner',)  # Filtrowanie po właścicielu projektu
    filter_horizontal = ('skills_required',)  # Umożliwia łatwe zarządzanie relacją wiele-do-wielu
