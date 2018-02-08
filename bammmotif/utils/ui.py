from django import forms
from ..models import MotifDatabase


class DBChoiceField(forms.ModelChoiceField):

    def __init__(self):
        dbs = MotifDatabase.objects.all().order_by('display_name')
        super().__init__(queryset=dbs, empty_label=None)

    def label_from_instance(self, obj):
        return obj.display_name
