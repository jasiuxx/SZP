# Generated by Django 5.1.3 on 2024-12-26 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0006_alter_employee_belbin_test_result'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='availability',
            field=models.BooleanField(default=True),
        ),
    ]
