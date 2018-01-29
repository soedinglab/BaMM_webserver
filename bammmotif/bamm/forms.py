from django import forms
from ..models import JobInfo, BaMMJob
from ..utils.ui import DBChoiceField


class PredictionForm(forms.ModelForm):
    class Meta:
        model = BaMMJob
        fields = ('Input_Sequences', 'reverse_Complement',
                  'model_Order', 'extend', 'bgModel_File',
                  'Motif_Initialization', 'Motif_InitFile',
                  'Motif_Init_File_Format', 'background_Order',
                  'Background_Sequences', 'score_Seqset',
                  'score_Cutoff', 'FDR', 
                  'q_value',
                  'MMcompare', 'p_value_cutoff')

    def __init__(self, *args, **kwargs):
        super(PredictionForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update({'class': 'has-popover',
                                                        'data-content': help_text,
                                                        'data-placement': 'right',
                                                        'data-container': 'body'})


class PredictionExampleForm(forms.ModelForm):
    class Meta:
        model = BaMMJob
        fields = ('reverse_Complement', 'model_Order',
                  'extend', 'background_Order',
                  'Background_Sequences', 'score_Seqset', 'score_Cutoff',
                  'FDR', 'q_value',
                  'MMcompare', 'p_value_cutoff')

    def __init__(self, *args, **kwargs):
        super(PredictionExampleForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update({'class': 'has-popover',
                                                        'data-content': help_text,
                                                        'data-placement': 'right',
                                                        'data-container': 'body'})


class PengToBammForm(forms.ModelForm):
    class Meta:
        model = BaMMJob
        fields = ('reverse_Complement', 'model_Order',
                  'extend', 'background_Order',
                  'Background_Sequences', 'score_Seqset', 'score_Cutoff',
                  'FDR', 'q_value', 'motif_db')

    def __init__(self, *args, **kwargs):
        super(PengToBammForm, self).__init__(*args, **kwargs)
        self.motif_dbs = MotifDatabase.objects.all().order_by('display_name')
        self.fields['motif_db'].queryset = self.motif_dbs

        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update({'class': 'has-popover',
                                                        'data-content': help_text,
                                                        'data-placement': 'right',
                                                        'data-container': 'body'})
