from django.core.exceptions import ValidationError
from ..utils.misc import valid_uuid


def UUID_validator(value):
    if not valid_uuid(value):
        raise ValidationError('this does not look like a job id')
