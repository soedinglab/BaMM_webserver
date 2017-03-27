from django import template

register = template.Library()

@register.filter
def in_category(DbMatch, m):
    return DbMatch.filter(motif=m)


