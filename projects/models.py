from django.db import models
from employees.models import Skill
from employers.models import Employer

class Project(models.Model):
    title = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    skills_required = models.ManyToManyField(Skill, related_name='projects')
    owner = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='projects')  # Powiązanie z pracodawcą

    def __str__(self):
        return self.title
