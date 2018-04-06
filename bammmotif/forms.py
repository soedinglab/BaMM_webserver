from django import forms
from .models import JobInfo


class MetaJobNameForm(forms.ModelForm):
    class Meta:
        model = JobInfo
        fields = ('job_name',)


class FindForm(forms.Form):
    job_ID = forms.CharField(max_length=255)
