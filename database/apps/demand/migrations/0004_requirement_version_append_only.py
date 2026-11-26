from django.db import migrations


def protect_versions(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    schema_editor.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_buyer_requirement_version_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'Buyer requirement versions are immutable';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    schema_editor.execute(
        """
        CREATE TRIGGER buyer_requirement_version_no_update
        BEFORE UPDATE ON buyer_requirement_version
        FOR EACH ROW EXECUTE FUNCTION prevent_buyer_requirement_version_mutation();
        """
    )
    schema_editor.execute(
        """
        CREATE TRIGGER buyer_requirement_version_no_delete
        BEFORE DELETE ON buyer_requirement_version
        FOR EACH ROW EXECUTE FUNCTION prevent_buyer_requirement_version_mutation();
        """
    )


def remove_version_protection(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    schema_editor.execute(
        "DROP TRIGGER IF EXISTS buyer_requirement_version_no_update "
        "ON buyer_requirement_version"
    )
    schema_editor.execute(
        "DROP TRIGGER IF EXISTS buyer_requirement_version_no_delete "
        "ON buyer_requirement_version"
    )
    schema_editor.execute(
        "DROP FUNCTION IF EXISTS prevent_buyer_requirement_version_mutation()"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("demand", "0003_alter_buyerrequirement_completeness_status_and_more"),
    ]

    operations = [
        migrations.RunPython(protect_versions, remove_version_protection),
    ]
