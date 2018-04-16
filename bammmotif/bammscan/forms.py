from django import forms
from django.forms import inlineformset_factory

from .models import BaMMScanJob
from ..models import JobInfo
from ..utils.ui import DBChoiceField, HELP_TEXTS


COMMON_FIELDS = (
    'reverse_Complement',
    'score_Cutoff',
    'FDR',
    'MMcompare',
    'e_value_cutoff',
    'motif_db',
)


class _BaMMScanForm(forms.ModelForm):
    class Meta:
        model = BaMMScanJob
        fields = (
            'Input_Sequences',
            'Motif_InitFile',
            'Motif_Init_File_Format',
            'bgModel_File',
        ) + COMMON_FIELDS


class BaMMScanForm(_BaMMScanForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['motif_db'] = DBChoiceField()
        for name, field in self.fields.items():
            field.help_text = HELP_TEXTS[name]


class _BaMMScanExampleForm(forms.ModelForm):
    class Meta:
        model = BaMMScanJob
        fields = COMMON_FIELDS


class BaMMScanExampleForm(_BaMMScanExampleForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['motif_db'] = DBChoiceField()
        for name, field in self.fields.items():
            field.help_text = HELP_TEXTS[name]


class _BaMMScanDBForm(forms.ModelForm):
    class Meta:
        model = BaMMScanJob
        fields = (
            'Input_Sequences',
        ) + COMMON_FIELDS


class BaMMScanDBForm(_BaMMScanDBForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['motif_db'] = DBChoiceField()
        for name, field in self.fields.items():
            field.help_text = HELP_TEXTS[name]
