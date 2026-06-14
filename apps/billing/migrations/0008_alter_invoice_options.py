from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0007_restore_invoice_decimal_defaults'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='invoice',
            options={
                'ordering': ['-id'],
                'verbose_name': 'فاتورة',
                'verbose_name_plural': 'الفواتير',
            },
        ),
    ]
