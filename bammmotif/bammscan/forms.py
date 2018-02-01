from django import forms
from django.forms import inlineformset_factory

from .models import BaMMScanJob
from ..models import JobInfo
from ..utils.ui import DBChoiceField


class BaMMScanForm(forms.ModelForm):
    class Meta:
        model = BaMMScanJob
        fields = (
            'Input_Sequences',
            'Motif_InitFile',
            'Motif_Init_File_Format',
            'bgModel_File',
            'reverse_Complement',
            'score_Cutoff',
            'FDR',
            'MMcompare',
            'p_value_cutoff',
            'motif_db',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['motif_db'] = DBChoiceField()


class BaMMScanExampleForm(forms.ModelForm):
    class Meta:
        model = BaMMScanJob
        fields = (
            'reverse_Complement',
            'score_Cutoff',
            'FDR',
            'MMcompare',
            'p_value_cutoff',
            'motif_db',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['motif_db'] = DBChoiceField()


class BaMMScanDBForm(forms.ModelForm):
    class Meta:
        model = BaMMScanJob
        fields = (
            'Input_Sequences',
            'reverse_Complement',
            'score_Cutoff',
            'FDR',
            'MMcompare',
            'p_value_cutoff',
            'motif_db',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['motif_db'] = DBChoiceField()
