from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0001_initial'),
        ('clients', '__first__'),
    ]

    operations = [
        migrations.AddField(
            model_name='expense',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='clients.client'),
        ),
    ]
