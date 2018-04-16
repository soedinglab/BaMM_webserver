from django import forms

from ..utils.ui import DBChoiceField, HELP_TEXTS

from .models import BaMMJob, OneStepBaMMJob


class PredictionForm(forms.ModelForm):
    class Meta:
        model = BaMMJob
        fields = ('Input_Sequences', 'reverse_Complement',
                  'model_order', 'extend', 'bgModel_File',
                  'Motif_Initialization', 'Motif_InitFile',
                  'Motif_Init_File_Format', 'background_Order',
                  'Background_Sequences', 'score_Seqset',
                  'score_Cutoff', 'FDR',
                  'q_value',
                  'MMcompare', 'e_value_cutoff')

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
        fields = ('reverse_Complement', 'model_order',
                  'extend', 'background_Order',
                  'Background_Sequences', 'score_Seqset', 'score_Cutoff',
                  'FDR', 'q_value',
                  'MMcompare', 'e_value_cutoff')

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


ONE_STEP_BASE_FIELDS = (
    'reverse_Complement', 'model_order',
    'extend', 'background_Order',
    'Background_Sequences', 'score_Seqset', 'score_Cutoff',
    'FDR',
    'MMcompare', 'motif_db', 'e_value_cutoff',
    'pattern_length', 'zscore_threshold', 'count_threshold',
    'objective_function', 'no_em', 'max_refined_motifs',
)


class _OneStepBammJobForm(forms.ModelForm):
    class Meta:
        model = OneStepBaMMJob
        fields = ('Input_Sequences',) + ONE_STEP_BASE_FIELDS


class OneStepBammJobForm(_OneStepBammJobForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['motif_db'] = DBChoiceField()
        for name, field in self.fields.items():
            field.help_text = HELP_TEXTS[name]


class _OneStepBammJobExampleForm(forms.ModelForm):
    class Meta:
        model = OneStepBaMMJob
        fields = ONE_STEP_BASE_FIELDS


class OneStepBammJobExampleForm(_OneStepBammJobExampleForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['motif_db'] = DBChoiceField()
        for name, field in self.fields.items():
            field.help_text = HELP_TEXTS[name]
