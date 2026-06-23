from django.db import migrations


def limpar_dados_lubrificadores(apps, schema_editor):
    Lubrificador = apps.get_model(
        "desgaste",
        "Lubrificador",
    )
    RegistroLubrificador = apps.get_model(
        "desgaste",
        "RegistroLubrificador",
    )
    OrdemCorretivaLubrificador = apps.get_model(
        "desgaste",
        "OrdemCorretivaLubrificador",
    )

    total_lubrificadores = Lubrificador.objects.count()
    total_registros = RegistroLubrificador.objects.count()
    total_ordens = OrdemCorretivaLubrificador.objects.count()

    # Remove primeiro as ordens vinculadas às corretivas.
    OrdemCorretivaLubrificador.objects.all().delete()

    # Remove corretivas antes das inspeções de origem.
    RegistroLubrificador.objects.filter(
        tipo_atuacao="CORRETIVA"
    ).delete()

    # Remove inspeções e demais registros dos lubrificadores.
    RegistroLubrificador.objects.all().delete()

    # Preserva os equipamentos e redefine o status atual.
    Lubrificador.objects.all().update(
        status_operacional="OPERANTE"
    )

    registros_restantes = (
        RegistroLubrificador.objects.count()
    )
    ordens_restantes = (
        OrdemCorretivaLubrificador.objects.count()
    )
    operacionais = Lubrificador.objects.filter(
        status_operacional="OPERANTE"
    ).count()

    print(
        "Limpeza concluída: "
        f"{total_ordens} ordens removidas, "
        f"{total_registros} registros removidos e "
        f"{total_lubrificadores} lubrificadores preservados."
    )

    print(
        "Resultado final: "
        f"{registros_restantes} registros, "
        f"{ordens_restantes} ordens e "
        f"{operacionais} lubrificadores operacionais."
    )


class Migration(migrations.Migration):

    dependencies = [
        (
            "desgaste",
            "0028_vincular_falha_ordem_corretiva",
        ),
    ]

    operations = [
        migrations.RunPython(
            limpar_dados_lubrificadores,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
