from django import forms
from bammmotif.models import Job, Bamm

class PengToBammForm(forms.ModelForm):
    class Meta:
        model = Bamm
        fields = ('model_Order',
                  'extend', 'background_Order',
                  'Background_Sequences', 'score_Seqset', 'score_Cutoff',
                  'FDR', 'q_value',)

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

