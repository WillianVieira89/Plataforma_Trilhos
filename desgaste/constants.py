# Fonte única de dados das estações da linha.
# Cada entrada tem: sigla (str), nome (str), vias (list de dicts com via, mt_inicial, mt_final).
# Os formatos consumidos por views.py e forms.py são derivados abaixo — não edite essas listas diretamente.
ESTACOES = [
    {"sigla": "CPR", "nome": "Capão Redondo",     "vias": [{"via": "1", "mt_inicial": 295,  "mt_final": 363},  {"via": "2", "mt_inicial": 270,  "mt_final": 338}]},
    {"sigla": "CPL", "nome": "Campo Limpo",        "vias": [{"via": "1", "mt_inicial": 907,  "mt_final": 975},  {"via": "2", "mt_inicial": 920,  "mt_final": 988}]},
    {"sigla": "VBE", "nome": "Vila das Belezas",   "vias": [{"via": "1", "mt_inicial": 1815, "mt_final": 1883}, {"via": "2", "mt_inicial": 1830, "mt_final": 1898}]},
    {"sigla": "GGR", "nome": "Giovanni Gronchi",   "vias": [{"via": "1", "mt_inicial": 2633, "mt_final": 2701}, {"via": "2", "mt_inicial": 2646, "mt_final": 2714}]},
    {"sigla": "STA", "nome": "Santo Amaro",        "vias": [{"via": "1", "mt_inicial": 3705, "mt_final": 3801}, {"via": "2", "mt_inicial": 3704, "mt_final": 3802}]},
    {"sigla": "LTR", "nome": "Largo Treze",        "vias": [{"via": "1", "mt_inicial": 4253, "mt_final": 4321}, {"via": "2", "mt_inicial": 4256, "mt_final": 4324}]},
    {"sigla": "APN", "nome": "Adolfo Pinheiro",    "vias": [{"via": "1", "mt_inicial": 4701, "mt_final": 4769}, {"via": "2", "mt_inicial": 4706, "mt_final": 4774}]},
    {"sigla": "ABV", "nome": "Alto da Boa Vista",  "vias": [{"via": "1", "mt_inicial": 5173, "mt_final": 5243}, {"via": "2", "mt_inicial": 5178, "mt_final": 5248}]},
    {"sigla": "BGA", "nome": "Borba Gato",         "vias": [{"via": "1", "mt_inicial": 5739, "mt_final": 5807}, {"via": "2", "mt_inicial": 5744, "mt_final": 5812}]},
    {"sigla": "BRK", "nome": "Brooklin",           "vias": [{"via": "1", "mt_inicial": 6179, "mt_final": 6247}, {"via": "2", "mt_inicial": 6184, "mt_final": 6252}]},
    {"sigla": "CPB", "nome": "Campo Belo",         "vias": [{"via": "1", "mt_inicial": 6733, "mt_final": 6801}, {"via": "2", "mt_inicial": 6740, "mt_final": 6808}]},
    {"sigla": "ECT", "nome": "Eucaliptos",         "vias": [{"via": "1", "mt_inicial": 7573, "mt_final": 7641}, {"via": "2", "mt_inicial": 7574, "mt_final": 7642}]},
    {"sigla": "MOE", "nome": "Moema",              "vias": [{"via": "1", "mt_inicial": 8061, "mt_final": 8129}, {"via": "2", "mt_inicial": 8062, "mt_final": 8130}]},
    {"sigla": "SER", "nome": "AACD Servidor",      "vias": [{"via": "1", "mt_inicial": 8669, "mt_final": 8739}, {"via": "2", "mt_inicial": 8668, "mt_final": 8738}]},
    {"sigla": "HSP", "nome": "Hospital São Paulo", "vias": [{"via": "1", "mt_inicial": 8997, "mt_final": 9067}, {"via": "2", "mt_inicial": 8998, "mt_final": 9068}]},
    {"sigla": "SCZ", "nome": "Santa Cruz",         "vias": [{"via": "1", "mt_inicial": 9399, "mt_final": 9467}, {"via": "2", "mt_inicial": 9398, "mt_final": 9466}]},
    {"sigla": "CKB", "nome": "Chácara Klabin",     "vias": [{"via": "1", "mt_inicial": 9873, "mt_final": 9941}, {"via": "2", "mt_inicial": 9874, "mt_final": 9942}]},
]

# Lista plana (um dict por via) — formato consumido por mapa_trocas_trilho em views.py
ESTACOES_MAPA = [
    {"sigla": e["sigla"], "nome": e["nome"], "via": v["via"], "mt_inicial": v["mt_inicial"], "mt_final": v["mt_final"]}
    for e in ESTACOES
    for v in e["vias"]
]

# Tuplas para ChoiceField — formato consumido por TrocaTrilhoForm em forms.py
ESTACOES_CHOICES = [("", "---------")] + [
    (e["sigla"], f"{e['sigla']} - {e['nome']}")
    for e in ESTACOES
]
