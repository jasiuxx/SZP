from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    is_employee = models.BooleanField(default=False)
    is_employer = models.BooleanField(default=False)

class Personality_trait(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Skill(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Employee(models.Model):
    user = models.OneToOneField('employees.CustomUser', on_delete=models.CASCADE, related_name='profile')
    skills = models.ManyToManyField('Skill', related_name="employees", blank=True)
    personality_traits = models.ManyToManyField(Personality_trait, related_name="employees", blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
