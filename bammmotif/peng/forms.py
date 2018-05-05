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
    if not form.is_valid() or not meta_job_form.is_valid():
        args['form'] = PengForm()
        args['type'] = "OK"
        args['message'] = "OK"
        valid = False
        return form, meta_job_form, valid, args

    valid = True
    return form, meta_job_form, valid, args


class _PengToBammForm(forms.ModelForm):
    class Meta:
        model = BaMMJob
        fields = ('reverse_Complement', 'model_order',
                  'extend', 'background_Order',
                  'Background_Sequences', 'score_Seqset', 'score_Cutoff',
                  'FDR', 'motif_db', 'MMcompare', 'e_value_cutoff')

class PengToBammForm(_PengToBammForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['motif_db'] = DBChoiceField()
        for name, field in self.fields.items():
            field.help_text = HELP_TEXTS[name]
