# Generated by Django 4.2.20 on 2025-03-31 14:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('canvas_app_explorer', '0013_drop_mysql_cache'),
    ]

    operations = [
        migrations.AddField(
            model_name='ltitool',
            name='launch_url',
            field=models.CharField(blank=True, max_length=2048, null=True),
        ),
    ]
