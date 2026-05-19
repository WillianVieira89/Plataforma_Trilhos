from django.contrib import admin
from .models import (
    Linha, 
    Estacao, 
    PontoOperacional, 
    Trilho, 
    Inspecao,
    MedicaoDesgaste,
    FaixaLocalizacao,
    ReferenciaLinearPKMT,
    InspecaoTrecho,
    ItemInspecao,
    SetorInspecao,
    OcorrenciaInspecaoTrecho,
    TrocaTrilho,
)


@admin.register(Linha)
class LinhaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome')
    search_fields = ('nome',)


@admin.register(Estacao)
class EstacaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'sigla', 'linha')
    search_fields = ('nome', 'sigla')
    list_filter = ('linha',)


@admin.register(PontoOperacional)
class PontoOperacionalAdmin(admin.ModelAdmin):
    list_display = ('id', 'codigo', 'descricao', 'tipo_ponto', 'ordem', 'posicao', 'possui_acesso_patio')
    search_fields = ('codigo', 'descricao')
    list_filter = ('tipo_ponto', 'posicao', 'possui_acesso_patio', 'estacao')
    
@admin.register(Trilho)
class TrilhoAdmin(admin.ModelAdmin):
    list_display = ('id', 'ponto_operacional', 'via', 'lado_trilho', 'ponto_kilometrico', 'marco_topografico', 'tipo_trilho')
    search_fields = ('ponto_operacional__codigo', 'ponto_operacional__descricao', 'ponto_kilometrico', 'marco_topografico', 'tipo_trilho')
    list_filter = ('via', 'lado_trilho', 'ponto_operacional__tipo_ponto')
    
@admin.register(Inspecao)
class InspecaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'trilho', 'data_inspecao', 'hora_inspecao', 'inspetor', 'tipo_inspecao')
    search_fields = ('trilho__ponto_operacional__codigo', 'inspetor', 'observacoes')
    list_filter = ('tipo_inspecao', 'data_inspecao', 'trilho__via', 'trilho__lado_trilho')
    
@admin.register(MedicaoDesgaste)
class MedicaoDesgasteAdmin(admin.ModelAdmin):
    list_display = ('id', 'inspecao', 'desgaste_vertical_mm', 'desgaste_lateral_mm', 'status_desgaste')
    search_fields = ('inspecao__trilho__ponto_operacional__codigo', 'observacao_tecnica')
    list_filter = ('status_desgaste', 'inspecao__trilho__via', 'inspecao__trilho__lado_trilho')

@admin.register(FaixaLocalizacao)
class FaixaLocalizacaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'ponto_operacional', 'via', 'mt_inicial', 'ponto_kilometrico_inicial', 'mt_final', 'ponto_kilometrico_final')
    search_fields = ('ponto_operacional__codigo', 'mt_inicial', 'ponto_kilometrico_inicial', 'mt_final', 'ponto_kilometrico_final')
    list_filter = ('via', 'ponto_operacional__tipo_ponto')

@admin.register(ReferenciaLinearPKMT)
class ReferenciaLinearPKMTAdmin(admin.ModelAdmin):
    list_display = ('id', 'via', 'marco_topografico', 'ponto_kilometrico', 'local_excel')
    search_fields = ('marco_topografico', 'ponto_kilometrico', 'local_excel')
    list_filter = ('via', 'local_excel') 

class OcorrenciaInspecaoTrechoInline(admin.TabularInline):
    model = OcorrenciaInspecaoTrecho
    extra = 0


@admin.register(SetorInspecao)
class SetorInspecaoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "tipo", "ordem", "ativo")
    list_filter = ("tipo", "ativo")
    search_fields = ("codigo", "nome")


@admin.register(ItemInspecao)
class ItemInspecaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome",)


@admin.register(InspecaoTrecho)
class InspecaoTrechoAdmin(admin.ModelAdmin):
    list_display = ("id", "data_inspecao", "hora_inspecao", "setor", "via", "trilho", "responsavel")
    list_filter = ("setor", "via", "trilho", "data_inspecao")
    search_fields = ("responsavel", "estacao_referencia", "referencia_local")
    inlines = [OcorrenciaInspecaoTrechoInline]
    
@admin.register(TrocaTrilho)
class TrocaTrilhoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'data_troca',
        'hora_troca',
        'via',
        'trilho',
        'mt_inicial',
        'mt_final',
        'tamanho_trilho_m',
        'tipo_solda',
        'responsavel',
    )
    list_filter = ('data_troca', 'via', 'trilho', 'tipo_solda', 'perfil_trilho', 'classe_trilho')
    search_fields = ('mt_inicial', 'mt_final', 'responsavel', 'estacao_referencia', 'referencia_local', 'os_numero')