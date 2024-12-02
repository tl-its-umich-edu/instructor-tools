
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('canvas_app_explorer', '0012_alter_ltitool_internal_notes'),
    ]

    operations = [
        migrations.RunSQL(
            "DROP TABLE IF EXISTS `canvas_app_explorer_cache`;",
            reverse_sql="""
            CREATE TABLE `canvas_app_explorer_cache` (
                cache_key varchar(255) CHARACTER SET utf8 COLLATE utf8_bin
                                       NOT NULL PRIMARY KEY,
                value longblob NOT NULL,
                value_type char(1) CHARACTER SET latin1 COLLATE latin1_bin
                                   NOT NULL DEFAULT 'p',
                expires BIGINT UNSIGNED NOT NULL
            );
            """
        ),
    ]