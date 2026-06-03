from django.urls import path
from . import views

urlpatterns = [
    path("", views.tela_inicial, name="tela_inicial"),

    path("registro-desgaste/", views.registrar_inspecao, name="registrar_inspecao"),
    path("historico/", views.historico_inspecoes, name="historico_inspecoes"),

    path("inspecoes/", views.listar_inspecoes, name="listar_inspecoes"),
    path("inspecoes/nova/", views.nova_inspecao, name="nova_inspecao"),
    path("inspecoes/<int:pk>/editar/", views.editar_inspecao, name="editar_inspecao"),

    path(
        "inspecoes/ocorrencias/<int:pk>/editar/",
        views.editar_ocorrencia_inspecao,
        name="editar_ocorrencia_inspecao",
    ),
    path(
        "inspecoes/ocorrencias/<int:pk>/excluir/",
        views.excluir_ocorrencia_inspecao,
        name="excluir_ocorrencia_inspecao",
    ),

    path("trocas-trilho/", views.mapa_trocas_trilho, name="mapa_trocas_trilho"),
    path("trocas-trilho/mapa/", views.mapa_trocas_trilho, name="mapa_trocas_trilho"),
    path("trocas-trilho/nova/", views.nova_troca_trilho, name="nova_troca_trilho"),
    path("trocas-trilho/<int:pk>/editar/", views.editar_troca_trilho, name="editar_troca_trilho"),
]