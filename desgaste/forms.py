from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory
from django.utils import timezone

from .constants import ESTACOES_CHOICES
from .utils import extrair_numero_mt
from .models import (
    PontoOperacional,
    Trilho,
    Inspecao,
    MedicaoDesgaste,
    InspecaoTrecho,
    ItemInspecao,
    OcorrenciaInspecaoTrecho,
    SetorInspecao,
    TipoSetor,
    TrocaTrilho,
    Estacao,
    ViaChoices,
    TrilhoChoices,
    Lubrificador,
    RegistroLubrificador,
    OrdemCorretivaLubrificador,
    ResultadoInspecaoChoices,
    StatusLubrificadorChoices,
    AlimentacaoEletricaChoices,
    ControladoraChoices,
    MotorLubrificadorChoices,
    IntegridadeReguaChoices,
    SensorInducaoChoices,
)




class RegistroInspecaoForm(forms.Form):
    ponto_operacional = forms.ModelChoiceField(
        queryset=PontoOperacional.objects.all().order_by("ordem"),
        label="Ponto operacional",
        empty_label="Selecione o ponto operacional",
    )

    via = forms.ChoiceField(
        label="Via",
        choices=[
            ("", "Selecione a via"),
            ("1", "Via 01"),
            ("2", "Via 02"),
        ],
    )

    trilho = forms.ModelChoiceField(
        queryset=Trilho.objects.select_related("ponto_operacional").all().order_by(
            "ponto_operacional__ordem",
            "via",
            "lado_trilho",
        ),
        label="Trilho",
        empty_label="Selecione o trilho",
    )

    data_inspecao = forms.DateField(
        label="Data da inspeção",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    hora_inspecao = forms.TimeField(
        label="Hora da inspeção",
        widget=forms.TimeInput(attrs={"type": "time"}),
    )

    inspetor = forms.CharField(
        label="Inspetor",
        max_length=100,
        widget=forms.TextInput(attrs={"placeholder": "Digite o nome do inspetor"}),
    )

    tipo_inspecao = forms.ChoiceField(
        label="Tipo de inspeção",
        choices=Inspecao.TIPO_INSPECAO_CHOICES,
    )

    observacoes = forms.CharField(
        label="Observações da inspeção",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Observações gerais da inspeção",
            }
        ),
    )

    desgaste_vertical_mm = forms.DecimalField(
        label="Desgaste vertical (mm)",
        max_digits=6,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(
            attrs={
                "step": "0.01",
                "placeholder": "Ex.: 2.50",
            }
        ),
    )

    desgaste_lateral_mm = forms.DecimalField(
        label="Desgaste lateral (mm)",
        max_digits=6,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(
            attrs={
                "step": "0.01",
                "placeholder": "Ex.: 1.20",
            }
        ),
    )

    observacao_tecnica = forms.CharField(
        label="Observação técnica",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Observações técnicas da medição",
            }
        ),
    )

    status_desgaste = forms.ChoiceField(
        label="Status do desgaste",
        choices=MedicaoDesgaste.STATUS_CHOICES,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        agora = timezone.localtime()
        self.fields["data_inspecao"].initial = agora.date()
        self.fields["hora_inspecao"].initial = agora.strftime("%H:%M")

    def clean(self):
        cleaned_data = super().clean()

        ponto_operacional = cleaned_data.get("ponto_operacional")
        via = cleaned_data.get("via")
        trilho = cleaned_data.get("trilho")

        if trilho and ponto_operacional and trilho.ponto_operacional_id != ponto_operacional.id:
            self.add_error(
                "trilho",
                "O trilho selecionado não pertence ao ponto operacional escolhido.",
            )

        if trilho and via and trilho.via != via:
            self.add_error(
                "trilho",
                "O trilho selecionado não pertence à via escolhida.",
            )

        return cleaned_data


class InspecaoForm(forms.ModelForm):
    class Meta:
        model = InspecaoTrecho
        fields = [
            "setor",
            "data_inspecao",
            "hora_inspecao",
            "hora_fim_inspecao",
            "via",
            "responsavel",
            "observacoes_gerais",
        ]

        widgets = {
            "setor": forms.Select(attrs={"class": "form-control"}),
            "data_inspecao": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),
            "hora_inspecao": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "form-control",
                }
            ),
            "hora_fim_inspecao": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "form-control",
                }
            ),
            "via": forms.Select(attrs={"class": "form-control", "id": "id_via"}),
            "responsavel": forms.TextInput(attrs={"class": "form-control"}),
            "observacoes_gerais": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        agora = timezone.localtime()

        self.fields["setor"].queryset = SetorInspecao.objects.filter(
            ativo=True
        ).order_by("ordem")

        self.fields["data_inspecao"].initial = agora.date()

        self.fields["hora_inspecao"].initial = None
        self.fields["hora_fim_inspecao"].initial = None

        self.fields["hora_inspecao"].required = True
        self.fields["hora_fim_inspecao"].required = True

        self.fields["hora_inspecao"].input_formats = ["%H:%M"]
        self.fields["hora_fim_inspecao"].input_formats = ["%H:%M"]

        self.fields["hora_inspecao"].label = "Hora início da inspeção"
        self.fields["hora_fim_inspecao"].label = "Hora fim da inspeção"
        self.fields["via"].label = "Via inspecionada"

    def clean(self):
        cleaned_data = super().clean()

        setor = cleaned_data.get("setor")
        via = cleaned_data.get("via")
        hora_inicio = cleaned_data.get("hora_inspecao")
        hora_fim = cleaned_data.get("hora_fim_inspecao")

        if setor and setor.tipo == TipoSetor.TRECHO and not via:
            self.add_error(
                "via",
                "Para setores do tipo trecho, informe a via inspecionada.",
            )

        if hora_inicio and hora_fim and hora_fim < hora_inicio:
            self.add_error(
                "hora_fim_inspecao",
                "A hora fim não pode ser menor que a hora início.",
            )

        return cleaned_data


