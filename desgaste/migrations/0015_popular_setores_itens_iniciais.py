from django.db import migrations


def popular_setores_e_itens(apps, schema_editor):
    SetorInspecao = apps.get_model("desgaste", "SetorInspecao")
    ItemInspecao = apps.get_model("desgaste", "ItemInspecao")

    setores = [
        {
            "codigo": "T1",
            "nome": "CPR - X45",
            "tipo": "trecho",
            "ordem": 1,
            "limite_inicial": "CPR",
            "limite_final": "X45",
        },
        {
            "codigo": "T2",
            "nome": "X45 - ABV",
            "tipo": "trecho",
            "ordem": 2,
            "limite_inicial": "X45",
            "limite_final": "ABV",
        },
        {
            "codigo": "T3",
            "nome": "ABV - ECT",
            "tipo": "trecho",
            "ordem": 3,
            "limite_inicial": "ABV",
            "limite_final": "ECT",
        },
        {
            "codigo": "T4",
            "nome": "ECT - VDC",
            "tipo": "trecho",
            "ordem": 4,
            "limite_inicial": "ECT",
            "limite_final": "VDC",
        },
        {
            "codigo": "PCR",
            "nome": "Pátio Capão Redondo",
            "tipo": "patio",
            "ordem": 5,
            "limite_inicial": "PCR",
            "limite_final": "PCR",
        },
        {
            "codigo": "PGC",
            "nome": "Pátio Guido Caloi",
            "tipo": "patio",
            "ordem": 6,
            "limite_inicial": "PGC",
            "limite_final": "PGC",
        },
    ]

    for setor in setores:
        SetorInspecao.objects.update_or_create(
            codigo=setor["codigo"],
            defaults={
                "nome": setor["nome"],
                "tipo": setor["tipo"],
                "ordem": setor["ordem"],
                "limite_inicial": setor["limite_inicial"],
                "limite_final": setor["limite_final"],
                "ativo": True,
            },
        )

    itens = [
        "ALMOFADA DANIFICADA",
        "FIXAÇÃO DANIFICADA",
        "FIXAÇÃO SOLTA",
        "DORMENTE DANIFICADO",
        "TRILHO COM DESGASTE",
        "TRILHO COM TRINCA",
        "JUNTA COMPROMETIDA",
        "PARAFUSO AUSENTE",
        "LASTRO IRREGULAR",
        "INTERFERÊNCIA NA VIA",
        "OUTROS",
    ]

    for nome in itens:
        ItemInspecao.objects.update_or_create(
            nome=nome,
            defaults={
                "ativo": True,
            },
        )


def remover_setores_e_itens(apps, schema_editor):
    SetorInspecao = apps.get_model("desgaste", "SetorInspecao")
    ItemInspecao = apps.get_model("desgaste", "ItemInspecao")

    codigos_setores = ["T1", "T2", "T3", "T4", "PCR", "PGC"]
    nomes_itens = [
        "ALMOFADA DANIFICADA",
        "FIXAÇÃO DANIFICADA",
        "FIXAÇÃO SOLTA",
        "DORMENTE DANIFICADO",
        "TRILHO COM DESGASTE",
        "TRILHO COM TRINCA",
        "JUNTA COMPROMETIDA",
        "PARAFUSO AUSENTE",
        "LASTRO IRREGULAR",
        "INTERFERÊNCIA NA VIA",
        "OUTROS",
    ]

    SetorInspecao.objects.filter(codigo__in=codigos_setores).delete()
    ItemInspecao.objects.filter(nome__in=nomes_itens).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("desgaste", "0014_ocorrenciainspecaotrecho_mt_problema"),
    ]

    operations = [
        migrations.RunPython(
            popular_setores_e_itens,
            remover_setores_e_itens,
        ),
    ]