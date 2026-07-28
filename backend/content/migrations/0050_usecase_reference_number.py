# Generated migration for hard-coded reference numbering

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0049_savedentitysearch'),
    ]

    operations = [
        migrations.AddField(
            model_name='usecase',
            name='reference_number',
            field=models.IntegerField(blank=True, help_text='Hard-coded reference number for case study generation', null=True),
        ),
    ]
