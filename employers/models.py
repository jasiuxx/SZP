from django.db import models
from account.models import CustomUser
from django.utils.crypto import get_random_string
import uuid


class VerificationCode(models.Model):
    code = models.CharField(max_length=8, unique=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    employer = models.OneToOneField(
        'Employer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verification_code'
    )  # Relacja one-to-one z pracodawcą

    def save(self, *args, **kwargs):
        if not self.code:
            from django.utils.crypto import get_random_string
            self.code = get_random_string(length=8)
        super().save(*args, **kwargs)

    def __str__(self):
        status = "Użyty" if self.is_used else "Wolny"
        return f"Kod: {self.code} ({status})"

class Employer(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='employer_profile',
        null=True,
        blank=True
    )
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"Pracodawca: {self.user.username} ({'Zweryfikowany' if self.is_verified else 'Niezweryfikowany'})"
