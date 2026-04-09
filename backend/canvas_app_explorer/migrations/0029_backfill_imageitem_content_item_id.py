from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('canvas_app_explorer', '0028_add_imageitem_content_item_id_column'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "UPDATE canvas_app_explorer_image_item AS ii "
                "INNER JOIN canvas_app_explorer_content_item AS ci "
                "ON ii.content_id = ci.content_id "
                "SET ii.content_item_id = ci.id "
                "WHERE ii.content_item_id IS NULL"
            ),
            reverse_sql=(
                "UPDATE canvas_app_explorer_image_item "
                "SET content_item_id = NULL"
            ),
        ),
    ]
