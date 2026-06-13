from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='settings',
            name='work_days',
            field=models.CharField(
                default='0,1,2,3,4',
                max_length=20,
                verbose_name='أيام العمل',
            ),
        ),
    ]
