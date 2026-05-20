import re
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from .forms import RegistroInspecaoForm, InspecaoForm, OcorrenciaInspecaoFormSet, TrocaTrilhoForm
from .models import (
    Inspecao,
    InspecaoTrecho,
    MedicaoDesgaste,
    Trilho,
    PontoOperacional,
    TrocaTrilho,
)

# ajuste estes valores para o trecho real depois
MT_TRECHO_INICIAL = 1
MT_TRECHO_FINAL = 10099
PASSO_MT = 2

ESTACOES_MAPA = [
    {"sigla": "CPR", "nome": "Capão Redondo", "via": "1", "mt_inicial": 295, "mt_final": 363},
    {"sigla": "CPR", "nome": "Capão Redondo", "via": "2", "mt_inicial": 270, "mt_final": 338},

    {"sigla": "CPL", "nome": "Campo Limpo", "via": "1", "mt_inicial": 1295, "mt_final": 1363},
    {"sigla": "CPL", "nome": "Campo Limpo", "via": "2", "mt_inicial": 1270, "mt_final": 1338},

    {"sigla": "VBE", "nome": "Vila das Belezas", "via": "1", "mt_inicial": None, "mt_final": None},
    {"sigla": "VBE", "nome": "Vila das Belezas", "via": "2", "mt_inicial": None, "mt_final": None},

    {"sigla": "GGR", "nome": "Giovanni Gronchi", "via": "1", "mt_inicial": None, "mt_final": None},
    {"sigla": "GGR", "nome": "Giovanni Gronchi", "via": "2", "mt_inicial": None, "mt_final": None},

    {"sigla": "STA", "nome": "Santo Amaro", "via": "1", "mt_inicial": None, "mt_final": None},
    {"sigla": "STA", "nome": "Santo Amaro", "via": "2", "mt_inicial": None, "mt_final": None},

    {"sigla": "LTR", "nome": "Largo Treze", "via": "1", "mt_inicial": None, "mt_final": None},
    {"sigla": "LTR", "nome": "Largo Treze", "via": "2", "mt_inicial": None, "mt_final": None},

    {"sigla": "APN", "nome": "Adolfo Pinheiro", "via": "1", "mt_inicial": None, "mt_final": None},
    {"sigla": "APN", "nome": "Adolfo Pinheiro", "via": "2", "mt_inicial": None, "mt_final": None},

    {"sigla": "ABV", "nome": "Alto da Boa Vista", "via": "1", "mt_inicial": None, "mt_final": None},
    {"sigla": "ABV", "nome": "Alto da Boa Vista", "via": "2", "mt_inicial": None, "mt_final": None},

    {"sigla": "BGA", "nome": "Borba Gato", "via": "1", "mt_inicial": None, "mt_final": None},
    {"sigla": "BGA", "nome": "Borba Gato", "via": "2", "mt_inicial": None, "mt_final": None},

    {"sigla": "BRK", "nome": "Brooklin", "via": "1", "mt_inicial": None, "mt_final": None},
    {"sigla": "BRK", "nome": "Brooklin", "via": "2", "mt_inicial": None, "mt_final": None},

    {"sigla": "CPB", "nome": "Campo Belo", "via": "1", "mt_inicial": None, "mt_final": None},
    {"sigla": "CPB", "nome": "Campo Belo", "via": "2", "mt_inicial": None, "mt_final": None},

    {"sigla": "ECT", "nome": "Eucaliptos", "via": "1", "mt_inicial": None, "mt_final": None},
    {"sigla": "ECT", "nome": "Eucaliptos", "via": "2", "mt_inicial": None, "mt_final": None},

    {"sigla": "MOE", "nome": "Moema", "via": "1", "mt_inicial": None, "mt_final": None},
    {"sigla": "MOE", "nome": "Moema", "via": "2", "mt_inicial": None, "mt_final": None},

    {"sigla": "SER", "nome": "AACD Servidor", "via": "1", "mt_inicial": None, "mt_final": None},
    {"sigla": "SER", "nome": "AACD Servidor", "via": "2", "mt_inicial": None, "mt_final": None},

    {"sigla": "HSP", "nome": "Hospital São Paulo", "via": "1", "mt_inicial": None, "mt_final": None},
    {"sigla": "HSP", "nome": "Hospital São Paulo", "via": "2", "mt_inicial": None, "mt_final": None},

    {"sigla": "SCZ", "nome": "Santa Cruz", "via": "1", "mt_inicial": None, "mt_final": None},
    {"sigla": "SCZ", "nome": "Santa Cruz", "via": "2", "mt_inicial": None, "mt_final": None},

    {"sigla": "CKB", "nome": "Chácara Klabin", "via": "1", "mt_inicial": None, "mt_final": None},
    {"sigla": "CKB", "nome": "Chácara Klabin", "via": "2", "mt_inicial": None, "mt_final": None},
]

