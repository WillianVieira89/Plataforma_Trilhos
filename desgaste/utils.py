import re


def extrair_numero_mt(valor):
    """Extrai o valor numérico de um marco topográfico (ex: 'MT-123' → 123, 'MT-1023' → 1023)."""
    if valor is None:
        return None

    texto = str(valor).strip()
    numeros = re.findall(r"\d+", texto)

    if not numeros:
        return None

    return int("".join(numeros))
