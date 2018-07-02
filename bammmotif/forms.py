from django import forms

from .models import JobInfo
from .models.validators import UUID_validator
from .utils.ui import HELP_TEXTS


class _MetaJobNameForm(forms.ModelForm):
    class Meta:
        model = JobInfo
        fields = ('job_name',)


class MetaJobNameForm(_MetaJobNameForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.help_text = HELP_TEXTS[name]


class FindForm(forms.Form):
    job_ID = forms.CharField(max_length=255, validators=[UUID_validator])


class _GenomeBrowserForm(forms.Form):
    organism = forms.CharField(max_length=255)
    assembly_id = forms.CharField(max_length=255)
    job_id = forms.CharField(max_length=255)
    motif_id = forms.IntegerField()


class GenomeBrowserForm(_GenomeBrowserForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.help_text = HELP_TEXTS[name]
