from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0002_alter_appointment_total_price'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='appointment',
            options={
                'ordering': ['-id'],
                'verbose_name': 'موعد',
                'verbose_name_plural': 'المواعيد',
            },
        ),
    ]