class OcorrenciaInspecaoTrechoForm(forms.ModelForm):
    class Meta:
        model = OcorrenciaInspecaoTrecho
        fields = ["trilho", "mt_problema", "item", "criticidade", "foto"]

        widgets = {
            "trilho": forms.Select(attrs={
                "class": "form-control trilho-ocorrencia",
            }),
            "mt_problema": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ex.: MT-123",
            }),
            "item": forms.Select(attrs={
                "class": "form-control",
            }),
            "criticidade": forms.Select(attrs={
                "class": "form-control",
            }),
            "foto": forms.ClearableFileInput(attrs={
                "class": "form-control",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["trilho"].required = True
        self.fields["trilho"].label = "Trilho"

        self.fields["mt_problema"].required = True
        self.fields["mt_problema"].label = "MT do problema"

        self.fields["item"].queryset = ItemInspecao.objects.filter(
            ativo=True
        ).order_by("nome")


class OcorrenciaInspecaoTrechoBaseFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        if any(self.errors):
            return

        via = ""

        if self.data:
            via = str(self.data.get("via") or "").strip()
        elif self.instance:
            via = str(getattr(self.instance, "via", "") or "").strip()

        permitidos_por_via = {
            ViaChoices.VIA_01: [TrilhoChoices.A, TrilhoChoices.B],
            ViaChoices.VIA_02: [TrilhoChoices.C, TrilhoChoices.D],
        }

        permitidos = permitidos_por_via.get(via)

        if not permitidos:
            return

        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue

            cleaned_data = form.cleaned_data

            if not cleaned_data:
                continue

            if cleaned_data.get("DELETE"):
                continue

            trilho = cleaned_data.get("trilho")

            if not trilho:
                continue

            if trilho not in permitidos:
                if via == ViaChoices.VIA_01:
                    raise forms.ValidationError(
                        "Na Via 01, as ocorrências devem ser cadastradas apenas nos Trilhos A ou B."
                    )

                if via == ViaChoices.VIA_02:
                    raise forms.ValidationError(
                        "Na Via 02, as ocorrências devem ser cadastradas apenas nos Trilhos C ou D."
                    )


OcorrenciaInspecaoFormSet = inlineformset_factory(
    InspecaoTrecho,
    OcorrenciaInspecaoTrecho,
    form=OcorrenciaInspecaoTrechoForm,
    formset=OcorrenciaInspecaoTrechoBaseFormSet,
    extra=1,
    can_delete=True,
)

OcorrenciaInspecaoTrechoFormSet = OcorrenciaInspecaoFormSet


class TrocaTrilhoForm(forms.ModelForm):
    estacao_referencia = forms.ChoiceField(
        choices=ESTACOES_CHOICES,
        required=False,
        label="Estação referência",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = TrocaTrilho
        fields = [
            "data_troca",
            "hora_inicio_troca",
            "hora_fim_troca",
            "via",
            "trilho",
            "estacao_referencia",
            "referencia_local",
            "mt_inicial",
            "mt_final",
            "medida_folga_mm",
            "solda_fechamento",
            "trilho_transicao",
            "temperatura_antes_solda_c",
            "temperatura_depois_solda_c",
            "tempo_aquecimento_seg",
            "tempo_vazao_seg",
            "perfil_trilho",
            "classe_trilho",
            "tipo_solda",
            "motivo_troca",
            "os_numero",
            "responsavel",
            "observacoes",
            "imagem",
        ]

        widgets = {
            "data_troca": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),
            "hora_inicio_troca": forms.TimeInput(
                format="%H:%M",
                attrs={
                    "type": "time",
                    "class": "form-control",
                },
            ),
            "hora_fim_troca": forms.TimeInput(
                format="%H:%M",
                attrs={
                    "type": "time",
                    "class": "form-control",
                },
            ),
            "via": forms.Select(
                attrs={
                    "class": "form-control",
                    "id": "id_via",
                }
            ),
            "trilho": forms.Select(
                attrs={
                    "class": "form-control",
                    "id": "id_trilho",
                }
            ),
            "referencia_local": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex.: Plataforma, trecho entre estações, pátio...",
                }
            ),
            "mt_inicial": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex.: MT-123",
                }
            ),
            "mt_final": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex.: MT-145",
                }
            ),
            "medida_folga_mm": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "Ex.: 5.00",
                }
            ),
            "solda_fechamento": forms.Select(attrs={"class": "form-control"}),
            "trilho_transicao": forms.Select(attrs={"class": "form-control"}),
            "temperatura_antes_solda_c": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "Ex.: 32.50",
                }
            ),
            "temperatura_depois_solda_c": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "Ex.: 45.20",
                }
            ),
            "tempo_aquecimento_seg": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "Minutos",
                }
            ),
            "tempo_vazao_seg": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "Segundos",
                }
            ),
            "perfil_trilho": forms.Select(attrs={"class": "form-control"}),
            "classe_trilho": forms.Select(attrs={"class": "form-control"}),
            "tipo_solda": forms.Select(attrs={"class": "form-control"}),
            "motivo_troca": forms.Select(attrs={"class": "form-control"}),
            "os_numero": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Número da OS",
                }
            ),
            "responsavel": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Responsável pela troca",
                }
            ),
            "observacoes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                }
            ),
            "imagem": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        agora = timezone.localtime()

        self.fields["data_troca"].initial = agora.date()
        self.fields["hora_inicio_troca"].initial = agora.strftime("%H:%M")
        self.fields["hora_fim_troca"].initial = agora.strftime("%H:%M")

        self.fields["hora_inicio_troca"].input_formats = ["%H:%M"]
        self.fields["hora_fim_troca"].input_formats = ["%H:%M"]

        self.fields["data_troca"].required = True
        self.fields["hora_inicio_troca"].required = True
        self.fields["hora_fim_troca"].required = True
        self.fields["via"].required = True
        self.fields["trilho"].required = True
        self.fields["mt_inicial"].required = True
        self.fields["mt_final"].required = True

        self.fields["responsavel"].required = True
        self.fields["tempo_aquecimento_seg"].label = "Tempo de aquecimento (min)"
        self.fields["motivo_troca"].label = "Motivo da troca"

        try:
            estacoes = Estacao.objects.all().order_by("nome")
            choices = [("", "---------")]

            for estacao in estacoes:
                choices.append((estacao.sigla, f"{estacao.sigla} - {estacao.nome}"))

            if len(choices) > 1:
                self.fields["estacao_referencia"].choices = choices
            else:
                self.fields["estacao_referencia"].choices = ESTACOES_CHOICES

        except Exception:
            self.fields["estacao_referencia"].choices = ESTACOES_CHOICES

    def clean(self):
        cleaned_data = super().clean()

        via = str(cleaned_data.get("via") or "").strip()
        trilho = str(cleaned_data.get("trilho") or "").strip().upper()
        hora_inicio = cleaned_data.get("hora_inicio_troca")
        hora_fim = cleaned_data.get("hora_fim_troca")

        if via == "1" and trilho and trilho not in ["A", "B"]:
            self.add_error(
                "trilho",
                "Para a Via 01, selecione apenas Trilho A ou Trilho B.",
            )

        if via == "2" and trilho and trilho not in ["C", "D"]:
            self.add_error(
                "trilho",
                "Para a Via 02, selecione apenas Trilho C ou Trilho D.",
            )

        if hora_inicio and hora_fim and hora_fim < hora_inicio:
            self.add_error(
                "hora_fim_troca",
                "A hora fim não pode ser menor que a hora início.",
            )

        mt_ini_num = extrair_numero_mt(cleaned_data.get("mt_inicial"))
        mt_fim_num = extrair_numero_mt(cleaned_data.get("mt_final"))

        if mt_ini_num is not None and mt_fim_num is not None and mt_ini_num == mt_fim_num:
            self.add_error("mt_final", "O MT final deve ser diferente do MT inicial.")

        return cleaned_data


