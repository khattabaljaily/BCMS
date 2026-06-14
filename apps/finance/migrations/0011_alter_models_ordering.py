from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0010_alter_treasury_balance_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='expense',
            options={
                'ordering': ['-id'],
                'verbose_name': 'مصروف',
                'verbose_name_plural': 'مصروفات',
            },
        ),
        migrations.AlterModelOptions(
            name='clientpayment',
            options={
                'ordering': ['-id'],
                'verbose_name': 'دفعة عميل',
                'verbose_name_plural': 'مدفوعات العملاء',
            },
        ),
    ]
