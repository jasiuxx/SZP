from django.db import models
from account.models import CustomUser




class Personality_trait(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Skill(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name




class Employee(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    skills = models.ManyToManyField('Skill', related_name="employees", blank=True)
    personality_traits = models.ManyToManyField(Personality_trait, related_name="employees", blank=True)
    belbin_test_result = models.JSONField(blank=True, null=True)



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

