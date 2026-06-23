from django.db import migrations


LUBRIFICADORES = [f"LUB-{i:02d}" for i in range(1, 27)]


def populate(apps, schema_editor):
    Lubrificador = apps.get_model("desgaste", "Lubrificador")
    for nome in LUBRIFICADORES:
        Lubrificador.objects.get_or_create(
            nome=nome,
            defaults={"status_operacional": "OPERANTE", "via": "", "mt": ""},
        )


def reverse_populate(apps, schema_editor):
    Lubrificador = apps.get_model("desgaste", "Lubrificador")
    Lubrificador.objects.filter(nome__in=LUBRIFICADORES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("desgaste", "0019_add_lubrificador"),
    ]

    operations = [
        migrations.RunPython(populate, reverse_populate),
    ]
