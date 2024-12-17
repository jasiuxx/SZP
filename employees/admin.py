from django.contrib import admin
from .models import Employee, Skill, Personality_trait

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['user', 'display_skills', 'display_personality_traits']

    def display_skills(self, obj):
        return ", ".join(skill.name for skill in obj.skills.all())
    display_skills.short_description = 'Skills'

    def display_personality_traits(self, obj):
        return ", ".join(trait.name for trait in obj.personality_traits.all())
    display_personality_traits.short_description = 'Personality Traits'

admin.site.register(Skill)
admin.site.register(Personality_trait)