class BaseAtuacaoLubrificadorForm(forms.ModelForm):
    class Meta:
        model = RegistroLubrificador
        fields = []

        widgets = {
            "data_hora": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                },
            ),
            "resultado_inspecao": forms.Select(
                attrs={"class": "form-control"}
            ),
            "resultado_corretiva": forms.Select(
                attrs={"class": "form-control"}
            ),
            "status_operacional": forms.Select(
                attrs={"class": "form-control"}
            ),
            "nivel_graxa_percentual": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "max": "100",
                    "step": "1",
                    "inputmode": "numeric",
                    "oninput": (
                        "if (this.value !== '') {"
                        "this.value = Math.min(100, "
                        "Math.max(0, Number(this.value)));"
                        "}"
                    ),
                    "placeholder": "Ex.: 80",
                }
            ),
            "alimentacao_eletrica": forms.Select(
                attrs={"class": "form-control"}
            ),
            "tensao_alimentacao": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01",
                    "placeholder": "Ex.: 220.00",
                }
            ),
            "controladora": forms.Select(
                attrs={"class": "form-control"}
            ),
            "motor": forms.Select(
                attrs={"class": "form-control"}
            ),
            "integridade_regua": forms.Select(
                attrs={"class": "form-control"}
            ),
            "quantidade_total_bicos": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "1",
                    "placeholder": "Quantidade instalada",
                }
            ),
            "quantidade_bicos_funcionais": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "1",
                    "placeholder": "Quantidade funcionando",
                }
            ),
            "sensor_inducao": forms.Select(
                attrs={"class": "form-control"}
            ),
            "falha_encontrada": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": (
                        "Descreva a anomalia ou condição encontrada."
                    ),
                }
            ),
            "servico_executado": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Descreva detalhadamente o serviço executado."
                    ),
                }
            ),
            "observacoes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Informações adicionais.",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["data_hora"].input_formats = [
            "%Y-%m-%dT%H:%M",
        ]

        if not self.instance.pk and not self.is_bound:
            self.fields["data_hora"].initial = (
                timezone.localtime().strftime("%Y-%m-%dT%H:%M")
            )

    def clean(self):
        cleaned_data = super().clean()

        total = cleaned_data.get("quantidade_total_bicos")
        funcionais = cleaned_data.get("quantidade_bicos_funcionais")

        if total is None and funcionais is not None:
            self.add_error(
                "quantidade_total_bicos",
                "Informe também a quantidade total de bicos.",
            )

        if total is not None and funcionais is None:
            self.add_error(
                "quantidade_bicos_funcionais",
                "Informe também a quantidade de bicos funcionais.",
            )

        if (
            total is not None
            and funcionais is not None
            and funcionais > total
        ):
            self.add_error(
                "quantidade_bicos_funcionais",
                (
                    "A quantidade de bicos funcionais não pode ser "
                    "maior que a quantidade total."
                ),
            )

        return cleaned_data


