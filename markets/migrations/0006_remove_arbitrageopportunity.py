# Generated manually - Remove ArbitrageOpportunity model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('markets', '0005_add_event_raw_data'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ArbitrageOpportunity',
        ),
    ]