def registrar_inspecao(request):
    all_pontos = PontoOperacional.objects.select_related('estacao').all().order_by('ordem')
    all_trilhos = Trilho.objects.select_related('ponto_operacional').all().order_by(
        'ponto_operacional__ordem', 'via', 'lado_trilho'
    )

    if request.method == 'POST':
        form = RegistroInspecaoForm(request.POST)

        if form.is_valid():
            trilho = form.cleaned_data['trilho']

            inspecao = Inspecao.objects.create(
                trilho=trilho,
                data_inspecao=form.cleaned_data['data_inspecao'],
                hora_inspecao=form.cleaned_data['hora_inspecao'],
                inspetor=form.cleaned_data['inspetor'],
                tipo_inspecao=form.cleaned_data['tipo_inspecao'],
                observacoes=form.cleaned_data['observacoes'],
            )

            MedicaoDesgaste.objects.create(
                inspecao=inspecao,
                desgaste_vertical_mm=form.cleaned_data['desgaste_vertical_mm'],
                desgaste_lateral_mm=form.cleaned_data['desgaste_lateral_mm'],
                observacao_tecnica=form.cleaned_data['observacao_tecnica'],
                status_desgaste=form.cleaned_data['status_desgaste'],
            )

            messages.success(request, 'Inspeção e medição salvas com sucesso.')
            return redirect('registrar_inspecao')
    else:
        form = RegistroInspecaoForm()

    return render(request, 'desgaste/registrar_inspecao.html', {
        'form': form,
        'all_pontos': all_pontos,
        'all_trilhos': all_trilhos,
    })

def historico_inspecoes(request):
    pontos = PontoOperacional.objects.select_related('estacao').all().order_by('ordem')
    trilhos = Trilho.objects.select_related('ponto_operacional').all().order_by(
        'ponto_operacional__ordem', 'via', 'lado_trilho'
    )

    ponto_id = request.GET.get('ponto_operacional')
    via = request.GET.get('via')
    trilho_id = request.GET.get('trilho')

    inspecoes = Inspecao.objects.select_related(
        'trilho__ponto_operacional'
    ).all().order_by('-data_inspecao', '-hora_inspecao')

    if ponto_id:
        inspecoes = inspecoes.filter(trilho__ponto_operacional_id=ponto_id)

    if via:
        inspecoes = inspecoes.filter(trilho__via=via)

    if trilho_id:
        inspecoes = inspecoes.filter(trilho_id=trilho_id)

    registros = []
    for inspecao in inspecoes:
        medicao = getattr(inspecao, 'medicao', None)
        registros.append({
            'inspecao': inspecao,
            'medicao': medicao,
        })

    return render(request, 'desgaste/historico_inspecoes.html', {
        'registros': registros,
        'pontos': pontos,
        'trilhos': trilhos,
        'filtro_ponto': ponto_id or '',
        'filtro_via': via or '',
        'filtro_trilho': trilho_id or '',
    })

def listar_inspecoes(request):
    inspecoes = (
        InspecaoTrecho.objects
        .select_related("setor")
        .prefetch_related("ocorrencias__item")
        .order_by("-data_inspecao", "-hora_inspecao")
    )

    setor_id = request.GET.get("setor")
    data_ini = request.GET.get("data_ini")
    data_fim = request.GET.get("data_fim")

    if setor_id:
        inspecoes = inspecoes.filter(setor_id=setor_id)

    if data_ini:
        inspecoes = inspecoes.filter(data_inspecao__gte=data_ini)

    if data_fim:
        inspecoes = inspecoes.filter(data_inspecao__lte=data_fim)

    context = {
        "inspecoes": inspecoes,
    }
    return render(request, "desgaste/inspecoes/listar_inspecoes.html", context)

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

    context = {
        "form": form,
        "formset": formset,
        "titulo": "Nova Inspeção",
    }
    return render(request, "inspecoes/form_inspecao.html", context)

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

    context = {
        "form": form,
        "formset": formset,
        "titulo": "Editar Inspeção",
    }
    return render(request, "inspecoes/form_inspecao.html", context)

