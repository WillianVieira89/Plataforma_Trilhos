from django.db import migrations


def reativar_e_completar_itens(apps, schema_editor):
    ItemInspecao = apps.get_model("desgaste", "ItemInspecao")

    # Reativa todos os itens já existentes no banco.
    # Isso resolve casos em que o item aparece no histórico,
    # mas não aparece no formulário porque ativo=False.
    ItemInspecao.objects.all().update(ativo=True)

    itens = [
        "GRAMPO AUSENTE",
        "GRAMPO DANIFICADO",
        "GRAMPO SOLTO",
        "CLIP AUSENTE",
        "CLIP DANIFICADO",
        "CLIP INVERTIDO",
        "CLIP QUEBRADO",
        "CLIPS AUSENTE",
        "CLIPS DANIFICADO",
        "CLIPS INVERTIDO",
        "CLIPS QUEBRADO",
        "AGUA NO NICHO",
        "ÁGUA NO NICHO",
        "ALMA DO TRILHO COM DEFEITO",
        "ALMOFADA AUSENTE",
        "ALMOFADA DANIFICADA",
        "ALMOFADA DESLOCADA",
        "APARELHO DILATADOR COM ANOMALIA",
        "APARELHO DILATADOR COM FOLGA",
        "APARELHO DILATADOR COM OBSTRUÇÃO",
        "ARRUELA DIFERENTE",
        "ARRUELA INVERTIDA",
        "ARRUELA INVERTIDA/DIFERENTE",
        "BARRA DE JUNÇÃO AUSENTE",
        "BARRA DE JUNÇÃO DANIFICADA",
        "BARRA DE JUNÇÃO FROUXA",
        "BOLETO DO TRILHO COM DESGASTE",
        "BOLETO DO TRILHO COM MARCA",
        "BOLETO DO TRILHO COM REBARBA",
        "CHUMBADOR AUSENTE",
        "CHUMBADOR DANIFICADO",
        "CHUMBADOR FROUXO",
        "CONTRA TRILHO COM ANOMALIA",
        "CONTRA TRILHO COM FOLGA",
        "DORMENTE COM DESGASTE",
        "DORMENTE DANIFICADO",
        "DORMENTE DESALINHADO",
        "DORMENTE QUEBRADO",
        "DORMENTE TRINCADO",
        "DRENAGEM OBSTRUÍDA",
        "FIXAÇÃO AUSENTE",
        "FIXAÇÃO COM DESGASTE",
        "FIXAÇÃO DANIFICADA",
        "FIXAÇÃO DESLOCADA",
        "FIXAÇÃO SOLTA",
        "INTERFERÊNCIA NA VIA",
        "JACARÉ COM DESGASTE",
        "JACARÉ COM TRINCA",
        "JUNTA COM DESNÍVEL",
        "JUNTA COM FOLGA",
        "JUNTA COMPROMETIDA",
        "LASTRO CONTAMINADO",
        "LASTRO DESLOCADO",
        "LASTRO INSUFICIENTE",
        "LASTRO IRREGULAR",
        "LIMPEZA NECESSÁRIA",
        "OBJETO NA VIA",
        "PARAFUSO AUSENTE",
        "PARAFUSO DANIFICADO",
        "PARAFUSO FROUXO",
        "PONTA DE AGULHA COM ANOMALIA",
        "PONTA DE AGULHA COM DESGASTE",
        "PONTA DE AGULHA COM FOLGA",
        "RETENSOR AUSENTE",
        "RETENSOR DANIFICADO",
        "RETENSOR SOLTO",
        "SAPATA DANIFICADA",
        "SAPATA DESLOCADA",
        "SOLDA COM ANOMALIA",
        "SOLDA COM DESNÍVEL",
        "SOLDA COM REBARBA",
        "SOLDA COM TRINCA",
        "TALA AUSENTE",
        "TALA DANIFICADA",
        "TALA FROUXA",
        "TIREFÃO AUSENTE",
        "TIREFÃO DANIFICADO",
        "TIREFÃO FROUXO",
        "TRILHO COM CORROSÃO",
        "TRILHO COM DESGASTE",
        "TRILHO COM DESNÍVEL",
        "TRILHO COM EMPENO",
        "TRILHO COM FRATURA",
        "TRILHO COM REBARBA",
        "TRILHO COM TRINCA",
        "TRILHO MARCADO",
        "VIA COM DESALINHAMENTO",
        "VIA COM DESNIVELAMENTO",
        "VIA COM SUJIDADE",
        "OUTROS",
    ]

    for nome in itens:
        qs = ItemInspecao.objects.filter(nome=nome)

        if qs.exists():
            qs.update(ativo=True)
        else:
            ItemInspecao.objects.create(
                nome=nome,
                ativo=True,
            )


class Migration(migrations.Migration):

    dependencies = [
        ("desgaste", "0016_popular_itens_ocorrencia_completos"),
    ]

    operations = [
        migrations.RunPython(
            reativar_e_completar_itens,
            migrations.RunPython.noop,
        ),
    ]