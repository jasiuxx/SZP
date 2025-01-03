from django.db import models
from employees.models import Skill
from employers.models import Employer

from employees.models import Employee  # Dodaj import do modelu Employee

class Project(models.Model):
    title = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    owner = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='projects')
    employees = models.ManyToManyField(Employee, related_name='projects', blank=True)  # Dodanie tej linii

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


class EmployeeProjectAssignment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.employee.user.first_name} {self.employee.user.last_name} - {self.skill.name}"