# Views para Troca de Trilho

def listar_trocas_trilho(request):
    trocas = TrocaTrilho.objects.all().order_by('-data_troca', '-hora_troca')

    via = request.GET.get('via')
    trilho = request.GET.get('trilho')
    data_ini = request.GET.get('data_ini')
    data_fim = request.GET.get('data_fim')

    if via:
        trocas = trocas.filter(via=via)

    if trilho:
        trocas = trocas.filter(trilho=trilho)

    if data_ini:
        trocas = trocas.filter(data_troca__gte=data_ini)

    if data_fim:
        trocas = trocas.filter(data_troca__lte=data_fim)

    return render(request, 'desgaste/trocas_trilho/listar_trocas.html', {
        'trocas': trocas,
        'filtro_via': via or '',
        'filtro_trilho': trilho or '',
        'filtro_data_ini': data_ini or '',
        'filtro_data_fim': data_fim or '',
    })

def nova_troca_trilho(request):
    if request.method == 'POST':
        form = TrocaTrilhoForm(request.POST, request.FILES, instance=TrocaTrilho())
        if form.is_valid():
            form.save()
            messages.success(request, 'Troca de trilho cadastrada com sucesso.')
            return redirect('mapa_trocas_trilho')
    else:
        form = TrocaTrilhoForm(instance=TrocaTrilho())

    return render(request, 'desgaste/trocas_trilho/form_troca.html', {
        'form': form,
        'titulo': 'Nova Troca de Trilho',
    })

def editar_troca_trilho(request, pk):
    troca = get_object_or_404(TrocaTrilho, pk=pk)

    if request.method == 'POST':
        form = TrocaTrilhoForm(request.POST, instance=troca)
        if form.is_valid():
            form.save()
            messages.success(request, 'Troca de trilho atualizada com sucesso.')
            return redirect('mapa_trocas_trilho')
    else:
        form = TrocaTrilhoForm(instance=troca)

    return render(request, 'desgaste/trocas_trilho/form_troca.html', {
        'form': form,
        'titulo': 'Editar Troca de Trilho',
    })

