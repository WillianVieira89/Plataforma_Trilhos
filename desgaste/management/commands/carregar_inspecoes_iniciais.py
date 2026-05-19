from django.core.management.base import BaseCommand

from ...models import ItemInspecao, SetorInspecao, TipoSetor


SETORES = [
    {"codigo": "T1", "nome": "CPR - X45", "tipo": TipoSetor.TRECHO, "ordem": 1, "limite_inicial": "CPR", "limite_final": "X45"},
    {"codigo": "T2", "nome": "X45 - ABV", "tipo": TipoSetor.TRECHO, "ordem": 2, "limite_inicial": "X45", "limite_final": "ABV"},
    {"codigo": "T3", "nome": "ABV - ECT", "tipo": TipoSetor.TRECHO, "ordem": 3, "limite_inicial": "ABV", "limite_final": "ECT"},
    {"codigo": "T4", "nome": "ECT - VDC", "tipo": TipoSetor.TRECHO, "ordem": 4, "limite_inicial": "ECT", "limite_final": "VDC"},
    {"codigo": "PCR", "nome": "Pátio Capão Redondo", "tipo": TipoSetor.PATIO, "ordem": 5, "limite_inicial": "PCR", "limite_final": "PCR"},
    {"codigo": "PGC", "nome": "Pátio Guido Caloi", "tipo": TipoSetor.PATIO, "ordem": 6, "limite_inicial": "PGC", "limite_final": "PGC"},
]

ITENS = [
    "AGUA NO NICHO",
    "ALMOFADA DANIFICADA",
    "ARRUELA DE PRESSÃO DANIFICADA",
    "ARRUELA FORA DE POSIÇÃO",
    "ARRUELA INVERTIDA/DIFERENTE",
    "ARRUELA SERRILHADA DANIFICADA",
    "BUCH CHUMB DANIF",
    "CALÇO QUEBRADO",
    "CLIPS INVERTIDO",
    "CLIPS QUEBRADO",
    "DESGASTE LATERAL",
    "DESGASTE ONDULATÓRIO",
    "DESTACAMENTO DE MATERIAL",
    "DESTACAMENTO JACARÉ",
    "ESCOAMENTO DE MATERIAL",
    "FALSO TORQUE",
    "FALTA DE CALÇO",
    "FUGA DE CORRENTE",
    "INFILTRAÇÃO",
    "ISOLADOR QUEBRADO",
    "JIC DANIFICADA",
    "LIXO NA VIA/PLATAFORMA",
    "NICHO ALAGADO",
    "NIVELAMENTO",
    "PARAFUSO QUEBRADO",
    "PARAFUSO QUEBRADO M16",
    "PARAFUSO SOLTO/FALSO TORQUE",
    "PLACA DANIFICADA",
    "PLACA INVERTIDA",
    "PLACA VIPA COMPLETA",
    "PRISIONEIRO QUEBRADO",
    "RUPTURA DE TRILHO",
    "SACAR CHUMBADOR",
    "SEM ARRUELA",
    "SEM ARRUELA 3MM",
    "SEM ARRUELA DE BORRACHA",
    "SEM BUCHA PU",
    "SEM ESCADA DE ACESSO",
    "SEM MT",
    "SEM PARAFUSO",
    "SEM PORCA",
    "SOLDA ABAULADA/DEST MAT",
    "TAMPA DO BALDINHO",
    "TRILHO SOLTO NA VIA",
    "TRINCA NO TRILHO",
    "PLACA DESMONTADA",
]


class Command(BaseCommand):
    help = "Carrega os setores e os itens iniciais de inspeção"

    def handle(self, *args, **options):
        for setor in SETORES:
            SetorInspecao.objects.update_or_create(
                codigo=setor["codigo"],
                defaults=setor
            )

        for nome in ITENS:
            ItemInspecao.objects.update_or_create(
                nome=nome,
                defaults={"ativo": True}
            )

        self.stdout.write(self.style.SUCCESS("Carga inicial concluída com sucesso."))