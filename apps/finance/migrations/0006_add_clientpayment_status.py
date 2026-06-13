from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0005_add_expense_method'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientpayment',
            name='status',
            field=models.CharField(choices=[('confirmed', 'مؤكدة'), ('cancelled', 'ملغاة')], default='confirmed', max_length=20, verbose_name='الحالة'),
        ),
    ]