def tela_inicial(request):
    return render(request, "desgaste/tela_inicial.html")


    trocas = TrocaTrilho.objects.all().order_by('via', 'mt_inicial', 'data_troca')

    registros_processados = []

    for troca in trocas:
        mt_ini_num = extrair_numero_mt(troca.mt_inicial)
        mt_fim_num = extrair_numero_mt(troca.mt_final)

        if mt_ini_num is None or mt_fim_num is None:
            continue

        if mt_fim_num < mt_ini_num:
            mt_ini_num, mt_fim_num = mt_fim_num, mt_ini_num
                   
        hora_inicio = getattr(troca, 'hora_inicio_troca', None) or getattr(troca, 'hora_troca', None)
        hora_fim = getattr(troca, 'hora_fim_troca', None) or getattr(troca, 'hora_troca', None)

        registros_processados.append({
            'id': troca.id,
            'via': troca.via,
            'trilho': troca.get_trilho_display(),
            'data_troca': troca.data_troca,
            'hora_inicio_troca': hora_inicio,
            'hora_fim_troca': hora_fim,
            'mt_inicial': troca.mt_inicial,
            'mt_final': troca.mt_final,
            'mt_ini_num': mt_ini_num,
            'mt_fim_num': mt_fim_num,
            'tamanho_trilho_m': troca.tamanho_trilho_m,
            'medida_folga_mm': troca.medida_folga_mm,
            'solda_fechamento': troca.get_solda_fechamento_display() if troca.solda_fechamento else '',
            'trilho_transicao': troca.get_trilho_transicao_display() if troca.trilho_transicao else '',
            'temperatura_antes_solda_c': troca.temperatura_antes_solda_c,
            'temperatura_depois_solda_c': troca.temperatura_depois_solda_c,
            'tempo_aquecimento_seg': troca.tempo_aquecimento_seg,
            'tempo_vazao_seg': troca.tempo_vazao_seg,
            'perfil_trilho': troca.get_perfil_trilho_display() if troca.perfil_trilho else '',
            'classe_trilho': troca.get_classe_trilho_display() if troca.classe_trilho else '',
            'tipo_solda': troca.get_tipo_solda_display() if troca.tipo_solda else '',
            'motivo_troca': troca.motivo_troca,
            'os_numero': troca.os_numero,
            'responsavel': troca.responsavel,
            'observacoes': troca.observacoes,
            'imagem_url': troca.imagem.url if troca.imagem else '',
        })

    passo_mt = 2  # cada segmento representa 2 metros

    if registros_processados:
        mt_min_real = min(item['mt_ini_num'] for item in registros_processados)
        mt_max_real = max(item['mt_fim_num'] for item in registros_processados)
    else:
        mt_min_real = 0
        mt_max_real = 100

    # ajusta o intervalo para múltiplos de 2
    mt_min = (mt_min_real // passo_mt) * passo_mt
    mt_max = ((mt_max_real + passo_mt - 1) // passo_mt) * passo_mt

    total_segmentos = (mt_max - mt_min) // passo_mt
    if total_segmentos <= 0:
        total_segmentos = 1

    via_1 = []
    via_2 = []

    for item in registros_processados:
        inicio_segmento = (item['mt_ini_num'] - mt_min) // passo_mt
        fim_segmento = (item['mt_fim_num'] - mt_min) // passo_mt

        if fim_segmento < inicio_segmento:
            inicio_segmento, fim_segmento = fim_segmento, inicio_segmento

        quantidade_segmentos = max(1, fim_segmento - inicio_segmento)

        left = (inicio_segmento / total_segmentos) * 100
        width = (quantidade_segmentos / total_segmentos) * 100

        bloco = {
            **item,
            'left': round(max(left, 0), 4),
            'width': round(max(width, 0.8), 4),
            'inicio_segmento': int(inicio_segmento),
            'fim_segmento': int(fim_segmento),
            'quantidade_segmentos': int(quantidade_segmentos),
        }

        if item['via'] == '1':
            via_1.append(bloco)
        elif item['via'] == '2':
            via_2.append(bloco)

    context = {
        'via_1_json': json.dumps(via_1, cls=DjangoJSONEncoder),
        'via_2_json': json.dumps(via_2, cls=DjangoJSONEncoder),
        'mt_min': mt_min,
        'mt_max': mt_max,
        'passo_mt': passo_mt,
        'total_segmentos': total_segmentos,
        'tem_dados': bool(registros_processados),
    }
    return render(request, 'desgaste/trocas_trilho/mapa_trocas.html', context)

def extrair_numero_mt(valor):
    if valor is None:
        return None

    texto = str(valor).strip()
    numeros = re.findall(r'\d+', texto)

    if not numeros:
        return None

    return int(''.join(numeros))

def valor_campo(obj, nome_campo, default=''):
    return getattr(obj, nome_campo, default)

def valor_display(obj, nome_campo):
    metodo = getattr(obj, f'get_{nome_campo}_display', None)
    if callable(metodo):
        try:
            return metodo()
        except Exception:
            return ''
    return ''

def mapa_trocas_trilho(request):
    trocas = TrocaTrilho.objects.all().order_by('via', 'mt_inicial', 'data_troca')

    registros_processados = []

    for troca in trocas:
        mt_ini_num = extrair_numero_mt(valor_campo(troca, 'mt_inicial'))
        mt_fim_num = extrair_numero_mt(valor_campo(troca, 'mt_final'))

        if mt_ini_num is None or mt_fim_num is None:
            continue

        if mt_fim_num < mt_ini_num:
            mt_ini_num, mt_fim_num = mt_fim_num, mt_ini_num

        hora_inicio = valor_campo(troca, 'hora_inicio_troca', None) or valor_campo(troca, 'hora_troca', None)
        hora_fim = valor_campo(troca, 'hora_fim_troca', None) or valor_campo(troca, 'hora_troca', None)

        imagem = valor_campo(troca, 'imagem', None)
        imagem_url = ''
        try:
            if imagem:
                imagem_url = imagem.url
        except Exception:
            imagem_url = ''

        registros_processados.append({
            'id': troca.id,
            'via': valor_campo(troca, 'via'),
            'trilho': valor_display(troca, 'trilho') or valor_campo(troca, 'trilho'),
            'data_troca': valor_campo(troca, 'data_troca'),
            'hora_inicio_troca': hora_inicio,
            'hora_fim_troca': hora_fim,
            'mt_inicial': valor_campo(troca, 'mt_inicial'),
            'mt_final': valor_campo(troca, 'mt_final'),
            'mt_ini_num': mt_ini_num,
            'mt_fim_num': mt_fim_num,
            'tamanho_trilho_m': valor_campo(troca, 'tamanho_trilho_m'),
            'medida_folga_mm': valor_campo(troca, 'medida_folga_mm'),
            'solda_fechamento': valor_display(troca, 'solda_fechamento') or valor_campo(troca, 'solda_fechamento'),
            'trilho_transicao': valor_display(troca, 'trilho_transicao') or valor_campo(troca, 'trilho_transicao'),
            'temperatura_antes_solda_c': valor_campo(troca, 'temperatura_antes_solda_c'),
            'temperatura_depois_solda_c': valor_campo(troca, 'temperatura_depois_solda_c'),
            'tempo_aquecimento_seg': valor_campo(troca, 'tempo_aquecimento_seg'),
            'tempo_vazao_seg': valor_campo(troca, 'tempo_vazao_seg'),
            'perfil_trilho': valor_display(troca, 'perfil_trilho') or valor_campo(troca, 'perfil_trilho'),
            'classe_trilho': valor_display(troca, 'classe_trilho') or valor_campo(troca, 'classe_trilho'),
            'tipo_solda': valor_display(troca, 'tipo_solda') or valor_campo(troca, 'tipo_solda'),
            'motivo_troca': valor_campo(troca, 'motivo_troca'),
            'os_numero': valor_campo(troca, 'os_numero'),
            'responsavel': valor_campo(troca, 'responsavel'),
            'observacoes': valor_campo(troca, 'observacoes'),
            'imagem_url': imagem_url,
        })

    mt_min = MT_TRECHO_INICIAL
    mt_max = MT_TRECHO_FINAL

    total_segmentos = ((mt_max - mt_min) // PASSO_MT) + 1
    if total_segmentos <= 0:
        total_segmentos = 1

    via_1 = []
    via_2 = []

    for item in registros_processados:
        inicio_segmento = (item['mt_ini_num'] - mt_min) // PASSO_MT
        fim_segmento = (item['mt_fim_num'] - mt_min) // PASSO_MT

        inicio_segmento = max(0, inicio_segmento)
        fim_segmento = min(total_segmentos, fim_segmento)

        if fim_segmento < inicio_segmento:
            inicio_segmento, fim_segmento = fim_segmento, inicio_segmento

        quantidade_segmentos = max(1, fim_segmento - inicio_segmento)

        left = (inicio_segmento / total_segmentos) * 100
        width = (quantidade_segmentos / total_segmentos) * 100

        bloco = {
            **item,
            'left': round(max(left, 0), 6),
            'width': round(max(width, 0.15), 6),
            'inicio_segmento': int(inicio_segmento),
            'fim_segmento': int(fim_segmento),
            'quantidade_segmentos': int(quantidade_segmentos),
        }

        if item['via'] == '1':
            via_1.append(bloco)
        elif item['via'] == '2':
            via_2.append(bloco)

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

        mt_inicial_aj = max(mt_inicial, mt_min)
        mt_final_aj = min(mt_final, mt_max)

        left = ((mt_inicial_aj - mt_min) / (mt_max - mt_min)) * 100 if mt_max > mt_min else 0
        width = ((mt_final_aj - mt_inicial_aj) / (mt_max - mt_min)) * 100 if mt_max > mt_min else 0
        mt_centro = (mt_inicial_aj + mt_final_aj) / 2
        left_centro = ((mt_centro - mt_min) / (mt_max - mt_min)) * 100 if mt_max > mt_min else 0

        item_estacao = {
            "sigla": estacao["sigla"],
            "nome": estacao["nome"],
            "via": via,
            "mt_inicial": mt_inicial,
            "mt_final": mt_final,
            "left": round(left, 6),
            "width": round(max(width, 1.2), 6),
            "left_centro": round(left_centro, 6),
        }

        if via == "1":
            estacoes_via_1.append(item_estacao)
        elif via == "2":
            estacoes_via_2.append(item_estacao)

    context = {
        'via_1_json': via_1,
        'via_2_json': via_2,
        'estacoes_via_1_json': estacoes_via_1,
        'estacoes_via_2_json': estacoes_via_2,
        'mt_min': mt_min,
        'mt_max': mt_max,
        'passo_mt': PASSO_MT,
        'total_segmentos': total_segmentos,
        'tem_dados': bool(registros_processados),
    }

    return render(request, 'desgaste/trocas_trilho/mapa_trocas.html', context)