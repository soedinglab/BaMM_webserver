import os

from django import template

register = template.Library()

@register.filter
def in_category(DbMatch, m):
    return DbMatch.filter(motif=m)

@register.simple_tag
def filter_motifs(motifs, directory, filetype=".png"):
    print("filter_motifs")
    for motif in motifs:
        print(motif.meme_id)
        if not motif.select:
            print("delete")
            # Delete motif, reverse motif and zip
            fname = os.path.join(directory, motif + ".png")
            fname_rev = os.path.join(directory, motif + "_rev.png")
            fname_zip = os.path.join(directory, motif + ".zip")
            os.remove(fname)
            os.remove(fname_rev)
            os.remove(fname_zip)
