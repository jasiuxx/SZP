from django.contrib import admin
from .models import Employer,VerificationCode
from django.urls import path
from django.shortcuts import redirect
from django.contrib import admin, messages
from .models import VerificationCode

@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'is_used', 'created_at', 'employer')
    readonly_fields = ('created_at',)
    change_list_template = "employers/verification_code_changelist.html"  # Własny szablon

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('generate-codes/', self.generate_codes_view, name='generate_codes'),
        ]
        return custom_urls + urls

    def generate_codes_view(self, request):
        """Widok do generowania nowych kodów."""
        VerificationCode.objects.create()
        self.message_user(request, "Wygenerowano nowy kod.")
        return redirect("..")  # Powrót do listy kodów




@admin.register(Employer)
class EmployerAdmin(admin.ModelAdmin):
    list_display = ("user",'user_first_name','user_last_name', "is_verified","verification_code")
    search_fields = ("user__username",)

    def user_first_name(self, obj):
        return obj.user.first_name  # Pobiera imię z powiązanego użytkownika
    user_first_name.short_description = 'First Name'

    def user_last_name(self, obj):
        return obj.user.last_name  # Pobiera nazwisko z powiązanego użytkownika
    user_last_name.short_description = 'Last Name'