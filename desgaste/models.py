from django.db import models
from django.core.exceptions import ValidationError

class Linha(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome


class Estacao(models.Model):
    linha = models.ForeignKey(Linha, on_delete=models.CASCADE, related_name="estacoes")
    nome = models.CharField(max_length=100)
    sigla = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.nome} ({self.sigla})"


class PontoOperacional(models.Model):
    TIPO_PONTO_CHOICES = [
        ("patio", "Pátio"),
        ("estacao", "Estação"),
        ("amv", "AMV"),
        ("aparelho_dilatador", "Aparelho Dilatador"),
        ("estacionamento_auxiliar", "Estacionamento Auxiliar"),
        ("terminal", "Terminal"),
        ("acesso", "Acesso"),
        ("outro", "Outro"),
    ]

    POSICAO_CHOICES = [
        ("leste", "Leste"),
        ("oeste", "Oeste"),
        ("centro", "Centro"),
        ("nao_aplicavel", "Não aplicável"),
    ]

    estacao = models.ForeignKey(
        Estacao,
        on_delete=models.CASCADE,
        related_name="pontos_operacionais",
        null=True,
        blank=True,
    )
    codigo = models.CharField(max_length=30)
    descricao = models.CharField(max_length=150)
    tipo_ponto = models.CharField(max_length=30, choices=TIPO_PONTO_CHOICES)
    ordem = models.PositiveIntegerField()
    posicao = models.CharField(max_length=20, choices=POSICAO_CHOICES, default="nao_aplicavel")
    possui_acesso_patio = models.BooleanField(default=False)
    observacoes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["ordem"]
        unique_together = ("codigo", "ordem")

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"


