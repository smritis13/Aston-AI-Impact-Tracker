from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0051_usecasetheme_is_deleted_alter_usecasetheme_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='usecase',
            name='domain',
            field=models.CharField(blank=True, help_text='Domain parsed from the source URL, e.g. aston.ac.uk', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='usecase',
            name='publisher',
            field=models.CharField(blank=True, help_text='Publisher/organisation that published the source, if identifiable', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='usecase',
            name='content_type',
            field=models.CharField(blank=True, choices=[('press_release', 'Press Release'), ('peer_reviewed', 'Peer-Reviewed Output'), ('news', 'News Article'), ('policy', 'Policy Document'), ('testimonial', 'Testimonial/Letter'), ('other', 'Other')], help_text="Classification of the source's publication type", max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='usecase',
            name='direct_quote',
            field=models.TextField(blank=True, help_text='Verbatim quote from the source supporting a citation or impact claim', null=True),
        ),
    ]
