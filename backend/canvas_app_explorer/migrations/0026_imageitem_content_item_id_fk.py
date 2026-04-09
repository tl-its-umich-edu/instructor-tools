from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('canvas_app_explorer', '0025_alter_imageitem_content_item'),
    ]

    operations = [
        migrations.AddField(
            model_name='imageitem',
            name='content_item_fk',
            field=models.ForeignKey(
                blank=True,
                null=True,
                db_column='content_item_id',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='image_items_by_content_item_id',
                to='canvas_app_explorer.contentitem',
            ),
        ),
    ]
