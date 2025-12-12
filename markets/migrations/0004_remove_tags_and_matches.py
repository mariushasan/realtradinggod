# Generated manually - Remove Tag, TagMatch, MarketMatch models

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('markets', '0003_add_event_and_eventmatch'),
    ]

    operations = [
        # Remove the Market.tags ManyToMany field
        migrations.RemoveField(
            model_name='market',
            name='tags',
        ),
        # Remove the ArbitrageOpportunity.market_match ForeignKey
        migrations.RemoveField(
            model_name='arbitrageopportunity',
            name='market_match',
        ),
        # Remove TagMatch model (depends on Tag, so remove first)
        migrations.DeleteModel(
            name='TagMatch',
        ),
        # Remove Tag model
        migrations.DeleteModel(
            name='Tag',
        ),
        # Remove MarketMatch model
        migrations.DeleteModel(
            name='MarketMatch',
        ),
    ]
