from django.contrib import messages
from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import never_cache
from .relatorios import gerar_excel_ocorrencias_inspecao

from .constants import ESTACOES_MAPA
from .utils import extrair_numero_mt
from .forms import (
    RegistroInspecaoForm,
    InspecaoForm,
    OcorrenciaInspecaoFormSet,
    OcorrenciaInspecaoTrechoForm,
    TrocaTrilhoForm,
    InspecaoLubrificadorForm,
    CorretivaLubrificadorForm,
    OrdemCorretivaLubrificadorFormSet,
    LubrificadorCadastroForm,
)
from .models import (
    Inspecao,
    InspecaoTrecho,
    MedicaoDesgaste,
    Trilho,
    PontoOperacional,
    TrocaTrilho,
    OcorrenciaInspecaoTrecho,
    ItemInspecao,
    ViaChoices,
    TrilhoChoices,
    CriticidadeChoices,
    Lubrificador,
    StatusLubrificadorChoices,
    RegistroLubrificador,
    TipoAtuacaoLubrificadorChoices,
    ResultadoInspecaoChoices,
    ResultadoCorretivaChoices,
    SituacaoPendenciaChoices,
)

MT_TRECHO_INICIAL = 1
MT_TRECHO_FINAL = 10099
PASSO_MT = 2


def valor_campo(obj, nome_campo, default=""):
    return getattr(obj, nome_campo, default)

def valor_display(obj, nome_campo):
    metodo = getattr(obj, f"get_{nome_campo}_display", None)
    if callable(metodo):
        try:
            return metodo()
        except Exception:
            return ""
    return ""

def registrar_inspecao(request):
    all_pontos = PontoOperacional.objects.select_related("estacao").all().order_by("ordem")
    all_trilhos = Trilho.objects.select_related("ponto_operacional").all().order_by(
        "ponto_operacional__ordem", "via", "lado_trilho"
    )

    if request.method == "POST":
        form = RegistroInspecaoForm(request.POST)

        if form.is_valid():
            trilho = form.cleaned_data["trilho"]

            inspecao = Inspecao.objects.create(
                trilho=trilho,
                data_inspecao=form.cleaned_data["data_inspecao"],
                hora_inspecao=form.cleaned_data["hora_inspecao"],
                inspetor=form.cleaned_data["inspetor"],
                tipo_inspecao=form.cleaned_data["tipo_inspecao"],
                observacoes=form.cleaned_data["observacoes"],
            )

            MedicaoDesgaste.objects.create(
                inspecao=inspecao,
                desgaste_vertical_mm=form.cleaned_data["desgaste_vertical_mm"],
                desgaste_lateral_mm=form.cleaned_data["desgaste_lateral_mm"],
                observacao_tecnica=form.cleaned_data["observacao_tecnica"],
                status_desgaste=form.cleaned_data["status_desgaste"],
            )

            messages.success(request, "Inspeção e medição salvas com sucesso.")
            return redirect("registrar_inspecao")
    else:
        form = RegistroInspecaoForm()

    return render(request, "desgaste/registrar_inspecao.html", {
        "form": form,
        "all_pontos": all_pontos,
        "all_trilhos": all_trilhos,
    })

def historico_inspecoes(request):
    pontos = PontoOperacional.objects.select_related("estacao").all().order_by("ordem")
    trilhos = Trilho.objects.select_related("ponto_operacional").all().order_by(
        "ponto_operacional__ordem", "via", "lado_trilho"
    )

    ponto_id = request.GET.get("ponto_operacional")
    via = request.GET.get("via")
    trilho_id = request.GET.get("trilho")

    inspecoes = (
        Inspecao.objects.select_related("trilho__ponto_operacional")
        .all()
        .order_by("-data_inspecao", "-hora_inspecao")
    )

    if ponto_id:
        inspecoes = inspecoes.filter(trilho__ponto_operacional_id=ponto_id)

    if via:
        inspecoes = inspecoes.filter(trilho__via=via)

    if trilho_id:
        inspecoes = inspecoes.filter(trilho_id=trilho_id)

    registros = []
    for inspecao in inspecoes:
        medicao = getattr(inspecao, "medicao", None)
        registros.append({
            "inspecao": inspecao,
            "medicao": medicao,
        })

    return render(request, "desgaste/historico_inspecoes.html", {
        "registros": registros,
        "pontos": pontos,
        "trilhos": trilhos,
        "filtro_ponto": ponto_id or "",
        "filtro_via": via or "",
        "filtro_trilho": trilho_id or "",
    })