class InspecaoLubrificadorForm(BaseAtuacaoLubrificadorForm):
    class Meta(BaseAtuacaoLubrificadorForm.Meta):
        fields = [
            "data_hora",
            "resultado_inspecao",
            "status_operacional",
            "nivel_graxa_percentual",
            "alimentacao_eletrica",
            "tensao_alimentacao",
            "controladora",
            "motor",
            "integridade_regua",
            "quantidade_total_bicos",
            "quantidade_bicos_funcionais",
            "sensor_inducao",
            "observacoes",
        ]

    def identificar_nao_conformidades(self, cleaned_data):
        status = cleaned_data.get("status_operacional")

        if (
            status
            and status != StatusLubrificadorChoices.OPERANTE
        ):
            opcoes = dict(StatusLubrificadorChoices.choices)
            descricao = opcoes.get(status, status)

            return [
                f"Status operacional: {descricao}"
            ]

        return []

    def identificar_falhas(self, cleaned_data):
        verificacoes = [
            (
                "Alimentação elétrica",
                "alimentacao_eletrica",
                AlimentacaoEletricaChoices.NORMAL,
                dict(AlimentacaoEletricaChoices.choices),
            ),
            (
                "Controladora",
                "controladora",
                ControladoraChoices.LIGADA,
                dict(ControladoraChoices.choices),
            ),
            (
                "Motor",
                "motor",
                MotorLubrificadorChoices.FUNCIONANDO,
                dict(MotorLubrificadorChoices.choices),
            ),
            (
                "Régua",
                "integridade_regua",
                IntegridadeReguaChoices.INTEGRA,
                dict(IntegridadeReguaChoices.choices),
            ),
            (
                "Sensor de indução",
                "sensor_inducao",
                SensorInducaoChoices.FUNCIONANDO,
                dict(SensorInducaoChoices.choices),
            ),
        ]

        falhas = []

        for titulo, campo, valor_normal, opcoes in verificacoes:
            valor = cleaned_data.get(campo)

            if valor and valor != valor_normal:
                descricao = opcoes.get(valor, valor)
                falhas.append(
                    f"{titulo}: {descricao}"
                )

        total = cleaned_data.get("quantidade_total_bicos")
        funcionais = cleaned_data.get(
            "quantidade_bicos_funcionais"
        )

        if (
            total is not None
            and funcionais is not None
            and funcionais < total
        ):
            quantidade_falhas = total - funcionais

            falhas.append(
                (
                    f"Bicos com falha: {quantidade_falhas} "
                    f"de {total}"
                )
            )

        return falhas

    def clean(self):
        cleaned_data = super().clean()

        resultado = cleaned_data.get("resultado_inspecao")

        nao_conformidades = (
            self.identificar_nao_conformidades(cleaned_data)
        )

        falhas = self.identificar_falhas(cleaned_data)

        condicoes_anormais = nao_conformidades + falhas

        self.nao_conformidades_identificadas = (
            nao_conformidades
        )
        self.falhas_identificadas = falhas

        if (
            resultado == ResultadoInspecaoChoices.COM_ANOMALIA
            and not condicoes_anormais
        ):
            self.add_error(
                "resultado_inspecao",
                (
                    "Para registrar uma anomalia, informe um "
                    "status diferente de Operante ou selecione "
                    "ao menos uma condição técnica anormal."
                ),
            )

        if (
            resultado == ResultadoInspecaoChoices.CONFORME
            and condicoes_anormais
        ):
            self.add_error(
                "resultado_inspecao",
                (
                    "O resultado não pode ser Conforme porque foram "
                    "identificadas as seguintes condições: "
                    + "; ".join(condicoes_anormais)
                ),
            )

        if (
            resultado == ResultadoInspecaoChoices.COM_ANOMALIA
            and falhas
        ):
            self.instance.falha_encontrada = "; ".join(falhas)
        else:
            self.instance.falha_encontrada = ""

        return cleaned_data


