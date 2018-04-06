from django import forms
from .models import MMcompareJob
from ..utils.ui import DBChoiceField


class MMCompareForm(forms.ModelForm):
    class Meta:
        model = MMcompareJob
        fields = ('Motif_InitFile', 'Motif_Init_File_Format',
                  'bgModel_File', 'e_value_cutoff', 'motif_db')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['motif_db'] = DBChoiceField()


class MMCompareExampleForm(forms.ModelForm):
    class Meta:
        model = MMcompareJob
        fields = ('e_value_cutoff', 'motif_db')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['motif_db'] = DBChoiceField()
