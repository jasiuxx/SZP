from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django.utils.crypto import get_random_string  # Do generowania losowych kodów
from django.contrib import admin,messages
from employers.models import Employer,VerificationCode





class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'is_employee', 'is_employer', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('is_employee', 'is_employer')}),
    )




admin.site.register(CustomUser, CustomUserAdmin)