def obter_ocorrencias_filtradas(request):
    ocorrencias = (
        OcorrenciaInspecaoTrecho.objects
        .select_related("inspecao__setor", "item")
        .order_by(
            "inspecao__data_inspecao",
            "inspecao__hora_inspecao",
            "trilho",
            "mt_problema",
            "item__nome",
        )
    )

    filtros = {
        "data_ini": request.GET.get("data_ini", "").strip(),
        "data_fim": request.GET.get("data_fim", "").strip(),
        "via": request.GET.get("via", "").strip(),
        "trilho": request.GET.get("trilho", "").strip(),
        "item": request.GET.get("item", "").strip(),
        "criticidade": request.GET.get("criticidade", "").strip(),
    }

    if filtros["data_ini"]:
        ocorrencias = ocorrencias.filter(
            inspecao__data_inspecao__gte=filtros["data_ini"]
        )

    if filtros["data_fim"]:
        ocorrencias = ocorrencias.filter(
            inspecao__data_inspecao__lte=filtros["data_fim"]
        )

    if filtros["via"]:
        ocorrencias = ocorrencias.filter(
            inspecao__via=filtros["via"]
        )

    if filtros["trilho"]:
        ocorrencias = ocorrencias.filter(
            trilho=filtros["trilho"]
        )

    if filtros["item"]:
        ocorrencias = ocorrencias.filter(
            item_id=filtros["item"]
        )

    if filtros["criticidade"]:
        ocorrencias = ocorrencias.filter(
            criticidade=filtros["criticidade"]
        )

    return ocorrencias, filtros

def listar_inspecoes(request):
    ocorrencias = (
        OcorrenciaInspecaoTrecho.objects
        .select_related("inspecao__setor", "item")
        .order_by(
            "inspecao__data_inspecao",
            "inspecao__hora_inspecao",
            "trilho",
            "item__nome",
        )
    )

    return render(request, "desgaste/inspecoes/listar_inspecoes.html", {
        "ocorrencias": ocorrencias,
    })

def exportar_excel_inspecoes(request):
    ocorrencias, filtros = obter_ocorrencias_filtradas(request)

    wb = gerar_excel_ocorrencias_inspecao(ocorrencias)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="relatorio_inspecoes_ocorrencias.xlsx"'

    wb.save(response)
    return response

def relatorio_inspecoes(request):
    mostrar_previa = request.GET.get("visualizar") == "1"

    ocorrencias, filtros = obter_ocorrencias_filtradas(request)

    if not mostrar_previa:
        ocorrencias = OcorrenciaInspecaoTrecho.objects.none()

    itens = ItemInspecao.objects.filter(ativo=True).order_by("nome")

    return render(request, "desgaste/relatorios/relatorio_inspecoes.html", {
        "ocorrencias": ocorrencias,
        "itens": itens,
        "via_choices": ViaChoices.choices,
        "trilho_choices": TrilhoChoices.choices,
        "criticidade_choices": CriticidadeChoices.choices,
        "filtros": filtros,
        "mostrar_previa": mostrar_previa,
    })

