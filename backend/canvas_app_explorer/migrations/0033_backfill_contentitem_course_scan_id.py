from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('canvas_app_explorer', '0032_contentitem_course_scan_alter_contentitem_course'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "UPDATE canvas_app_explorer_content_item AS ci "
                "INNER JOIN canvas_app_explorer_course_scan AS cs "
                "ON ci.course_id = cs.course_id "
                "SET ci.course_scan_id = cs.id "
                "WHERE ci.course_scan_id IS NULL"
            ),
            reverse_sql=(
                "UPDATE canvas_app_explorer_content_item "
                "SET course_scan_id = NULL"
            ),
        ),
    ]
