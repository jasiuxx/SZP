# Generated by Django 5.1.3 on 2024-12-26 11:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0007_employee_availability'),
        ('projects', '0004_remove_project_skills_required_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectTeam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='employees.employee')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.project')),
            ],
        ),
    ]
