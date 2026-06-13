from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0006_add_clientpayment_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientpayment',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
