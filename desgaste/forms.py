from django import forms
from django.utils import timezone
from django.forms import inlineformset_factory

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
)


class RegistroInspecaoForm(forms.Form):
    ponto_operacional = forms.ModelChoiceField(
        queryset=PontoOperacional.objects.all().order_by('ordem'),
        label='Ponto operacional',
        empty_label='Selecione o ponto operacional'
    )

    via = forms.ChoiceField(
        label='Via',
        choices=[
            ('', 'Selecione a via'),
            ('1', 'Via 01'),
            ('2', 'Via 02'),
        ]
    )

    trilho = forms.ModelChoiceField(
        queryset=Trilho.objects.select_related('ponto_operacional').all().order_by(
            'ponto_operacional__ordem', 'via', 'lado_trilho'
        ),
        label='Trilho',
        empty_label='Selecione o trilho'
    )

    data_inspecao = forms.DateField(
        label='Data da inspeção',
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    hora_inspecao = forms.TimeField(
        label='Hora da inspeção',
        widget=forms.TimeInput(attrs={'type': 'time'})
    )

    inspetor = forms.CharField(
        label='Inspetor',
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Digite o nome do inspetor'})
    )

    tipo_inspecao = forms.ChoiceField(
        label='Tipo de inspeção',
        choices=Inspecao.TIPO_INSPECAO_CHOICES
    )

    observacoes = forms.CharField(
        label='Observações da inspeção',
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Observações gerais da inspeção'
        })
    )

    desgaste_vertical_mm = forms.DecimalField(
        label='Desgaste vertical (mm)',
        max_digits=6,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Ex.: 2.50'})
    )

    desgaste_lateral_mm = forms.DecimalField(
        label='Desgaste lateral (mm)',
        max_digits=6,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Ex.: 1.20'})
    )

    observacao_tecnica = forms.CharField(
        label='Observação técnica',
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Observações técnicas da medição'
        })
    )

    status_desgaste = forms.ChoiceField(
        label='Status do desgaste',
        choices=MedicaoDesgaste.STATUS_CHOICES
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        agora = timezone.localtime()
        self.fields['data_inspecao'].initial = agora.date()
        self.fields['hora_inspecao'].initial = agora.strftime('%H:%M')

    def clean(self):
        cleaned_data = super().clean()

        ponto_operacional = cleaned_data.get('ponto_operacional')
        via = cleaned_data.get('via')
        trilho = cleaned_data.get('trilho')

        if trilho and ponto_operacional and trilho.ponto_operacional_id != ponto_operacional.id:
            self.add_error('trilho', 'O trilho selecionado não pertence ao ponto operacional escolhido.')

        if trilho and via and trilho.via != via:
            self.add_error('trilho', 'O trilho selecionado não pertence à via escolhida.')

        return cleaned_data


class InspecaoForm(forms.ModelForm):
    class Meta:
        model = InspecaoTrecho
        fields = [
            "setor",
            "data_inspecao",
            "hora_inspecao",
            "via",
            "trilho",
            "estacao_referencia",
            "referencia_local",
            "pk_inicial",
            "pk_final",
            "mt_inicial",
            "mt_final",
            "responsavel",
            "observacoes_gerais",
        ]
        widgets = {
            "setor": forms.Select(attrs={"class": "form-control"}),
            "data_inspecao": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "hora_inspecao": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "via": forms.Select(attrs={"class": "form-control"}),
            "trilho": forms.Select(attrs={"class": "form-control"}),
            "estacao_referencia": forms.TextInput(attrs={"class": "form-control"}),
            "referencia_local": forms.TextInput(attrs={"class": "form-control"}),
            "pk_inicial": forms.TextInput(attrs={"class": "form-control"}),
            "pk_final": forms.TextInput(attrs={"class": "form-control"}),
            "mt_inicial": forms.TextInput(attrs={"class": "form-control"}),
            "mt_final": forms.TextInput(attrs={"class": "form-control"}),
            "responsavel": forms.TextInput(attrs={"class": "form-control"}),
            "observacoes_gerais": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["setor"].queryset = SetorInspecao.objects.filter(ativo=True).order_by("ordem")
        self.fields["data_inspecao"].initial = timezone.localdate()

    def clean(self):
        cleaned_data = super().clean()
        setor = cleaned_data.get("setor")
        via = cleaned_data.get("via")

        if setor and setor.tipo == TipoSetor.TRECHO and not via:
            self.add_error("via", "Para setores do tipo trecho, informe a via.")

        return cleaned_data


class OcorrenciaInspecaoTrechoForm(forms.ModelForm):
    class Meta:
        model = OcorrenciaInspecaoTrecho
        fields = ["item", "criticidade", "observacao", "foto"]
        widgets = {
            "item": forms.Select(attrs={"class": "form-control"}),
            "criticidade": forms.Select(attrs={"class": "form-control"}),
            "observacao": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "foto": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["item"].queryset = ItemInspecao.objects.filter(ativo=True).order_by("nome")


OcorrenciaInspecaoFormSet = inlineformset_factory(
    InspecaoTrecho,
    OcorrenciaInspecaoTrecho,
    form=OcorrenciaInspecaoTrechoForm,
    extra=1,
    can_delete=True,
)

# Alias opcional para manter compatibilidade, se algum outro arquivo usar este nome
OcorrenciaInspecaoTrechoFormSet = OcorrenciaInspecaoFormSet

class TrocaTrilhoForm(forms.ModelForm):
    class Meta:
        model = TrocaTrilho
        fields = [
            'data_troca',
            'hora_troca',
            'via',
            'trilho',
            'estacao_referencia',
            'referencia_local',
            'mt_inicial',
            'mt_final',
            'tamanho_trilho_m',
            'medida_folga_mm',
            'solda_fechamento',
            'trilho_transicao',
            'temperatura_antes_solda_c',
            'temperatura_depois_solda_c',
            'tempo_aquecimento_seg',
            'tempo_vazao_seg',
            'perfil_trilho',
            'classe_trilho',
            'tipo_solda',
            'motivo_troca',
            'os_numero',
            'responsavel',
            'observacoes',
            'imagem',
        ]
        widgets = {
            'data_troca': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_troca': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'via': forms.Select(attrs={'class': 'form-control'}),
            'trilho': forms.Select(attrs={'class': 'form-control'}),
            'estacao_referencia': forms.TextInput(attrs={'class': 'form-control'}),
            'referencia_local': forms.TextInput(attrs={'class': 'form-control'}),
            'mt_inicial': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: MT-123'}),
            'mt_final': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: MT-145'}),
            'tamanho_trilho_m': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Ex.: 18.00'}),
            'medida_folga_mm': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Ex.: 5.00'}),
            'temperatura_antes_solda_c': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Ex.: 32.50'}),
            'solda_fechamento': forms.Select(attrs={'class': 'form-control'}),
            'trilho_transicao': forms.Select(attrs={'class': 'form-control'}),
            'temperatura_depois_solda_c': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Ex.: 45.20'}),
            'tempo_aquecimento_seg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Segundos'}),
            'tempo_vazao_seg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Segundos'}),

            'perfil_trilho': forms.Select(attrs={'class': 'form-control'}),
            'classe_trilho': forms.Select(attrs={'class': 'form-control'}),
            'tipo_solda': forms.Select(attrs={'class': 'form-control'}),
            'motivo_troca': forms.TextInput(attrs={'class': 'form-control'}),
            'os_numero': forms.TextInput(attrs={'class': 'form-control'}),
            'responsavel': forms.TextInput(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'imagem': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        agora = timezone.localtime()
        self.fields['data_troca'].initial = agora.date()
        self.fields['hora_troca'].initial = agora.strftime('%H:%M')