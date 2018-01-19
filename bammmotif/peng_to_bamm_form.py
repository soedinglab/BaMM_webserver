from django import forms
from .models import Job, MotifDatabase


class DBChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.display_name

class PengToBammForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('reverse_Complement',
                  'model_Order', 'extend',
                  'background_Order',
                  'Background_Sequences', 'score_Seqset',
                  'score_Cutoff', 'FDR',
                  'q_value', 'motif_db')
        
    motif_dbs = None
    motif_db = DBChoiceField(queryset=motif_dbs, empty_label=None)

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

