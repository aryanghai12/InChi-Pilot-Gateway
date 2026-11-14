import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BuyerRequirement',
            fields=[
                ('requirement_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('buyer_organisation_name', models.CharField(blank=True, default='', max_length=255)),
                ('buyer_reference', models.CharField(blank=True, default='', max_length=100)),
                ('target_market', models.CharField(blank=True, default='', max_length=100)),
                ('product_category_id', models.CharField(blank=True, default='', max_length=100)),
                ('requirement_title', models.CharField(blank=True, default='', max_length=255)),
                ('requirement_status', models.CharField(default='draft', max_length=50)),
                ('completeness_status', models.CharField(default='incomplete', max_length=50)),
                ('matching_ready', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='created_buyer_requirements', to=settings.AUTH_USER_MODEL)),
                ('owner_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='owned_buyer_requirements', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='updated_buyer_requirements', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'buyer_requirement',
            },
        ),
        migrations.CreateModel(
            name='BuyerRequirementVersion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('version', models.PositiveIntegerField()),
                ('requirement_notes', models.TextField(blank=True, default='')),
                ('schema_version', models.CharField(default='buyer-requirement-v1', max_length=50)),
                ('matching_configuration_version', models.CharField(blank=True, default='', max_length=100)),
                ('change_reason', models.CharField(blank=True, default='', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='created_requirement_versions', to=settings.AUTH_USER_MODEL)),
                ('requirement', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='versions', to='demand.buyerrequirement')),
            ],
            options={
                'db_table': 'buyer_requirement_version',
            },
        ),
        migrations.CreateModel(
            name='MatchingReadinessBlocker',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('field_id', models.CharField(max_length=20)),
                ('reason_code', models.CharField(max_length=100)),
                ('reason_detail', models.TextField(blank=True, default='')),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('requirement_version', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='matching_readiness_blockers', to='demand.buyerrequirementversion')),
            ],
            options={
                'db_table': 'matching_readiness_blocker',
            },
        ),
        migrations.CreateModel(
            name='RequirementCommercialTerms',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('target_price_min', models.DecimalField(blank=True, decimal_places=4, max_digits=18, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('target_price_max', models.DecimalField(blank=True, decimal_places=4, max_digits=18, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('currency_code', models.CharField(blank=True, default='', max_length=3)),
                ('price_basis', models.CharField(blank=True, default='', max_length=100)),
                ('requirement_version', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='commercial_terms', to='demand.buyerrequirementversion')),
            ],
            options={
                'db_table': 'requirement_commercial_terms',
            },
        ),
        migrations.CreateModel(
            name='RequirementDelivery',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('delivery_location', models.JSONField(blank=True, default=dict)),
                ('delivery_window_start', models.DateField(blank=True, null=True)),
                ('delivery_window_end', models.DateField(blank=True, null=True)),
                ('required_lead_time_value', models.PositiveIntegerField(blank=True, null=True)),
                ('required_lead_time_unit', models.CharField(blank=True, default='', max_length=50)),
                ('requirement_version', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='delivery', to='demand.buyerrequirementversion')),
            ],
            options={
                'db_table': 'requirement_delivery',
            },
        ),
        migrations.CreateModel(
            name='RequirementEligibilityCriterion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('criterion_key', models.CharField(max_length=100)),
                ('operator', models.CharField(max_length=50)),
                ('criterion_value', models.JSONField(default=dict)),
                ('unknown_policy', models.CharField(blank=True, default='', max_length=50)),
                ('criteria_version', models.CharField(blank=True, default='', max_length=50)),
                ('requirement_version', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='eligibility_criteria', to='demand.buyerrequirementversion')),
            ],
            options={
                'db_table': 'requirement_eligibility_criterion',
            },
        ),
        migrations.CreateModel(
            name='RequirementEvidenceCriterion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('evidence_type', models.CharField(max_length=100)),
                ('criterion_value', models.JSONField(blank=True, default=dict)),
                ('classification', models.CharField(choices=[('mandatory', 'Mandatory'), ('preferred', 'Preferred')], max_length=20)),
                ('taxonomy_version', models.CharField(blank=True, default='', max_length=50)),
                ('requirement_version', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='evidence_criteria', to='demand.buyerrequirementversion')),
            ],
            options={
                'db_table': 'requirement_evidence_criterion',
            },
        ),
        migrations.CreateModel(
            name='RequirementPreference',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('preference_key', models.CharField(max_length=100)),
                ('preference_value', models.JSONField(default=dict)),
                ('priority_weight_key', models.CharField(blank=True, default='', max_length=100)),
                ('criteria_version', models.CharField(blank=True, default='', max_length=50)),
                ('requirement_version', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='preferences', to='demand.buyerrequirementversion')),
            ],
            options={
                'db_table': 'requirement_preference',
            },
        ),
        migrations.CreateModel(
            name='RequirementQuantity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('quantity_value', models.DecimalField(blank=True, decimal_places=4, max_digits=18, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('quantity_unit', models.CharField(blank=True, default='', max_length=50)),
                ('order_frequency', models.CharField(blank=True, default='', max_length=50)),
                ('recurrence_interval', models.PositiveIntegerField(blank=True, null=True)),
                ('recurrence_period', models.CharField(blank=True, default='', max_length=50)),
                ('requirement_version', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='quantity', to='demand.buyerrequirementversion')),
            ],
            options={
                'db_table': 'requirement_quantity',
            },
        ),
        migrations.CreateModel(
            name='RequirementSpecification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('attributes', models.JSONField(blank=True, default=dict)),
                ('schema_version', models.CharField(default='category-schema-v1', max_length=50)),
                ('requirement_version', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='specification', to='demand.buyerrequirementversion')),
            ],
            options={
                'db_table': 'requirement_specification',
            },
        ),
        migrations.AddIndex(
            model_name='buyerrequirement',
            index=models.Index(fields=['requirement_status'], name='buyer_requi_require_dbc024_idx'),
        ),
        migrations.AddIndex(
            model_name='buyerrequirement',
            index=models.Index(fields=['completeness_status'], name='buyer_requi_complet_669914_idx'),
        ),
        migrations.AddIndex(
            model_name='buyerrequirement',
            index=models.Index(fields=['matching_ready'], name='buyer_requi_matchin_c34b29_idx'),
        ),
        migrations.AddIndex(
            model_name='buyerrequirement',
            index=models.Index(fields=['owner_user'], name='buyer_requi_owner_u_cc16ef_idx'),
        ),
        migrations.AddIndex(
            model_name='buyerrequirement',
            index=models.Index(fields=['target_market'], name='buyer_requi_target__7563a6_idx'),
        ),
        migrations.AddIndex(
            model_name='buyerrequirement',
            index=models.Index(fields=['product_category_id'], name='buyer_requi_product_3a3bef_idx'),
        ),
        migrations.AddIndex(
            model_name='buyerrequirement',
            index=models.Index(fields=['-updated_at'], name='buyer_requi_updated_5ddf7e_idx'),
        ),
        migrations.AddIndex(
            model_name='buyerrequirementversion',
            index=models.Index(fields=['requirement', 'version'], name='buyer_requi_require_69c5c5_idx'),
        ),
        migrations.AddIndex(
            model_name='buyerrequirementversion',
            index=models.Index(fields=['-created_at'], name='buyer_requi_created_f9875d_idx'),
        ),
        migrations.AddConstraint(
            model_name='buyerrequirementversion',
            constraint=models.UniqueConstraint(fields=('requirement', 'version'), name='uq_buyer_requirement_version'),
        ),
        migrations.AddIndex(
            model_name='matchingreadinessblocker',
            index=models.Index(fields=['requirement_version', 'active'], name='matching_re_require_d6cccd_idx'),
        ),
        migrations.AddConstraint(
            model_name='matchingreadinessblocker',
            constraint=models.UniqueConstraint(fields=('requirement_version', 'field_id', 'reason_code'), name='uq_matching_readiness_blocker'),
        ),
        migrations.AddConstraint(
            model_name='requirementcommercialterms',
            constraint=models.CheckConstraint(condition=models.Q(('target_price_min__isnull', True), ('target_price_min__gt', 0), _connector='OR'), name='target_price_min_positive_when_supplied'),
        ),
        migrations.AddConstraint(
            model_name='requirementcommercialterms',
            constraint=models.CheckConstraint(condition=models.Q(('target_price_max__isnull', True), ('target_price_max__gt', 0), _connector='OR'), name='target_price_max_positive_when_supplied'),
        ),
        migrations.AddConstraint(
            model_name='requirementcommercialterms',
            constraint=models.CheckConstraint(condition=models.Q(('target_price_min__isnull', True), ('target_price_max__isnull', True), ('target_price_min__lte', models.F('target_price_max')), _connector='OR'), name='target_price_min_lte_max'),
        ),
        migrations.AddConstraint(
            model_name='requirementdelivery',
            constraint=models.CheckConstraint(condition=models.Q(('delivery_window_start__isnull', True), ('delivery_window_end__isnull', True), ('delivery_window_start__lte', models.F('delivery_window_end')), _connector='OR'), name='delivery_window_start_lte_end'),
        ),
        migrations.AddConstraint(
            model_name='requirementeligibilitycriterion',
            constraint=models.UniqueConstraint(fields=('requirement_version', 'criterion_key'), name='uq_requirement_eligibility_key'),
        ),
        migrations.AddIndex(
            model_name='requirementevidencecriterion',
            index=models.Index(fields=['requirement_version', 'classification'], name='requirement_require_3d1e3e_idx'),
        ),
        migrations.AddConstraint(
            model_name='requirementpreference',
            constraint=models.UniqueConstraint(fields=('requirement_version', 'preference_key'), name='uq_requirement_preference_key'),
        ),
        migrations.AddConstraint(
            model_name='requirementquantity',
            constraint=models.CheckConstraint(condition=models.Q(('quantity_value__isnull', True), ('quantity_value__gt', 0), _connector='OR'), name='quantity_value_positive_when_supplied'),
        ),
    ]
