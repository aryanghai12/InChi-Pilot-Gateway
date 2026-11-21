from django.db import migrations


def protect_audit_rows(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    schema_editor.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_readiness_audit_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'Readiness audit events are append-only';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    schema_editor.execute(
        """
        CREATE TRIGGER readiness_audit_no_update
        BEFORE UPDATE ON readiness_audit_event
        FOR EACH ROW EXECUTE FUNCTION prevent_readiness_audit_mutation();
        """
    )
    schema_editor.execute(
        """
        CREATE TRIGGER readiness_audit_no_delete
        BEFORE DELETE ON readiness_audit_event
        FOR EACH ROW EXECUTE FUNCTION prevent_readiness_audit_mutation();
        """
    )


def remove_audit_protection(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    schema_editor.execute("DROP TRIGGER IF EXISTS readiness_audit_no_update ON readiness_audit_event")
    schema_editor.execute("DROP TRIGGER IF EXISTS readiness_audit_no_delete ON readiness_audit_event")
    schema_editor.execute("DROP FUNCTION IF EXISTS prevent_readiness_audit_mutation()")


class Migration(migrations.Migration):
    dependencies = [
        ("readiness", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(protect_audit_rows, remove_audit_protection),
    ]
