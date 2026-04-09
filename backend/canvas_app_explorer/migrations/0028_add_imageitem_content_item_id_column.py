from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('canvas_app_explorer', '0027_remove_imageitem_content_item_fk'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE canvas_app_explorer_image_item "
                "ADD COLUMN content_item_id bigint NULL, "
                "ADD CONSTRAINT fk_image_item_content_item_id "
                "FOREIGN KEY (content_item_id) "
                "REFERENCES canvas_app_explorer_content_item (id) "
                "ON DELETE CASCADE;"
            ),
            reverse_sql=(
                "ALTER TABLE canvas_app_explorer_image_item "
                "DROP FOREIGN KEY fk_image_item_content_item_id, "
                "DROP COLUMN content_item_id;"
            ),
        ),
    ]
