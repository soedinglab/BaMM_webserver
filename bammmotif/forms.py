from django import forms
from .models import Job

### upload input files for denovo prediction

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('job_name','Input_Sequences','reverse_Complement','model_Order','extend_1','extend_2','Motif_Initialization','Motif_InitFile','Motif_Init_File_Format','background_Order','Background_Sequences','FDR','m_Fold','cv_Fold','sampling_Order','EM','q_value','MMcompare','p_value_cutoff',)

    def __init__(self, *args, **kwargs):
        super(JobForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update({'class':'has-popover', 'data-content':help_text, 'data-placement':'right', 'data-container':'body'})

class ExampleForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('job_name','reverse_Complement','model_Order','extend_1','extend_2','Motif_Initialization','Motif_InitFile','Motif_Init_File_Format','background_Order','Background_Sequences','FDR','m_Fold','cv_Fold','sampling_Order','EM','q_value','MMcompare','p_value_cutoff',)

### upload input files for position discovery
class DiscoveryForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('job_name','Input_Sequences', 'Motif_InitFile' , 'Motif_Init_File_Format','bgModel_File','reverse_Complement','MMcompare','p_value_cutoff')


### upload input files for position discovery
class DiscoveryDBForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('job_name','Input_Sequences','reverse_Complement','MMcompare','p_value_cutoff')


class CompareForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('job_name', 'Motif_InitFile', 'Motif_Init_File_Format', 'bgModel_File', 'model_Order', 'p_value_cutoff')

class ExampleCompareForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('job_name', 'p_value_cutoff')

 
### Parameter settings for denovo prediction
class ParameterForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('model_Order', 'extend_1', 'extend_2',)

### insert job id to find corresponding results
class FindForm(forms.Form):
    job_ID = forms.CharField(max_length=255)

class DBForm(forms.Form):
    db_ID = forms.CharField(max_length=255)
