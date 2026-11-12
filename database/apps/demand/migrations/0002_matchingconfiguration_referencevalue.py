import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demand', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MatchingConfiguration',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('configuration_key', models.CharField(max_length=100)),
                ('version', models.PositiveIntegerField()),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('approved', 'Approved'), ('retired', 'Retired')], default='draft', max_length=20)),
                ('configuration', models.JSONField(default=dict)),
                ('approved_by', models.CharField(blank=True, default='', max_length=255)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'matching_configuration',
                'indexes': [models.Index(fields=['configuration_key', 'status'], name='matching_co_configu_58ab80_idx')],
                'constraints': [models.UniqueConstraint(fields=('configuration_key', 'version'), name='uq_matching_configuration_version')],
            },
        ),
        migrations.CreateModel(
            name='ReferenceValue',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('reference_type', models.CharField(max_length=50)),
                ('code', models.CharField(max_length=100)),
                ('display_name', models.CharField(max_length=255)),
                ('version', models.PositiveIntegerField(default=1)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('active', 'Active'), ('retired', 'Retired')], default='draft', max_length=20)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('approved_by', models.CharField(blank=True, default='', max_length=255)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'demand_reference_value',
                'indexes': [models.Index(fields=['reference_type', 'status'], name='demand_refe_referen_5944d3_idx'), models.Index(fields=['reference_type', 'code'], name='demand_refe_referen_faa96f_idx')],
                'constraints': [models.UniqueConstraint(fields=('reference_type', 'code', 'version'), name='uq_demand_reference_value_version')],
            },
        ),
    ]
