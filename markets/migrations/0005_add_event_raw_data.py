# Generated manually - Add raw_data field to Event model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('markets', '0004_remove_tags_and_matches'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='raw_data',
            field=models.JSONField(default=dict, help_text='Raw API response for this event'),
        ),
    ]
