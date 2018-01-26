from django import forms
from .models import Job, MotifDatabase, JobInfo
from .utils.ui import DBChoiceField


class MetaJobNameForm(forms.ModelForm):
    class Meta:
        model = JobInfo
        fields = ('job_name',)


class PredictionForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('job_name', 'Input_Sequences', 'reverse_Complement',
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
        model = Job
        fields = ('job_name', 'reverse_Complement', 'model_Order',
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


class OccurrenceForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('job_name', 'Input_Sequences', 'Motif_InitFile',
                  'Motif_Init_File_Format', 'bgModel_File',
                  'reverse_Complement', 'score_Cutoff', 'FDR',
                  'MMcompare', 'p_value_cutoff')


class OccurrenceExampleForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('job_name', 'reverse_Complement', 'score_Cutoff',
                  'FDR',
                  'MMcompare', 'p_value_cutoff')


class OccurrenceDBForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('job_name', 'Input_Sequences', 'reverse_Complement',
                  'score_Cutoff', 'FDR',
                  'MMcompare', 'p_value_cutoff')


class CompareForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('job_name', 'Motif_InitFile', 'Motif_Init_File_Format',
                  'bgModel_File', 'p_value_cutoff')


class CompareExampleForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('job_name', 'p_value_cutoff')


class FindForm(forms.Form):
    job_ID = forms.CharField(max_length=255)
