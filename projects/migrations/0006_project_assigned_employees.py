# Generated by Django 5.1.3 on 2024-12-26 11:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0007_employee_availability'),
        ('projects', '0005_projectteam'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='assigned_employees',
            field=models.ManyToManyField(blank=True, related_name='projects', to='employees.employee'),
        ),
    ]
