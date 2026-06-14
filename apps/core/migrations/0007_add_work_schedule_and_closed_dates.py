from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_alter_centerbackup_file_size_alter_notification_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='settings',
            name='work_schedule',
            field=models.TextField(blank=True, default='', verbose_name='جدول الدوام التفصيلي'),
        ),
        migrations.AddField(
            model_name='settings',
            name='closed_dates',
            field=models.TextField(blank=True, default='', verbose_name='تواريخ الإغلاق'),
        ),
    ]
