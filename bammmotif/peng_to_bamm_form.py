from django import forms
from .models import Job

class PengToBammForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('reverse_Complement',
                  'model_Order', 'extend', 'bgModel_File',
                  'background_Order',
                  'Background_Sequences', 'score_Seqset',
                  'score_Cutoff', 'FDR',
                  'q_value')

    def __init__(self, *args, **kwargs):
        super(PengToBammForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update({'class': 'has-popover',
                                                        'data-content': help_text,
                                                        'data-placement': 'right',
                                                        'data-container': 'body'})

