# Generated by Django 3.2.13 on 2022-06-23 15:26

# Resource(s)
# https://docs.djangoproject.com/en/4.0/topics/migrations/#data-migrations
# https://lti.colcampus.com/xml_builder

from django.db import migrations

def create_initial_canvas_placements(apps, schema_editor) -> None:
    CanvasPlacement = apps.get_model('canvas_app_explorer', 'CanvasPlacement')

    placement_names = [
        'Account Navigation',
        'Assignment Menu',
        'Assignment Configuration',
        'Collaboration',
        'Course Home Sub Navigation',
        'Course Navigation',
        'Course Settings Sub Navigation',
        'Discussion Menu',
        'Editor Button',
        'File Menu',
        'Global Navigation',
        'Homework Submission',
        'Migration Selection',
        'Module Menu',
        'Quiz Menu',
        'User Navigation',
        'Assignment Selection',
        'Link Selection',
        'Wiki Page Menu',
        'Tool Configuration',
        'Post Grades'
    ]

    CanvasPlacement.objects.bulk_create([
        CanvasPlacement(name=placement_name) for placement_name in placement_names
    ])

class Migration(migrations.Migration):

    dependencies = [
        ('canvas_app_explorer', '0008_ltitool_canvas_id'),
    ]

    operations = [
        migrations.RunPython(create_initial_canvas_placements),
    ]
