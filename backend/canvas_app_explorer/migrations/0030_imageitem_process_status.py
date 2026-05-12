from django.db import migrations, models


def backfill_image_process_state(apps, schema_editor):
    ImageItem = apps.get_model('canvas_app_explorer', 'ImageItem')

    for image in ImageItem.objects.all().only('id', 'image_alt_text', 'image_process_state').iterator():
        alt_text = image.image_alt_text or ''
        image.image_process_state = 'success' if alt_text.strip() else 'failed'
        image.save(update_fields=['image_process_state'])


class Migration(migrations.Migration):

    dependencies = [
        ('canvas_app_explorer', '0029_coursescanerrorlog_error_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='imageitem',
            name='image_process_state',
            field=models.CharField(
                choices=[('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed')],
                default='pending',
                max_length=20,
            ),
        ),
        migrations.RunPython(backfill_image_process_state, migrations.RunPython.noop),
    ]
