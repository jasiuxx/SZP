from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Employee, Skill, Personality_trait

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'is_employee', 'is_employer', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('is_employee', 'is_employer')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Employee)
admin.site.register(Skill)
admin.site.register(Personality_trait)