def nova_inspecao(request):
    if request.method == "POST":
        form = InspecaoForm(request.POST)
        formset = OcorrenciaInspecaoFormSet(request.POST, request.FILES)

        if form.is_valid() and formset.is_valid():
            inspecao = form.save()
            formset.instance = inspecao
            formset.save()

            messages.success(request, "Inspeção cadastrada com sucesso.")
            return redirect("listar_inspecoes")
    else:
        form = InspecaoForm()
        formset = OcorrenciaInspecaoFormSet()

    return render(request, "desgaste/inspecoes/form_inspecao.html", {
        "form": form,
        "formset": formset,
        "titulo": "Nova Inspeção",
    })

def editar_inspecao(request, pk):
    inspecao = get_object_or_404(InspecaoTrecho, pk=pk)

    if request.method == "POST":
        form = InspecaoForm(request.POST, instance=inspecao)
        formset = OcorrenciaInspecaoFormSet(request.POST, request.FILES, instance=inspecao)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()

            messages.success(request, "Inspeção atualizada com sucesso.")
            return redirect("listar_inspecoes")
    else:
        form = InspecaoForm(instance=inspecao)
        formset = OcorrenciaInspecaoFormSet(instance=inspecao)

    return render(request, "desgaste/inspecoes/form_inspecao.html", {
        "form": form,
        "formset": formset,
        "titulo": "Editar Inspeção",
    })
    
