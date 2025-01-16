# Generated by Django 5.1.3 on 2024-12-18 11:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employers', '0003_verificationcode_remove_employer_verification_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='verificationcode',
            name='employer',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='verification_code', to='employers.employer'),
        ),
    ]
