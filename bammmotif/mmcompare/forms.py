from django import forms
from .models import MMcompareJob
from ..utils.ui import DBChoiceField, HELP_TEXTS


class _MMCompareForm(forms.ModelForm):
    class Meta:
        model = MMcompareJob
        fields = ('Motif_InitFile', 'Motif_Init_File_Format',
                  'bgModel_File', 'e_value_cutoff', 'motif_db')


class MMCompareForm(_MMCompareForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.help_text = HELP_TEXTS[name]
        self.fields['motif_db'] = DBChoiceField(help_text=HELP_TEXTS['motif_db_compare'])


class _MMCompareExampleForm(forms.ModelForm):
    class Meta:
        model = MMcompareJob
        fields = ('e_value_cutoff', 'motif_db')


class MMCompareExampleForm(_MMCompareExampleForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.help_text = HELP_TEXTS[name]
        self.fields['motif_db'] = DBChoiceField(help_text=HELP_TEXTS['motif_db_compare'])
