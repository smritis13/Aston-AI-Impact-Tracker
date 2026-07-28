from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0050_usecase_reference_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='usecasetheme',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='usecasetheme',
            name='title',
            field=models.CharField(max_length=200),
        ),
    ]
