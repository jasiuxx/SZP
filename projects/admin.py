from django.contrib import admin
from .models import Project, ProjectSkillRequirement
from employees.models import Skill  # Jeśli chcesz mieć dostęp do Skill w adminie

# Zarejestruj model Project
class ProjectSkillRequirementInline(admin.TabularInline):
    model = ProjectSkillRequirement
    extra = 1  # Liczba formularzy, które mają się domyślnie pojawić w formularzu

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'code', 'owner', 'description')  # Kolumny do wyświetlenia w liście projektów
    search_fields = ('title', 'code', 'description')  # Wyszukiwanie po tych polach
    inlines = [ProjectSkillRequirementInline]  # Dodajemy inline dla ProjectSkillRequirement

# Zarejestruj model Project i powiązany formularz admina
admin.site.register(Project, ProjectAdmin)

# Zarejestruj model ProjectSkillRequirement osobno
class ProjectSkillRequirementAdmin(admin.ModelAdmin):
    list_display = ('project', 'skill', 'required_count')  # Kolumny do wyświetlenia w liście
    search_fields = ('project__title', 'skill__name')  # Wyszukiwanie po nazwie projektu i umiejętności

admin.site.register(ProjectSkillRequirement, ProjectSkillRequirementAdmin)




