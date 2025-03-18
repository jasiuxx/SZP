from django.contrib import admin
from .models import Employee, Skill, Personality_trait, EmployeeSkill, Experience
from account.models import CustomUser
from django.utils.safestring import mark_safe

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['user','user_first_name','user_last_name', 'display_skills', 'display_personality_traits','belbin_test_result']

    def display_skills(self, obj):
        skills_with_levels = []
        for skill in obj.skills.all():
            try:
                employee_skill = EmployeeSkill.objects.get(employee=obj, skill=skill)
                level_display = {
                    '1': 'Junior',
                    '2': 'Mid',
                    '3': 'Senior'
                }.get(employee_skill.proficiency_level, '')
                skills_with_levels.append(f"{skill.name} ({level_display})")
            except EmployeeSkill.DoesNotExist:
                skills_with_levels.append(f"{skill.name}")
        return ", ".join(skills_with_levels)
    display_skills.short_description = 'Skills'

    def display_personality_traits(self, obj):
        return ", ".join(trait.name for trait in obj.personality_traits.all())
    display_personality_traits.short_description = 'Personality Traits'

    def user_first_name(self, obj):
        return obj.user.first_name  # Pobiera imię z powiązanego użytkownika
    user_first_name.short_description = 'First Name'

    def user_last_name(self, obj):
        return obj.user.last_name  # Pobiera nazwisko z powiązanego użytkownika
    user_last_name.short_description = 'Last Name'

class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'logo_display')
    search_fields = ('name',)

    def logo_display(self, obj):
        if obj.logo:
            return mark_safe(f'<img src="{obj.logo.url}" width="30" height="30" />')
        return "Brak logo"
    logo_display.short_description = 'Logo'

admin.site.register(Skill, SkillAdmin)
admin.site.register(Personality_trait)

@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('title', 'employee', 'date_started', 'date_ended')
    list_filter = ('employee',)
    search_fields = ('title', 'description', 'employee__user__first_name', 'employee__user__last_name')
    date_hierarchy = 'date_started'
