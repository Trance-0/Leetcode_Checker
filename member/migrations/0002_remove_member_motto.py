# Generated by Django 4.2.10 on 2024-10-29 00:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("member", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(model_name="member", name="motto",),
    ]
