from django.db import models


# slightly adapted from: https://stackoverflow.com/a/1113039/2272172

class SeparatedValuesField(models.TextField):

    def __init__(self, *args, **kwargs):
        self.token = kwargs.pop('token', ';')
        super(SeparatedValuesField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            return
        if isinstance(value, list):
            return value
        return value.split(self.token)

    def get_db_prep_value(self, value, connection, prepared):
        if value:
            assert(isinstance(value, list) or isinstance(value, tuple))
            return self.token.join()

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)
