from django import forms

from ..utils.ui import DBChoiceField


class DBForm(forms.Form):
    search_term = forms.CharField(max_length=255, required=False)
    database = DBChoiceField()
