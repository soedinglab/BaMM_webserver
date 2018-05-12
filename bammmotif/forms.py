from django import forms

from .models import JobInfo
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
    job_ID = forms.CharField(max_length=255)
