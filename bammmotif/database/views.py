from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)

from .forms import DBForm
from ..models import ChIPseq, MotifDatabase


def maindb(request):
    if request.method == "POST":
        form = DBForm(request.POST)
        if form.is_valid():
            motif_db = form.cleaned_data['database']

            if 'browse_button' in request.POST:
                return redirect('db_browse', db_id=motif_db.db_id)

            search_term = form.cleaned_data['search_term']
            if not search_term:
                form = DBForm(request.POST)
                return render(request, 'database/db_main.html', {'form': form, 'warning': True})
            db_entries = ChIPseq.objects.filter(target_name__icontains=search_term,
                                                motif_db=motif_db)
            if db_entries.exists():
                return render(
                    request, 'database/db_overview.html',
                    {
                        'protein_name': search_term,
                        'db_entries': db_entries,
                        'db_location': motif_db.relative_db_model_dir,
                        'is_bamm_database': motif_db.model_parameters.modelorder > 0,
                    })
            else:
                form = DBForm(request.POST)
                return render(request, 'database/db_main.html', {'form': form, 'warning': True})
    else:
        form = DBForm()
    return render(request, 'database/db_main.html', {'form': form})


def db_browse(request, db_id):
    motif_db = get_object_or_404(MotifDatabase, db_id=db_id)
    db_entries = ChIPseq.objects.filter(motif_db=db_id)
    search_term = motif_db.display_name

    return render(
        request, 'database/db_overview.html',
        {
            'protein_name': search_term,
            'db_entries': db_entries,
            'db_location': motif_db.relative_db_model_dir,
            'is_bamm_database': motif_db.model_parameters.modelorder > 0,
        })


def db_detail(request, pk):
    entry = get_object_or_404(ChIPseq, motif_id=pk)
    db_location = entry.motif_db.relative_db_model_dir
    return render(request, 'database/db_detail.html', {
        'entry': entry,
        'db_location': db_location,
        'is_bamm_database': entry.motif_db.model_parameters.modelorder > 0,
    })
