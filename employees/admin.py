from django.contrib import admin
from .models import Employee, Skill, Personality_trait
from account.models import CustomUser
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['user','user_first_name','user_last_name', 'display_skills', 'display_personality_traits','belbin_test_result']

    def display_skills(self, obj):
        return ", ".join(skill.name for skill in obj.skills.all())
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

admin.site.register(Skill)
admin.site.register(Personality_trait)
