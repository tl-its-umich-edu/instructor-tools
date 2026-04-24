from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('canvas_app_explorer', '0025_multiscan_schema_transition'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='coursescan',
            name='q_task_id',
        ),
    ]
