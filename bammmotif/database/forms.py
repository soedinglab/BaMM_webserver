from django import forms

from ..utils.ui import DBChoiceField, HELP_TEXTS


class DBForm(forms.Form):
    search_term = forms.CharField(max_length=255, required=False,
                                  help_text=HELP_TEXTS['search_term'])
    database = DBChoiceField(help_text=HELP_TEXTS['motif_db'])
