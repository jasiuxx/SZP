from django.db import models
from employees.models import Skill
from employers.models import Employer

class Project(models.Model):
    title = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    owner = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='projects')

    def __str__(self):
        return self.title


class ProjectSkillRequirement(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='skill_requirements')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    required_count = models.PositiveIntegerField(default=0)  # Liczba wymaganych specjalistów

    class Meta:
        unique_together = ('project', 'skill')  # Każda kombinacja projektu i umiejętności musi być unikalna

    def __str__(self):
        return f"{self.project.title} - {self.skill.name}: {self.required_count} osób"