class Trilho(models.Model):
    VIA_CHOICES = [
        ("1", "Via 01"),
        ("2", "Via 02"),
    ]

    TRILHO_CHOICES = [
        ("A", "Trilho A"),
        ("B", "Trilho B"),
        ("C", "Trilho C"),
        ("D", "Trilho D"),
    ]

    ponto_operacional = models.ForeignKey(
        PontoOperacional,
        on_delete=models.CASCADE,
        related_name="trilhos",
    )
    via = models.CharField(max_length=1, choices=VIA_CHOICES)
    lado_trilho = models.CharField(max_length=1, choices=TRILHO_CHOICES)
    ponto_kilometrico = models.CharField(max_length=30, blank=True, null=True)
    marco_topografico = models.CharField(max_length=30, blank=True, null=True)
    tipo_trilho = models.CharField(max_length=100, blank=True, null=True)
    fabricante = models.CharField(max_length=100, blank=True, null=True)
    data_instalacao = models.DateField(blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("ponto_operacional", "via", "lado_trilho")

    def _ultimo_numero(self, valor):
        if not valor:
            return None

        numeros = "".join(ch if ch.isdigit() else " " for ch in valor).split()

        if not numeros:
            return None

        return int(numeros[-1])

    def clean(self):
        pares_validos = {
            "1": ["A", "B"],
            "2": ["C", "D"],
        }

        if self.via and self.lado_trilho:
            if self.lado_trilho not in pares_validos.get(self.via, []):
                raise ValidationError({
                    "lado_trilho": (
                        f'Para a Via {self.via}, os trilhos permitidos são '
                        f'{", ".join(pares_validos[self.via])}.'
                    )
                })

        for campo in ["ponto_kilometrico", "marco_topografico"]:
            valor = getattr(self, campo)
            ultimo = self._ultimo_numero(valor)

            if ultimo is None:
                continue

            if self.via == "1" and ultimo % 2 == 0:
                raise ValidationError({
                    campo: f"Na Via 01, o {campo.upper()} deve terminar em número ímpar."
                })

            if self.via == "2" and ultimo % 2 != 0:
                raise ValidationError({
                    campo: f"Na Via 02, o {campo.upper()} deve terminar em número par."
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ponto_operacional} - Via {self.via} - Trilho {self.lado_trilho}"


class Inspecao(models.Model):
    TIPO_INSPECAO_CHOICES = [
        ("rotina", "Rotina"),
        ("preventiva", "Preventiva"),
        ("corretiva", "Corretiva"),
        ("extraordinaria", "Extraordinária"),
    ]

    trilho = models.ForeignKey(
        Trilho,
        on_delete=models.CASCADE,
        related_name="inspecoes",
    )
    data_inspecao = models.DateField()
    hora_inspecao = models.TimeField()
    inspetor = models.CharField(max_length=100)
    tipo_inspecao = models.CharField(max_length=20, choices=TIPO_INSPECAO_CHOICES, default="rotina")
    observacoes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-data_inspecao", "-hora_inspecao"]

    def __str__(self):
        return f"{self.trilho} - {self.data_inspecao} {self.hora_inspecao}"


class MedicaoDesgaste(models.Model):
    STATUS_CHOICES = [
        ("normal", "Normal"),
        ("atencao", "Atenção"),
        ("critico", "Crítico"),
    ]

    inspecao = models.OneToOneField(
        Inspecao,
        on_delete=models.CASCADE,
        related_name="medicao",
    )
    desgaste_vertical_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    desgaste_lateral_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    observacao_tecnica = models.TextField(blank=True, null=True)
    status_desgaste = models.CharField(max_length=20, choices=STATUS_CHOICES, default="normal")

    class Meta:
        verbose_name = "Medição de Desgaste"
        verbose_name_plural = "Medições de Desgaste"

    def __str__(self):
        return f"Medição - {self.inspecao}"


class FaixaLocalizacao(models.Model):
    VIA_CHOICES = [
        ("1", "Via 01"),
        ("2", "Via 02"),
    ]

    ponto_operacional = models.ForeignKey(
        PontoOperacional,
        on_delete=models.CASCADE,
        related_name="faixas_localizacao",
    )
    via = models.CharField(max_length=1, choices=VIA_CHOICES)
    mt_inicial = models.CharField(max_length=30, blank=True, null=True)
    ponto_kilometrico_inicial = models.CharField(max_length=30, blank=True, null=True)
    mt_final = models.CharField(max_length=30, blank=True, null=True)
    ponto_kilometrico_final = models.CharField(max_length=30, blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Faixa de Localização"
        verbose_name_plural = "Faixas de Localização"
        unique_together = ("ponto_operacional", "via")

    def _ultimo_numero(self, valor):
        if not valor:
            return None

        numeros = "".join(ch if ch.isdigit() else " " for ch in valor).split()

        if not numeros:
            return None

        return int(numeros[-1])

    def clean(self):
        campos = [
            "mt_inicial",
            "ponto_kilometrico_inicial",
            "mt_final",
            "ponto_kilometrico_final",
        ]

        for campo in campos:
            valor = getattr(self, campo)
            ultimo = self._ultimo_numero(valor)

            if ultimo is None:
                continue

            if self.via == "1" and ultimo % 2 == 0:
                raise ValidationError({
                    campo: f"Na Via 01, {campo} deve terminar em número ímpar."
                })

            if self.via == "2" and ultimo % 2 != 0:
                raise ValidationError({
                    campo: f"Na Via 02, {campo} deve terminar em número par."
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ponto_operacional} - Via {self.via}"


class ReferenciaLinearPKMT(models.Model):
    VIA_CHOICES = [
        ("1", "Via 01"),
        ("2", "Via 02"),
    ]

    via = models.CharField(max_length=1, choices=VIA_CHOICES)
    marco_topografico = models.CharField(max_length=30)
    ponto_kilometrico = models.CharField(max_length=30)
    local_excel = models.CharField(max_length=100)
    observacoes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Referência Linear PK/MT"
        verbose_name_plural = "Referências Lineares PK/MT"
        ordering = ["via", "marco_topografico"]

    def __str__(self):
        return (
            f"Via {self.via} - Marco Topográfico {self.marco_topografico} - "
            f"PK {self.ponto_kilometrico} - {self.local_excel}"
        )


class TipoSetor(models.TextChoices):
    TRECHO = "trecho", "Trecho"
    PATIO = "patio", "Pátio"


class ViaChoices(models.TextChoices):
    VIA_01 = "VIA_01", "Via 01"
    VIA_02 = "VIA_02", "Via 02"


class TrilhoChoices(models.TextChoices):
    A = "A", "Trilho A"
    B = "B", "Trilho B"
    C = "C", "Trilho C"
    D = "D", "Trilho D"


class CriticidadeChoices(models.TextChoices):
    BAIXA = "baixa", "Baixa"
    MEDIA = "media", "Média"
    ALTA = "alta", "Alta"
    CRITICA = "critica", "Crítica"


class SetorInspecao(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=TipoSetor.choices)
    ordem = models.PositiveIntegerField(unique=True)
    limite_inicial = models.CharField(max_length=30, blank=True)
    limite_final = models.CharField(max_length=30, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["ordem"]
        verbose_name = "Setor de inspeção"
        verbose_name_plural = "Setores de inspeção"

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class ItemInspecao(models.Model):
    nome = models.CharField(max_length=150, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Item de inspeção"
        verbose_name_plural = "Itens de inspeção"

    def __str__(self):
        return self.nome


class InspecaoTrecho(models.Model):
    setor = models.ForeignKey(
        SetorInspecao,
        on_delete=models.PROTECT,
        related_name="inspecoes",
    )
    data_inspecao = models.DateField()

    hora_inspecao = models.TimeField(
        verbose_name="Hora início da inspeção",
    )

    hora_fim_inspecao = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Hora fim da inspeção",
    )

    via = models.CharField(
        max_length=10,
        choices=ViaChoices.choices,
        blank=True,
    )

    # Campo mantido como legado. A inspeção atual é por via completa:
    # Via 01 = Trilhos A/B | Via 02 = Trilhos C/D.
    trilho = models.CharField(
        max_length=1,
        choices=TrilhoChoices.choices,
        blank=True,
    )

    estacao_referencia = models.CharField(max_length=80, blank=True)
    referencia_local = models.CharField(max_length=120, blank=True)

    pk_inicial = models.CharField(max_length=20, blank=True)
    pk_final = models.CharField(max_length=20, blank=True)
    mt_inicial = models.CharField(max_length=20, blank=True)
    mt_final = models.CharField(max_length=20, blank=True)

    responsavel = models.CharField(max_length=120)
    observacoes_gerais = models.TextField(blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-data_inspecao", "-hora_inspecao"]
        verbose_name = "Inspeção de trecho"
        verbose_name_plural = "Inspeções de trecho"

    def __str__(self):
        return f"{self.setor.codigo} - {self.data_inspecao} {self.hora_inspecao.strftime('%H:%M')}"

    def clean(self):
        errors = {}

        if self.trilho and not self.via:
            errors["via"] = "Informe a via para usar trilho."

        if self.via == ViaChoices.VIA_01 and self.trilho and self.trilho not in [TrilhoChoices.A, TrilhoChoices.B]:
            errors["trilho"] = "Na Via 01, o trilho deve ser A ou B."

        if self.via == ViaChoices.VIA_02 and self.trilho and self.trilho not in [TrilhoChoices.C, TrilhoChoices.D]:
            errors["trilho"] = "Na Via 02, o trilho deve ser C ou D."

        if self.hora_inspecao and self.hora_fim_inspecao:
            if self.hora_fim_inspecao < self.hora_inspecao:
                errors["hora_fim_inspecao"] = "A hora fim não pode ser menor que a hora início."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class OcorrenciaInspecaoTrecho(models.Model):
    inspecao = models.ForeignKey(
        InspecaoTrecho,
        on_delete=models.CASCADE,
        related_name="ocorrencias",
    )

    trilho = models.CharField(
        max_length=1,
        choices=TrilhoChoices.choices,
        blank=True,
        verbose_name="Trilho da ocorrência",
    )

    mt_problema = models.CharField(
        max_length=30,
        blank=True,
        default="",
        verbose_name="MT do problema",
    )

    item = models.ForeignKey(
        ItemInspecao,
        on_delete=models.PROTECT,
        related_name="ocorrencias",
    )

    criticidade = models.CharField(
        max_length=10,
        choices=CriticidadeChoices.choices,
        default=CriticidadeChoices.MEDIA,
    )

    observacao = models.TextField(blank=True)
    foto = models.ImageField(upload_to="inspecoes/ocorrencias/", blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ocorrência da inspeção de trecho"
        verbose_name_plural = "Ocorrências da inspeção de trecho"

    def __str__(self):
        trilho = f" - Trilho {self.trilho}" if self.trilho else ""
        mt = f" - MT {self.mt_problema}" if self.mt_problema else ""
        return f"{self.item.nome}{trilho}{mt} - {self.inspecao}"

    def clean(self):
        errors = {}

        via = getattr(self.inspecao, "via", None)

        if via == ViaChoices.VIA_01 and self.trilho and self.trilho not in [TrilhoChoices.A, TrilhoChoices.B]:
            errors["trilho"] = "Na Via 01, a ocorrência deve ser vinculada ao Trilho A ou B."

        if via == ViaChoices.VIA_02 and self.trilho and self.trilho not in [TrilhoChoices.C, TrilhoChoices.D]:
            errors["trilho"] = "Na Via 02, a ocorrência deve ser vinculada ao Trilho C ou D."

        if errors:
            raise ValidationError(errors)
class TrocaTrilho(models.Model):
    VIA_CHOICES = [
        ("1", "Via 01"),
        ("2", "Via 02"),
    ]

    TRILHO_CHOICES = [
        ("A", "Trilho A"),
        ("B", "Trilho B"),
        ("C", "Trilho C"),
        ("D", "Trilho D"),
    ]

    PERFIL_TRILHO_CHOICES = [
        ("UIC60", "UIC 60"),
    ]

    CLASSE_TRILHO_CHOICES = [
        ("260", "260"),
        ("350", "350"),
        ("400", "400"),
    ]

    TIPO_SOLDA_CHOICES = [
        ("thermit", "Thermit"),
        ("rail_tech", "Rail Tech"),
    ]

    SIM_NAO_CHOICES = [
        ("sim", "Sim"),
        ("nao", "Não"),
    ]

    MOTIVO_TROCA_CHOICES = [
        ("programada", "Programada"),
        ("trinca", "Trinca"),
        ("desgaste", "Desgaste"),
    ]

    data_troca = models.DateField()

    hora_troca = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Hora da troca",
    )

    hora_inicio_troca = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Hora início da troca",
    )

    hora_fim_troca = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Hora fim da troca",
    )

    via = models.CharField(max_length=1, choices=VIA_CHOICES)
    trilho = models.CharField(max_length=1, choices=TRILHO_CHOICES)

    estacao_referencia = models.CharField(max_length=80, blank=True)
    referencia_local = models.CharField(max_length=120, blank=True)

    mt_inicial = models.CharField(max_length=30)
    mt_final = models.CharField(max_length=30)
    tamanho_trilho_m = models.DecimalField(max_digits=8, decimal_places=2)

    medida_folga_mm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Medida da folga (mm)",
    )

    solda_fechamento = models.CharField(
        max_length=3,
        choices=SIM_NAO_CHOICES,
        blank=True,
        verbose_name="Solda de fechamento?",
    )

    trilho_transicao = models.CharField(
        max_length=3,
        choices=SIM_NAO_CHOICES,
        blank=True,
        verbose_name="Trilho de transição?",
    )

    temperatura_antes_solda_c = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Temperatura antes da solda (°C)",
    )

    temperatura_depois_solda_c = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Temperatura depois da solda (°C)",
    )

    tempo_aquecimento_seg = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Tempo de aquecimento (min)",
    )

    tempo_vazao_seg = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Tempo de vazão (s)",
    )

    imagem = models.ImageField(
        upload_to="trocas_trilho/",
        blank=True,
        null=True,
        verbose_name="Imagem",
    )

    motivo_troca = models.CharField(
        max_length=20,
        choices=MOTIVO_TROCA_CHOICES,
        blank=True,
        verbose_name="Motivo da troca",
    )

    perfil_trilho = models.CharField(max_length=20, choices=PERFIL_TRILHO_CHOICES, blank=True)
    classe_trilho = models.CharField(max_length=10, choices=CLASSE_TRILHO_CHOICES, blank=True)
    tipo_solda = models.CharField(max_length=20, choices=TIPO_SOLDA_CHOICES, blank=True)

    os_numero = models.CharField(max_length=50, blank=True)
    responsavel = models.CharField(max_length=120)
    observacoes = models.TextField(blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-data_troca", "-hora_inicio_troca", "-hora_troca"]
        verbose_name = "Troca de Trilho"
        verbose_name_plural = "Trocas de Trilho"

    def __str__(self):
        return f"{self.data_troca} - Via {self.via} - Trilho {self.trilho}"

    @staticmethod
    def extrair_numero_mt(valor):
        import re

        if valor is None:
            return None

        texto = str(valor).strip()
        numeros = re.findall(r"\d+", texto)

        if not numeros:
            return None

        return int("".join(numeros))

    def clean(self):
        errors = {}

        pares_validos = {
            "1": ["A", "B"],
            "2": ["C", "D"],
        }

        if self.via and self.trilho:
            if self.trilho not in pares_validos.get(self.via, []):
                errors["trilho"] = (
                    f'Para a Via {self.via}, os trilhos permitidos são '
                    f'{", ".join(pares_validos[self.via])}.'
                )

        if self.tamanho_trilho_m is not None and self.tamanho_trilho_m <= 0:
            errors["tamanho_trilho_m"] = "Informe um tamanho de trilho maior que zero."

        if self.hora_inicio_troca and self.hora_fim_troca:
            if self.hora_fim_troca < self.hora_inicio_troca:
                errors["hora_fim_troca"] = "A hora fim não pode ser menor que a hora início."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.hora_troca and self.hora_inicio_troca:
            self.hora_troca = self.hora_inicio_troca

        mt_ini_num = self.extrair_numero_mt(self.mt_inicial)
        mt_fim_num = self.extrair_numero_mt(self.mt_final)

        if mt_ini_num is not None and mt_fim_num is not None:
            self.tamanho_trilho_m = abs(mt_fim_num - mt_ini_num) * 2

        self.full_clean()
        super().save(*args, **kwargs)