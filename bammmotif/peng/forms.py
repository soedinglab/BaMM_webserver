from django.conf import settings
from django import forms

from ..bamm.models import BaMMJob
from ..forms import MetaJobNameForm
from ..utils.ui import DBChoiceField, HELP_TEXTS

from .models import PengJob


class _PengForm(forms.ModelForm):

    class Meta:
        model = PengJob
        fields = (
            'fasta_file', 'bg_sequences',
            'pattern_length', 'zscore_threshold', 'count_threshold', 'bg_model_order',
            'reverse_Complement', 'objective_function', 'no_em'
        )


class PengForm(_PengForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.help_text = HELP_TEXTS[name]


class _PengExampleForm(forms.ModelForm):

    class Meta:
        model = PengJob
        fields = (
            'bg_sequences',
            'pattern_length', 'zscore_threshold', 'count_threshold', 'bg_model_order',
            'reverse_Complement', 'objective_function', 'no_em',
        )


class PengExampleForm(_PengExampleForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.help_text = HELP_TEXTS[name]


def get_valid_peng_form(post, files, user, mode):
    args = {}
    meta_job_form = MetaJobNameForm(post)

    if mode == 'example':
        valid = True
        args['form'] = PengExampleForm()
        return PengExampleForm(post, files), meta_job_form, valid, args

    form = PengForm(post, files)
    if not form.is_valid() or meta_job_form.is_valid():
        args['form'] = PengForm()
        args['type'] = "OK"
        args['message'] = "OK"
        valid = False
        return form, meta_job_form, valid, args

    if user.is_authenticated:
        max_size = settings.MAX_UPLOAD_SIZE
    else:
        max_size = settings.MAX_UPLOAD_SIZE_ANONYMOUS

    # Test if data maximum size is not reached
    content = form.cleaned_data['fasta_file']
    if content._size > int(max_size):
        args['form'] = PengForm()
        args['type'] = "FileSize"
        args['message'] = max_size
        valid = False
        return form, meta_job_form, valid, args

    valid = True
    return form, meta_job_form, valid, args


class PengToBammForm(forms.ModelForm):
    class Meta:
        model = BaMMJob
        fields = ('reverse_Complement', 'model_order',
                  'extend', 'background_Order',
                  'Background_Sequences', 'score_Seqset', 'score_Cutoff',
                  'FDR', 'q_value', 'motif_db')

    def __init__(self, *args, **kwargs):
        super(PengToBammForm, self).__init__(*args, **kwargs)
        self.fields['motif_db'] = DBChoiceField()

        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update({'class': 'has-popover',
                                                        'data-content': help_text,
                                                        'data-placement': 'right',
                                                        'data-container': 'body'})
