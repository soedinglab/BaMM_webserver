from django import forms
from .models import Job, PengJob_deprecated
from .command_line import ShootPengModule


#class PengForm(forms.ModelForm):
#
#    class Meta:
#        model = PengJob
#        fields = tuple(ShootPengModule().options.keys()) + ('job_name',)
#        #fields = (
#        #    'fasta_file', 'meme_output', 'json_output', 'temp_dir', 'bg_sequences',
#        #    'pattern_length', 'zscore_threshold', 'count_threshold', 'bg_model_order',
#        #    'strand', 'objective_function', 'enrich_pseudocount_factor', 'no_em',
#        #    'em_saturation_threshold', 'em_threshold', 'em_max_iterations', 'no_merging',
#        #    'bit_factor_threshold', 'use_default_pwm', 'pwm_pseudo_counts', 'n_threads',
#        #    'silent', 'job_name'
#        #)
#
#    def __init__(self, *args, **kwargs):
#        super(PengForm, self).__init__(*args, **kwargs)
#        for field in self.fields:
#            help_text = self.fields[field].help_text
#            self.fields[field].help_text = None
#            if help_text != '':
#                self.fields[field].widget.attrs.update({'class': 'has-popover',
#                                                        'data-content': help_text,
#                                                        'data-placement': 'right',
#                                                        'data-container': 'body'})


@deprecated("outdated")
class PredictionForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('job_name', 'Input_Sequences', 'reverse_Complement',
                  'model_Order', 'extend_1', 'extend_2', 'bgModel_File',
                  'Motif_Initialization', 'Motif_InitFile',
                  'Motif_Init_File_Format', 'background_Order',
                  'Background_Sequences', 'score_Seqset',
                  'score_Cutoff', 'FDR', 'm_Fold', 'sampling_Order',
                  'q_value', 'MMcompare', 'p_value_cutoff')

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


@deprecated("outdated")
class PredictionExampleForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('job_name', 'reverse_Complement', 'model_Order',
                  'extend_1', 'extend_2', 'background_Order',
                  'Background_Sequences', 'score_Seqset', 'score_Cutoff',
                  'FDR', 'm_Fold', 'sampling_Order', 'q_value',
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


@deprecated("outdated")
class OccurrenceForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('job_name', 'Input_Sequences', 'Motif_InitFile',
                  'Motif_Init_File_Format', 'bgModel_File',
                  'reverse_Complement', 'score_Cutoff', 'FDR',
                  'm_Fold', 'sampling_Order',
                  'MMcompare', 'p_value_cutoff')


@deprecated("outdated")
class OccurrenceExampleForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('job_name', 'reverse_Complement', 'score_Cutoff',
                  'FDR', 'm_Fold', 'sampling_Order',
                  'MMcompare', 'p_value_cutoff')


@deprecated("outdated")
class OccurrenceDBForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('job_name', 'Input_Sequences', 'reverse_Complement',
                  'score_Cutoff', 'FDR', 'm_Fold', 'sampling_Order',
                  'MMcompare', 'p_value_cutoff')


@deprecated("outdated")
class CompareForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('job_name', 'Motif_InitFile', 'Motif_Init_File_Format',
                  'bgModel_File', 'model_Order', 'p_value_cutoff')


@deprecated("outdated")
class CompareExampleForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('job_name', 'p_value_cutoff')


class FindForm(forms.Form):
    job_ID = forms.CharField(max_length=255)


class DBForm(forms.Form):
    db_ID = forms.CharField(max_length=255)
