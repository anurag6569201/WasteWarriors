# Generated by Django 5.0 on 2024-01-23 10:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0005_comment'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='blog',
            new_name='post',
        ),
    ]
