import os

from django import template

register = template.Library()


@register.filter
def in_category(DbMatch, m):
    return DbMatch.filter(motif=m)


@register.filter
def filename(value):
    if not value:
        return value
    return os.path.basename(value.file.name)
