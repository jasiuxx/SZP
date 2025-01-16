# Generated by Django 5.1.3 on 2025-01-01 14:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0008_remove_employee_availability'),
        ('projects', '0007_rename_assigned_employees_project_employees_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmployeeProjectAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='employees.employee')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.project')),
                ('skill', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='employees.skill')),
            ],
        ),
    ]