class CorretivaLubrificadorForm(BaseAtuacaoLubrificadorForm):
    class Meta(BaseAtuacaoLubrificadorForm.Meta):
        fields = [
            "data_hora",
            "resultado_corretiva",
            "status_operacional",
            "nivel_graxa_percentual",
            "alimentacao_eletrica",
            "tensao_alimentacao",
            "controladora",
            "motor",
            "integridade_regua",
            "quantidade_total_bicos",
            "quantidade_bicos_funcionais",
            "sensor_inducao",
            "servico_executado",
            "observacoes",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["servico_executado"].required = True

    def clean_servico_executado(self):
        servico = str(
            self.cleaned_data.get("servico_executado") or ""
        ).strip()

        if not servico:
            raise forms.ValidationError(
                "Descreva o serviço executado na manutenção corretiva."
            )

        return servico


class OrdemCorretivaLubrificadorForm(forms.ModelForm):
    class Meta:
        model = OrdemCorretivaLubrificador
        fields = ["numero"]

        widgets = {
            "numero": forms.TextInput(
                attrs={
                    "class": "form-control ordem-corretiva",
                    "placeholder": "Ex.: 54109217",
                    "autocomplete": "off",
                }
            ),
        }

    def clean_numero(self):
        numero = str(
            self.cleaned_data.get("numero") or ""
        ).strip().upper()

        if not numero:
            raise forms.ValidationError(
                "Informe o número da ordem corretiva."
            )

        return numero


class OrdemCorretivaLubrificadorBaseFormSet(BaseInlineFormSet):
    def __init__(
        self,
        *args,
        quantidade_minima=1,
        **kwargs,
    ):
        self.quantidade_minima = max(
            1,
            int(quantidade_minima or 1),
        )

        super().__init__(*args, **kwargs)

        if not self.is_bound:
            self.extra = self.quantidade_minima

    def clean(self):
        super().clean()

        if any(self.errors):
            return

        numeros = []
        quantidade_valida = 0

        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue

            dados = form.cleaned_data

            if not dados or dados.get("DELETE"):
                continue

            numero = str(dados.get("numero") or "").strip().upper()

            if not numero:
                continue

            quantidade_valida += 1

            if numero in numeros:
                raise forms.ValidationError(
                    f"A ordem corretiva {numero} foi informada mais de uma vez."
                )

            numeros.append(numero)

        if quantidade_valida < self.quantidade_minima:
            raise forms.ValidationError(
                (
                    f"Foram identificadas "
                    f"{self.quantidade_minima} falhas. "
                    f"Informe pelo menos "
                    f"{self.quantidade_minima} ordens corretivas."
                )
            )


OrdemCorretivaLubrificadorFormSet = inlineformset_factory(
    RegistroLubrificador,
    OrdemCorretivaLubrificador,
    form=OrdemCorretivaLubrificadorForm,
    formset=OrdemCorretivaLubrificadorBaseFormSet,
    extra=1,
    can_delete=True,
)


# Compatibilidade temporária com a view anterior.
RegistroLubrificadorForm = InspecaoLubrificadorForm


class LubrificadorCadastroForm(forms.ModelForm):
    class Meta:
        model = Lubrificador
        fields = [
            "nome",
            "via",
            "mt",
        ]

        widgets = {
            "nome": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex.: LUB-27",
                }
            ),
            "via": forms.Select(
                attrs={"class": "form-control"}
            ),
            "mt": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex.: MT-1541",
                }
            ),
        }

    def clean_nome(self):
        nome = self.cleaned_data["nome"].strip().upper()

        queryset = Lubrificador.objects.filter(
            nome__iexact=nome
        )

        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise forms.ValidationError(
                "Já existe um lubrificador com este nome."
            )

        return nome
