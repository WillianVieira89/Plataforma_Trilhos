from django.db import migrations, models


def converter_via_para_numerico(apps, schema_editor):
    InspecaoTrecho = apps.get_model("desgaste", "InspecaoTrecho")
    mapa = {"VIA_01": "1", "VIA_02": "2"}
    for obj in InspecaoTrecho.objects.filter(via__in=mapa.keys()):
        obj.via = mapa[obj.via]
        obj.save(update_fields=["via"])


class Migration(migrations.Migration):

    dependencies = [
        ("desgaste", "0017_reativar_e_completar_itens_ocorrencia"),
    ]

    operations = [
        migrations.RunPython(
            converter_via_para_numerico,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="inspecaotrecho",
            name="via",
            field=models.CharField(
                blank=True,
                choices=[("1", "Via 01"), ("2", "Via 02")],
                max_length=1,
            ),
        ),
    ]
