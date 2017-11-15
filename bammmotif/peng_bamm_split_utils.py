from django.shortcuts import get_object_or_404
from .models import PengJob
from django.core.files import File
from django.conf import settings
from .peng_bamm_split_job import peng_meme_directory
from .utils.meme_reader import update_and_copy_meme_file

import os
import shutil
import subprocess

def upload_example_fasta_for_peng(job_id):
    peng_job = get_object_or_404(PengJob, pk=job_id)
    out_filename = "ExampleData.fasta"
    with open(settings.EXAMPLE_FASTA) as fh:
        peng_job.fasta_file.save(out_filename, File(fh))
        peng_job.save()

def copy_peng_to_bamm(peng_id, bamm_id, post):
    # Copy plots
    # peng_plot_output_directory = os.path.join(peng_meme_directory(peng_id), "meme_plots")
    peng_save_directory = os.path.join(peng_meme_directory(peng_id), "selected_motifs")
    bamm_output_dir = os.path.join(settings.MEDIA_ROOT, str(bamm_id), "pengoutput")
    bamm_plot_output_directory = os.path.join(bamm_output_dir, 'meme_plots')
    if not os.path.exists(bamm_plot_output_directory):
        os.makedirs(bamm_plot_output_directory)
    for file in os.listdir(peng_save_directory):
        shutil.copy(os.path.join(peng_save_directory, file), bamm_plot_output_directory)
    # copy meme.out
    meme_path_src = os.path.join(peng_meme_directory(peng_id), "out.meme")
    meme_path_dst = os.path.join(bamm_output_dir, "out.meme")
    update_and_copy_meme_file(meme_path_src, meme_path_dst, peng_save_directory)
    print("meme_path_src", meme_path_src)
    # shutil.copy(meme_path_src, bamm_output_dir)
    # copy input file
    peng_input = os.path.join(settings.MEDIA_ROOT, str(peng_id), "Input")
    bamm_input = os.path.join(settings.MEDIA_ROOT, str(bamm_id), "Input")
    if not os.path.exists(bamm_input):
        os.makedirs(bamm_input)
    # TODO: Is this supposed to be multiple files??
    for file in os.listdir(peng_input):
        shutil.copy(os.path.join(peng_input, file), bamm_input)

def load_meme_ids(path, filetype='.png'):
    for _, _, files in os.walk(path):
        filelist = [x.rsplit('.', maxsplit=1)[0] for x in files if x.endswith(filetype)]
    return filelist

def zip_motifs(motif_ids, directory, with_reverse=True):
    for motif in motif_ids:
        cmd = ['zip']
        cmd.append('-j')
        archive_name = os.path.join(directory, motif + ".zip")
        if os.path.exists(archive_name):
            os.remove(archive_name)
        cmd.append(archive_name)
        args = os.path.join(directory, motif + ".png")
        cmd.append(args)
        # Now add meme file
        meme_file = os.path.join(directory, motif + ".meme")
        cmd.append(meme_file)
        if with_reverse:
            additional_args = " %s_rev.png" % os.path.join(directory, motif)
            cmd.append(additional_args)
            # Use -j option to prune directory prefixes
        #cmd = "zip -j %s %s" % (archive_name, args)
        # print(cmd)
        subprocess.run(cmd)
    # Now zip all
    plots = [os.path.join(directory, x) for x in os.listdir(directory) if x.endswith(".png") or x.endswith(".meme")]
    archive_name = os.path.join(directory, "motif_all.zip")
    cmd = ['zip', '-j', archive_name] + plots
    # cmd = "zip -j %s %s" % (archive_name, plots)
    # print(cmd)
    subprocess.run(cmd)

def check_if_request_from_peng_directly(request):
    from_peng_identifier = "from_peng"
    if "meme_meta_info" not in request.POST:
        return False
    if request.POST["meme_meta_info"] == from_peng_identifier:
        return True
    return False

def save_selected_motifs(request, pk):
    print("save_selected_motifs")
    MOTIF_SELECT_IDENTIFIER = "_select"
    peng_plot_output_directory = os.path.join(peng_meme_directory(pk), "meme_plots")
    peng_save_directory = os.path.join(peng_meme_directory(pk), "selected_motifs")
    if not os.path.exists(peng_save_directory):
        os.makedirs(peng_save_directory)
    selected_motifs = [x.replace(MOTIF_SELECT_IDENTIFIER, "") for x in request.keys() if x.endswith(MOTIF_SELECT_IDENTIFIER)]
    print(selected_motifs)
    for file in os.listdir(peng_plot_output_directory):
        if any([file.startswith(x) for x in selected_motifs]):
            print("copying: ", file)
            shutil.copy(os.path.join(peng_plot_output_directory, file), os.path.join(peng_save_directory, file))


