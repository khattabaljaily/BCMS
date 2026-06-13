from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0003_merge_20260612_1848'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='expense',
            name='client',
        ),
    ]
