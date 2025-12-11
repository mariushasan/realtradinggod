# Generated manually
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('markets', '0002_add_tagmatch_model'),
    ]

    operations = [
        # Create Event model
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exchange', models.CharField(choices=[('kalshi', 'Kalshi'), ('polymarket', 'Polymarket')], max_length=20)),
                ('external_id', models.CharField(max_length=255)),
                ('title', models.CharField(max_length=500)),
                ('description', models.TextField(blank=True)),
                ('category', models.CharField(blank=True, max_length=255)),
                ('url', models.URLField(blank=True, max_length=500)),
                ('volume', models.FloatField(default=0.0)),
                ('volume_24h', models.FloatField(default=0.0)),
                ('liquidity', models.FloatField(default=0.0)),
                ('open_interest', models.FloatField(default=0.0)),
                ('is_active', models.BooleanField(default=True)),
                ('mutually_exclusive', models.BooleanField(default=False)),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-updated_at'],
                'unique_together': {('exchange', 'external_id')},
            },
        ),
        # Create EventMatch model
        migrations.CreateModel(
            name='EventMatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('similarity_score', models.FloatField(default=0.0)),
                ('match_reason', models.TextField(blank=True, help_text='Why these events were matched')),
                ('is_verified', models.BooleanField(default=False, help_text='Manually verified as same event')),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('kalshi_event', models.ForeignKey(
                    limit_choices_to={'exchange': 'kalshi'},
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='kalshi_matches',
                    to='markets.event'
                )),
                ('polymarket_event', models.ForeignKey(
                    limit_choices_to={'exchange': 'polymarket'},
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='polymarket_matches',
                    to='markets.event'
                )),
            ],
            options={
                'ordering': ['-similarity_score', '-updated_at'],
                'unique_together': {('kalshi_event', 'polymarket_event')},
            },
        ),
        # Add event ForeignKey to Market model
        migrations.AddField(
            model_name='market',
            name='event',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='markets',
                to='markets.event'
            ),
        ),
        # Add additional fields to Market model
        migrations.AddField(
            model_name='market',
            name='volume',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='market',
            name='volume_24h',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='market',
            name='liquidity',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='market',
            name='open_interest',
            field=models.FloatField(default=0.0),
        ),
    ]
