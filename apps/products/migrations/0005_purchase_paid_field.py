from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_purchase_invoice'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseinvoice',
            name='paid',
            field=models.BooleanField(default=False, verbose_name='مدفوعة'),
        ),
    ]
