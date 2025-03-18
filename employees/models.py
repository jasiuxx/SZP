from django.db import models
from account.models import CustomUser
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
import json
from django.utils import timezone




class Personality_trait(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Skill(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='skills/logos/', blank=True, null=True)

    def __str__(self):
        return self.name




class Employee(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    skills = models.ManyToManyField('Skill', related_name="employees", blank=True)
    personality_traits = models.ManyToManyField(Personality_trait, related_name="employees", blank=True)
    belbin_test_result = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}" if self.user.first_name and self.user.last_name else self.user.username

class BelbinScore(models.Model):
    """
    Model do przechowywania punktów Belbina dla każdej roli osobno.
    """
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='belbin_scores'
    )
    role_name = models.CharField(max_length=10)  # np. 'SH', 'CO', 'PL' itp.
    score = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.employee} - {self.role_name}: {self.score}"

class EmployeeSkill(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="employee_skills")
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    proficiency_level = models.CharField(
        max_length=20,
        choices=[
            ('1', 'Junior'),
            ('2', 'Mid'),
            ('3', 'Senior')
        ],
        default='2'
    )

    class Meta:
        unique_together = ('employee', 'skill')

class Experience(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='experiences')
    title = models.CharField(max_length=255, verbose_name="Tytuł")
    description = models.TextField(verbose_name="Opis")
    date_started = models.DateField(verbose_name="Data rozpoczęcia")
    date_ended = models.DateField(verbose_name="Data zakończenia", null=True, blank=True)
    image = models.ImageField(upload_to='experiences/', null=True, blank=True, verbose_name="Zdjęcie")
    project_file = models.FileField(upload_to='experience_files/', null=True, blank=True, verbose_name="Plik projektu")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Doświadczenie"
        verbose_name_plural = "Doświadczenia"
        ordering = ['-date_started']

    def __str__(self):
        return f"{self.title} - {self.employee}"

