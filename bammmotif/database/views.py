from os import path

from django.shortcuts import render, get_object_or_404

from .forms import DBForm
from ..models import ChIPseq


def maindb(request):
    if request.method == "POST":
        form = DBForm(request.POST)
        if form.is_valid():
            search_term = form.cleaned_data['search_term']
            motif_db = form.cleaned_data['database']
            db_entries = ChIPseq.objects.filter(target_name__icontains=search_term,
                                                motif_db=motif_db)
            if db_entries.exists():
                return render(
                    request, 'database/db_overview.html',
                    {
                        'protein_name': search_term,
                        'db_entries': db_entries,
                        'db_location': motif_db.relative_db_model_dir
                    })
            else:
                form = DBForm()
                return render(request, 'database/db_main.html', {'form': form, 'warning': True})
    else:
        form = DBForm()
    return render(request, 'database/db_main.html', {'form': form})


def db_detail(request, pk):
    entry = get_object_or_404(ChIPseq, motif_id=pk)
    db_location = entry.motif_db.relative_db_model_dir
    return render(request, 'database/db_detail.html',
                  {'entry': entry, 'db_location': db_location})