def editar_ocorrencia_inspecao(request, pk):
    ocorrencia = get_object_or_404(
        OcorrenciaInspecaoTrecho.objects.select_related("inspecao__setor", "item"),
        pk=pk,
    )

    if request.method == "POST":
        form = OcorrenciaInspecaoTrechoForm(
            request.POST,
            request.FILES,
            instance=ocorrencia,
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Ocorrência atualizada com sucesso.")
            return redirect("listar_inspecoes")
    else:
        form = OcorrenciaInspecaoTrechoForm(instance=ocorrencia)

    return render(request, "desgaste/inspecoes/form_ocorrencia.html", {
        "form": form,
        "ocorrencia": ocorrencia,
        "titulo": "Editar ocorrência",
    })

def excluir_ocorrencia_inspecao(request, pk):
    ocorrencia = get_object_or_404(
        OcorrenciaInspecaoTrecho.objects.select_related("inspecao__setor", "item"),
        pk=pk,
    )

    if request.method == "POST":
        ocorrencia.delete()
        messages.success(request, "Ocorrência excluída com sucesso.")
        return redirect("listar_inspecoes")

    return render(request, "desgaste/inspecoes/confirmar_exclusao_ocorrencia.html", {
        "ocorrencia": ocorrencia,
    })

def listar_trocas_trilho(request):
    trocas = TrocaTrilho.objects.all().order_by("-data_troca", "-hora_troca")

    via = request.GET.get("via")
    trilho = request.GET.get("trilho")
    data_ini = request.GET.get("data_ini")
    data_fim = request.GET.get("data_fim")

    if via:
        trocas = trocas.filter(via=via)

    if trilho:
        trocas = trocas.filter(trilho=trilho)

    if data_ini:
        trocas = trocas.filter(data_troca__gte=data_ini)

    if data_fim:
        trocas = trocas.filter(data_troca__lte=data_fim)

    return render(request, "desgaste/trocas_trilho/listar_trocas.html", {
        "trocas": trocas,
        "filtro_via": via or "",
        "filtro_trilho": trilho or "",
        "filtro_data_ini": data_ini or "",
        "filtro_data_fim": data_fim or "",
    })

def nova_troca_trilho(request):
    if request.method == "POST":
        form = TrocaTrilhoForm(request.POST, request.FILES, instance=TrocaTrilho())
        if form.is_valid():
            form.save()
            messages.success(request, "Troca de trilho cadastrada com sucesso.")
            return redirect("mapa_trocas_trilho")
    else:
        form = TrocaTrilhoForm(instance=TrocaTrilho())

    return render(request, "desgaste/trocas_trilho/form_troca.html", {
        "form": form,
        "titulo": "Cadastro Troca de Trilho",
    })

def editar_troca_trilho(request, pk):
    troca = get_object_or_404(TrocaTrilho, pk=pk)

    if request.method == "POST":
        form = TrocaTrilhoForm(request.POST, request.FILES, instance=troca)
        if form.is_valid():
            form.save()
            messages.success(request, "Troca de trilho atualizada com sucesso.")
            return redirect("mapa_trocas_trilho")
    else:
        form = TrocaTrilhoForm(instance=troca)

    return render(request, "desgaste/trocas_trilho/form_troca.html", {
        "form": form,
        "titulo": "Editar Troca de Trilho",
    })

def tela_inicial(request):
    return render(request, "desgaste/tela_inicial.html")

def mapa_trocas_trilho(request):
    trocas = TrocaTrilho.objects.all().order_by("via", "trilho", "mt_inicial", "data_troca")

    registros_processados = []

    for troca in trocas:
        mt_ini_num = extrair_numero_mt(valor_campo(troca, "mt_inicial"))
        mt_fim_num = extrair_numero_mt(valor_campo(troca, "mt_final"))

        if mt_ini_num is None or mt_fim_num is None:
            continue

        if mt_fim_num < mt_ini_num:
            mt_ini_num, mt_fim_num = mt_fim_num, mt_ini_num

        hora_inicio = valor_campo(troca, "hora_inicio_troca", None) or valor_campo(troca, "hora_troca", None)
        hora_fim = valor_campo(troca, "hora_fim_troca", None) or valor_campo(troca, "hora_troca", None)

        imagem = valor_campo(troca, "imagem", None)
        imagem_url = ""
        try:
            if imagem:
                imagem_url = imagem.url
        except Exception:
            imagem_url = ""

        registros_processados.append({
            "id": troca.id,
            "via": str(valor_campo(troca, "via") or "").strip(),
            "trilho": valor_display(troca, "trilho") or valor_campo(troca, "trilho"),
            "trilho_codigo": str(valor_campo(troca, "trilho") or "").strip().upper(),
            "data_troca": valor_campo(troca, "data_troca"),
            "hora_inicio_troca": hora_inicio,
            "hora_fim_troca": hora_fim,
            "mt_inicial": valor_campo(troca, "mt_inicial"),
            "mt_final": valor_campo(troca, "mt_final"),
            "mt_ini_num": mt_ini_num,
            "mt_fim_num": mt_fim_num,
            "tamanho_trilho_m": valor_campo(troca, "tamanho_trilho_m"),
            "medida_folga_mm": valor_campo(troca, "medida_folga_mm"),
            "solda_fechamento": valor_display(troca, "solda_fechamento") or valor_campo(troca, "solda_fechamento"),
            "trilho_transicao": valor_display(troca, "trilho_transicao") or valor_campo(troca, "trilho_transicao"),
            "temperatura_antes_solda_c": valor_campo(troca, "temperatura_antes_solda_c"),
            "temperatura_depois_solda_c": valor_campo(troca, "temperatura_depois_solda_c"),
            "tempo_aquecimento_seg": valor_campo(troca, "tempo_aquecimento_seg"),
            "tempo_vazao_seg": valor_campo(troca, "tempo_vazao_seg"),
            "perfil_trilho": valor_display(troca, "perfil_trilho") or valor_campo(troca, "perfil_trilho"),
            "classe_trilho": valor_display(troca, "classe_trilho") or valor_campo(troca, "classe_trilho"),
            "tipo_solda": valor_display(troca, "tipo_solda") or valor_campo(troca, "tipo_solda"),
            "motivo_troca": valor_campo(troca, "motivo_troca"),
            "os_numero": valor_campo(troca, "os_numero"),
            "responsavel": valor_campo(troca, "responsavel"),
            "observacoes": valor_campo(troca, "observacoes"),
            "imagem_url": imagem_url,
        })

    mt_min = MT_TRECHO_INICIAL
    mt_max = MT_TRECHO_FINAL

    total_segmentos = ((mt_max - mt_min) // PASSO_MT) + 1
    if total_segmentos <= 0:
        total_segmentos = 1

    via_1_a = []
    via_1_b = []
    via_2_c = []
    via_2_d = []

    for item in registros_processados:
        inicio_segmento = (item["mt_ini_num"] - mt_min) // PASSO_MT
        fim_segmento = (item["mt_fim_num"] - mt_min) // PASSO_MT

        inicio_segmento = max(0, inicio_segmento)
        fim_segmento = min(total_segmentos, fim_segmento)

        if fim_segmento < inicio_segmento:
            inicio_segmento, fim_segmento = fim_segmento, inicio_segmento

        quantidade_segmentos = max(1, fim_segmento - inicio_segmento)

        bloco = {
            **item,
            "inicio_segmento": int(inicio_segmento),
            "fim_segmento": int(fim_segmento),
            "quantidade_segmentos": int(quantidade_segmentos),
        }

        via = str(item.get("via", "")).strip()
        trilho = str(item.get("trilho_codigo", "")).strip().upper()

        if via == "1":
            if trilho == "A":
                via_1_a.append(bloco)
            elif trilho == "B":
                via_1_b.append(bloco)

        elif via == "2":
            if trilho == "C":
                via_2_c.append(bloco)
            elif trilho == "D":
                via_2_d.append(bloco)

    estacoes_via_1 = []
    estacoes_via_2 = []

    for estacao in ESTACOES_MAPA:
        mt_inicial = estacao.get("mt_inicial")
        mt_final = estacao.get("mt_final")
        via = estacao.get("via")

        if mt_inicial is None or mt_final is None:
            continue

        if mt_final < mt_inicial:
            mt_inicial, mt_final = mt_final, mt_inicial

        if mt_final < mt_min or mt_inicial > mt_max:
            continue

        item_estacao = {
            "sigla": estacao["sigla"],
            "nome": estacao["nome"],
            "via": via,
            "mt_inicial": mt_inicial,
            "mt_final": mt_final,
        }

        if via == "1":
            estacoes_via_1.append(item_estacao)
        elif via == "2":
            estacoes_via_2.append(item_estacao)

    estacoes_via_1.sort(key=lambda x: x["mt_inicial"])
    estacoes_via_2.sort(key=lambda x: x["mt_inicial"])

    context = {
        "via_1_a_json": via_1_a,
        "via_1_b_json": via_1_b,
        "via_2_c_json": via_2_c,
        "via_2_d_json": via_2_d,
        "estacoes_via_1_json": estacoes_via_1,
        "estacoes_via_2_json": estacoes_via_2,
        "mt_min": mt_min,
        "mt_max": mt_max,
        "passo_mt": PASSO_MT,
        "total_segmentos": total_segmentos,
        "tem_dados": bool(registros_processados),
    }

    return render(request, "desgaste/trocas_trilho/mapa_trocas.html", context)

@never_cache
def api_itens_inspecao(request):
    itens = (
        ItemInspecao.objects
        .filter(ativo=True)
        .order_by("nome")
        .values("id", "nome")
    )

    return JsonResponse({
        "itens": list(itens)
    })

def listar_lubrificadores(request):
    filtro_via = request.GET.get("via", "").strip()
    filtro_status = request.GET.get("status", "").strip()

    ultimo_registro = (
        RegistroLubrificador.objects
        .filter(lubrificador_id=OuterRef("pk"))
        .order_by("-data_hora", "-criado_em")
    )

    pendencia_aberta = (
        RegistroLubrificador.objects
        .filter(
            lubrificador_id=OuterRef("pk"),
            tipo_atuacao=TipoAtuacaoLubrificadorChoices.INSPECAO,
            resultado_inspecao=ResultadoInspecaoChoices.COM_ANOMALIA,
            situacao_pendencia__in=[
                SituacaoPendenciaChoices.AGUARDANDO_CORRETIVA,
                SituacaoPendenciaChoices.EM_TRATAMENTO,
            ],
        )
        .order_by("-data_hora", "-criado_em")
    )

    lubrificadores = (
        Lubrificador.objects
        .annotate(
            ultimo_registro_id=Subquery(
                ultimo_registro.values("pk")[:1]
            ),
            pendencia_aberta_id=Subquery(
                pendencia_aberta.values("pk")[:1]
            ),
        )
        .order_by("nome")
    )

    if filtro_via:
        lubrificadores = lubrificadores.filter(
            via=filtro_via
        )

    if filtro_status:
        lubrificadores = lubrificadores.filter(
            status_operacional=filtro_status
        )

    lubrificadores = list(lubrificadores)

    ids_registros = set()

    for lubrificador in lubrificadores:
        if lubrificador.ultimo_registro_id:
            ids_registros.add(
                lubrificador.ultimo_registro_id
            )

        if lubrificador.pendencia_aberta_id:
            ids_registros.add(
                lubrificador.pendencia_aberta_id
            )

    registros_por_id = (
        RegistroLubrificador.objects
        .filter(pk__in=ids_registros)
        .select_related(
            "registrado_por",
            "inspecao_origem",
        )
        .in_bulk()
    )

    for lubrificador in lubrificadores:
        lubrificador.ultimo_registro = registros_por_id.get(
            lubrificador.ultimo_registro_id
        )

        lubrificador.pendencia_aberta = registros_por_id.get(
            lubrificador.pendencia_aberta_id
        )

    return render(
        request,
        "desgaste/lubrificadores/listar_lubrificadores.html",
        {
            "lubrificadores": lubrificadores,
            "filtro_via": filtro_via,
            "filtro_status": filtro_status,
            "status_choices": StatusLubrificadorChoices.choices,
        },
    )


def registrar_inspecao_lubrificador(request, pk):
    lubrificador = get_object_or_404(
        Lubrificador,
        pk=pk,
    )

    instancia = RegistroLubrificador(
        lubrificador=lubrificador,
        tipo_atuacao=TipoAtuacaoLubrificadorChoices.INSPECAO,
        situacao_pendencia=SituacaoPendenciaChoices.SEM_PENDENCIA,
    )

    if request.method == "POST":
        form = InspecaoLubrificadorForm(
            request.POST,
            instance=instancia,
        )

        if form.is_valid():
            with transaction.atomic():
                registro = form.save(commit=False)

                registro.tipo_atuacao = (
                    TipoAtuacaoLubrificadorChoices.INSPECAO
                )

                if (
                    registro.resultado_inspecao
                    == ResultadoInspecaoChoices.COM_ANOMALIA
                ):
                    registro.situacao_pendencia = (
                        SituacaoPendenciaChoices.AGUARDANDO_CORRETIVA
                    )
                else:
                    registro.situacao_pendencia = (
                        SituacaoPendenciaChoices.SEM_PENDENCIA
                    )

                if request.user.is_authenticated:
                    registro.registrado_por = request.user

                registro.save()

                lubrificador.status_operacional = (
                    registro.status_operacional
                )
                lubrificador.save(
                    update_fields=["status_operacional"]
                )

            if (
                registro.resultado_inspecao
                == ResultadoInspecaoChoices.COM_ANOMALIA
            ):
                messages.warning(
                    request,
                    (
                        f"Inspeção do {lubrificador.nome} registrada "
                        "com pendência aguardando corretiva."
                    ),
                )
            else:
                messages.success(
                    request,
                    (
                        f"Inspeção do {lubrificador.nome} registrada "
                        "sem pendências."
                    ),
                )

            return redirect("listar_lubrificadores")
    else:
        form = InspecaoLubrificadorForm(
            instance=instancia,
            initial={
                "status_operacional": (
                    lubrificador.status_operacional
                ),
            },
        )

    return render(
        request,
        (
            "desgaste/lubrificadores/"
            "form_registro_lubrificador.html"
        ),
        {
            "form": form,
            "lubrificador": lubrificador,
            "titulo": f"Nova inspeção — {lubrificador.nome}",
            "tipo_formulario": "inspecao",
        },
    )


def registrar_corretiva_lubrificador(
    request,
    pk,
    inspecao_pk,
):
    lubrificador = get_object_or_404(
        Lubrificador,
        pk=pk,
    )

    inspecao_origem = get_object_or_404(
        RegistroLubrificador,
        pk=inspecao_pk,
        lubrificador=lubrificador,
        tipo_atuacao=TipoAtuacaoLubrificadorChoices.INSPECAO,
        resultado_inspecao=ResultadoInspecaoChoices.COM_ANOMALIA,
    )

    falhas_inspecao = [
        falha.strip()
        for falha in (
            inspecao_origem.falha_encontrada or ""
        ).split(";")
        if falha.strip()
    ]

    quantidade_ordens = max(
        1,
        len(falhas_inspecao),
    )

    if not inspecao_origem.pendencia_aberta:
        messages.info(
            request,
            (
                "Esta inspeção não possui uma pendência "
                "corretiva aberta."
            ),
        )
        return redirect(
            "historico_lubrificador",
            pk=lubrificador.pk,
        )

    ultimo_registro = (
        lubrificador.registros
        .order_by("-data_hora", "-criado_em")
        .first()
    )

    instancia = RegistroLubrificador(
        lubrificador=lubrificador,
        tipo_atuacao=TipoAtuacaoLubrificadorChoices.CORRETIVA,
        inspecao_origem=inspecao_origem,
        situacao_pendencia=SituacaoPendenciaChoices.EM_TRATAMENTO,
    )

    valores_iniciais = {
        "status_operacional": (
            lubrificador.status_operacional
        ),
    }

    if ultimo_registro:
        valores_iniciais.update({
            "nivel_graxa_percentual": (
                ultimo_registro.nivel_graxa_percentual
            ),
            "alimentacao_eletrica": (
                ultimo_registro.alimentacao_eletrica
            ),
            "tensao_alimentacao": (
                ultimo_registro.tensao_alimentacao
            ),
            "controladora": ultimo_registro.controladora,
            "motor": ultimo_registro.motor,
            "integridade_regua": (
                ultimo_registro.integridade_regua
            ),
            "quantidade_total_bicos": (
                ultimo_registro.quantidade_total_bicos
            ),
            "quantidade_bicos_funcionais": (
                ultimo_registro.quantidade_bicos_funcionais
            ),
            "sensor_inducao": (
                ultimo_registro.sensor_inducao
            ),
        })

    if request.method == "POST":
        form = CorretivaLubrificadorForm(
            request.POST,
            instance=instancia,
        )

        ordens_formset = OrdemCorretivaLubrificadorFormSet(
            request.POST,
            instance=instancia,
            prefix="ordens",
            quantidade_minima=quantidade_ordens,
        )

        if form.is_valid() and ordens_formset.is_valid():
            with transaction.atomic():
                registro = form.save(commit=False)

                registro.tipo_atuacao = (
                    TipoAtuacaoLubrificadorChoices.CORRETIVA
                )
                registro.inspecao_origem = inspecao_origem
                registro.falha_encontrada = (
                    inspecao_origem.falha_encontrada
                )

                if request.user.is_authenticated:
                    registro.registrado_por = request.user

                if (
                    registro.resultado_corretiva
                    == ResultadoCorretivaChoices.RESOLVIDA
                ):
                    registro.situacao_pendencia = (
                        SituacaoPendenciaChoices.CONCLUIDA
                    )
                    inspecao_origem.situacao_pendencia = (
                        SituacaoPendenciaChoices.CONCLUIDA
                    )
                else:
                    registro.situacao_pendencia = (
                        SituacaoPendenciaChoices.EM_TRATAMENTO
                    )
                    inspecao_origem.situacao_pendencia = (
                        SituacaoPendenciaChoices.EM_TRATAMENTO
                    )

                registro.save()

                ordens_formset.instance = registro
                ordens_formset.save()

                inspecao_origem.save(
                    update_fields=["situacao_pendencia"]
                )

                lubrificador.status_operacional = (
                    registro.status_operacional
                )
                lubrificador.save(
                    update_fields=["status_operacional"]
                )

            if (
                registro.resultado_corretiva
                == ResultadoCorretivaChoices.RESOLVIDA
            ):
                messages.success(
                    request,
                    (
                        f"Corretiva do {lubrificador.nome} "
                        "registrada e pendência concluída."
                    ),
                )
            else:
                messages.warning(
                    request,
                    (
                        f"Corretiva do {lubrificador.nome} registrada. "
                        "A pendência permanece em tratamento."
                    ),
                )

            return redirect("listar_lubrificadores")
    else:
        form = CorretivaLubrificadorForm(
            instance=instancia,
            initial=valores_iniciais,
        )

        ordens_formset = OrdemCorretivaLubrificadorFormSet(
            instance=instancia,
            prefix="ordens",
            quantidade_minima=quantidade_ordens,
        )

    return render(
        request,
        (
            "desgaste/lubrificadores/"
            "form_corretiva_lubrificador.html"
        ),
        {
            "form": form,
            "ordens_formset": ordens_formset,
            "falhas_inspecao": falhas_inspecao,
            "quantidade_ordens": quantidade_ordens,
            "lubrificador": lubrificador,
            "inspecao_origem": inspecao_origem,
            "titulo": (
                f"Registrar corretiva — "
                f"{lubrificador.nome}"
            ),
        },
    )


def registrar_atualizacao_lubrificador(request, pk):
    """Compatibilidade com links antigos do módulo."""
    return registrar_inspecao_lubrificador(request, pk)


def historico_lubrificador(request, pk):
    lubrificador = get_object_or_404(
        Lubrificador,
        pk=pk,
    )

    registros = (
        lubrificador.registros
        .select_related(
            "registrado_por",
            "inspecao_origem",
        )
        .prefetch_related("ordens_corretivas")
        .order_by("-data_hora", "-criado_em")
    )

    return render(
        request,
        "desgaste/lubrificadores/historico_lubrificador.html",
        {
            "lubrificador": lubrificador,
            "registros": registros,
        },
    )


def novo_lubrificador(request):
    if not request.user.is_staff:
        messages.error(
            request,
            (
                "A criação de lubrificadores é restrita "
                "aos administradores."
            ),
        )
        return redirect("listar_lubrificadores")

    if request.method == "POST":
        form = LubrificadorCadastroForm(request.POST)

        if form.is_valid():
            lubrificador = form.save()

            messages.success(
                request,
                f"{lubrificador.nome} cadastrado com sucesso.",
            )
            return redirect("listar_lubrificadores")
    else:
        form = LubrificadorCadastroForm()

    return render(
        request,
        "desgaste/lubrificadores/form_lubrificador.html",
        {
            "form": form,
            "titulo": "Novo lubrificador",
        },
    )


def editar_lubrificador(request, pk):
    if not request.user.is_staff:
        messages.error(
            request,
            (
                "A edição cadastral é restrita "
                "aos administradores."
            ),
        )
        return redirect("listar_lubrificadores")

    lubrificador = get_object_or_404(
        Lubrificador,
        pk=pk,
    )

    if request.method == "POST":
        form = LubrificadorCadastroForm(
            request.POST,
            instance=lubrificador,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                f"Cadastro do {lubrificador.nome} atualizado.",
            )
            return redirect("listar_lubrificadores")
    else:
        form = LubrificadorCadastroForm(
            instance=lubrificador,
        )

    return render(
        request,
        "desgaste/lubrificadores/form_lubrificador.html",
        {
            "form": form,
            "lubrificador": lubrificador,
            "titulo": (
                f"Editar cadastro — {lubrificador.nome}"
            ),
        },
    )
