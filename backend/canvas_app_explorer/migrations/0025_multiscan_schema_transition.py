from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('canvas_app_explorer', '0024_alter_toolcategory_options'),
    ]

    operations = [
        # Add new nullable FK columns first so we can backfill before switching constraints.
        migrations.AddField(
            model_name='contentitem',
            name='course_scan',
            field=models.ForeignKey(
                blank=True,
                null=True,
                db_column='course_scan_id',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='content_items_new',
                to='canvas_app_explorer.coursescan',
            ),
        ),
        migrations.AddField(
            model_name='imageitem',
            name='content_item_new',
            field=models.ForeignKey(
                blank=True,
                null=True,
                db_column='content_item_id',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='images_new',
                to='canvas_app_explorer.contentitem',
            ),
        ),
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
        # Remove old FKs that depend on unique indexes before altering uniqueness.
        migrations.RemoveField(
            model_name='imageitem',
            name='course',
        ),
        migrations.RemoveField(
            model_name='imageitem',
            name='content_item',
        ),
        migrations.RemoveField(
            model_name='contentitem',
            name='course',
        ),
        migrations.RenameField(
            model_name='imageitem',
            old_name='content_item_new',
            new_name='content_item',
        ),
        migrations.AlterField(
            model_name='coursescan',
            name='course_id',
            field=models.BigIntegerField(),
        ),
        migrations.AlterField(
            model_name='contentitem',
            name='content_id',
            field=models.BigIntegerField(),
        ),
        migrations.AlterField(
            model_name='contentitem',
            name='course_scan',
            field=models.ForeignKey(
                db_column='course_scan_id',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='content_items',
                to='canvas_app_explorer.coursescan',
            ),
        ),
        migrations.AlterField(
            model_name='imageitem',
            name='content_item',
            field=models.ForeignKey(
                db_column='content_item_id',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='images',
                to='canvas_app_explorer.contentitem',
            ),
        ),
        migrations.AddConstraint(
            model_name='contentitem',
            constraint=models.UniqueConstraint(
                fields=('course_scan', 'content_id'),
                name='uniq_contentitem_scan_content_id',
            ),
        ),
    ]
