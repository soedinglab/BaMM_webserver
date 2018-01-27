from django.shortcuts import get_object_or_404
from bammmotif.models import Peng
from django.core.files import File
from django.conf import settings

from bammmotif.peng.io import meme_plot_directory, peng_meme_directory, get_temporary_job_dir, get_bmscore_filename
from bammmotif.utils.meme_reader import update_and_copy_meme_file, Meme
from bammmotif.peng.settings import (
    MEME_PLOT_DIRECTORY,
    MEME_OUTPUT_FILE,
    PENG_OUTPUT,
    SELECTED_MOTIFS,
    PENG_INPUT,
    ZIPPED_MOTIFS,
    MOTIF_SELECT_IDENTIFIER,
    EXAMPLE_FASTA_FILE,
    FILTERPWM_OUTPUT_FILE,
    JOB_OUTPUT_DIRECTORY,
    BAMMPLOT_SUFFIX_REV,
    BAMMPLOT_SUFFIX)
from webserver.settings import BAMM_INPUT
import os
import shutil
import subprocess
import csv

def upload_example_fasta_for_peng(job_id):
    peng_job = get_object_or_404(Peng, pk=job_id)
    out_filename = EXAMPLE_FASTA_FILE
    with open(settings.EXAMPLE_FASTA) as fh:
        peng_job.fasta_file.save(out_filename, File(fh))
        peng_job.save()

def copy_peng_to_bamm(peng_id, bamm_id, post):
    # Copy plots
    # peng_plot_output_directory = os.path.join(peng_meme_directory(peng_id), "meme_plots")
    peng_save_directory = os.path.join(peng_meme_directory(peng_id), SELECTED_MOTIFS)
    bamm_output_dir = os.path.join(settings.MEDIA_ROOT, str(bamm_id), PENG_OUTPUT)
    bamm_plot_output_directory = os.path.join(bamm_output_dir, MEME_PLOT_DIRECTORY)
    if not os.path.exists(bamm_plot_output_directory):
        os.makedirs(bamm_plot_output_directory)
    for file in os.listdir(peng_save_directory):
        shutil.copy(os.path.join(peng_save_directory, file), bamm_plot_output_directory)
    # copy meme.out
    meme_path_src = os.path.join(peng_meme_directory(peng_id), MEME_OUTPUT_FILE)
    meme_path_dst = os.path.join(bamm_output_dir, MEME_OUTPUT_FILE)
    update_and_copy_meme_file(meme_path_src, meme_path_dst, peng_save_directory)
    # copy results of filterPWM
    filterpwm_src = os.path.join(settings.MEDIA_ROOT, str(peng_id), JOB_OUTPUT_DIRECTORY, FILTERPWM_OUTPUT_FILE)
    #filterpwm_dst  = os.path.join(settings.MEDIA_ROOT, str(bamm_id), BAMM_INPUT)
    shutil.copy(filterpwm_src, bamm_output_dir)
    # copy input file
    peng_input = os.path.join(settings.MEDIA_ROOT, str(peng_id), PENG_INPUT)
    bamm_input = os.path.join(settings.MEDIA_ROOT, str(bamm_id), BAMM_INPUT)
    if not os.path.exists(bamm_input):
        os.makedirs(bamm_input)
    # TODO: Is this supposed to be multiple files??
    for file in os.listdir(peng_input):
        shutil.copy(os.path.join(peng_input, file), bamm_input)

def copy_bmscores(peng_id, bamm_id):
    bamm_input = os.path.join(settings.MEDIA_ROOT, str(bamm_id), BAMM_INPUT)
    bmf_path = os.path.join(get_temporary_job_dir(peng_id), get_bmscore_filename(peng_id))
    shutil.copy(bmf_path, bamm_input)


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
            additional_args = os.path.join(directory, motif + "_rev.png")
            cmd.append(additional_args)
            # Use -j option to prune directory prefixes
        #cmd = "zip -j %s %s" % (archive_name, args)
        # print(cmd)
        #print(os.path.join(directory, motif + ".png"))
        #print(" %s_rev.png" % os.path.join(directory, motif))
        subprocess.run(cmd)
    # Now zip all
    plots = [os.path.join(directory, x) for x in os.listdir(directory) if x.endswith(".png") or x.endswith(".meme")]
    # Add meme file
    plots.append(os.path.join(directory.rsplit('/', maxsplit=1)[0], MEME_OUTPUT_FILE))
    archive_name = os.path.join(directory, ZIPPED_MOTIFS)
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

def save_selected_motifs_old(request, pk):
    print("save_selected_motifs")
    peng_plot_output_directory = os.path.join(peng_meme_directory(pk), MEME_PLOT_DIRECTORY)
    peng_save_directory = os.path.join(peng_meme_directory(pk), SELECTED_MOTIFS)
    if not os.path.exists(peng_save_directory):
        os.makedirs(peng_save_directory)
    selected_motifs = [x.replace(MOTIF_SELECT_IDENTIFIER, "") for x in request.keys() if x.endswith(MOTIF_SELECT_IDENTIFIER)]
    print(selected_motifs)
    min_requirement_for_refinement = False
    for file in os.listdir(peng_plot_output_directory):
        if any([file.startswith(x) for x in selected_motifs]):
            min_requirement_for_refinement = True
            print("copying: ", file)
            shutil.copy(os.path.join(peng_plot_output_directory, file), os.path.join(peng_save_directory, file))
    return min_requirement_for_refinement


def rename_plots(meme_list, directory, prefix_name):
    # Utility function to not break too much of the current functions.
    for meme in meme_list:
        plot_name = os.path.join(directory, prefix_name + "_motif_" + str(meme.motif_number) + BAMMPLOT_SUFFIX)
        new_plot_name = meme.meme_id + ".png"
        os.rename(plot_name, new_plot_name)
        plot_name_rev = os.path.join(directory, prefix_name + "_motif_" + str(meme.motif_number) + BAMMPLOT_SUFFIX_REV)
        new_plot_name_rev = meme.meme_id + "_rev.png"
        os.rename(plot_name_rev, new_plot_name_rev)


def save_selected_motifs(request, pk):
    print("save_selected_motifs")
    peng_plot_output_directory = meme_plot_directory(str(pk))
    peng_save_directory = os.path.join(peng_meme_directory(pk), SELECTED_MOTIFS)
    if not os.path.exists(peng_save_directory):
        os.makedirs(peng_save_directory)
    selected_motifs = [x.replace(MOTIF_SELECT_IDENTIFIER, "") for x in request.keys() if x.endswith(MOTIF_SELECT_IDENTIFIER)]
    print(selected_motifs)
    min_requirement_for_refinement = False
    for file in os.listdir(peng_plot_output_directory):
        if any([file.startswith(x) for x in selected_motifs]):
            min_requirement_for_refinement = True
            print("copying: ", file)
            shutil.copy(os.path.join(peng_plot_output_directory, file), os.path.join(peng_save_directory, file))
    return min_requirement_for_refinement


def upload_example_fasta(job_pk):
    job = get_object_or_404(Peng, pk=job_pk)
    out_filename = "ExampleData.fasta"
    with open(settings.EXAMPLE_FASTA) as fh:
        job.fasta_file.save(out_filename, File(fh))
        job.save()
    print(job.fasta_file.name)


def read_bmscore(fname):
    scores = {}
    with open(fname, newline='') as f:
        reader = csv.DictReader(f, dialect=csv.excel_tab)
        for row in reader:
            scores[row['motif_number']] = row
    return scores

def merge_meme_and_bmscore(meme_list, meme_list_old, bm_scores):
    # first we need to match ausfc scores with the memes from peng
    for i in range(1, len(meme_list_old) + 1):
        meme_list_old[i-1].ausfc = float(bm_scores[str(i)]['ausfc'])
        meme_list_old[i-1].motif_number = i
    meme_dict = {meme_list_old[i].meme_id: meme_list_old[i] for i in range(len(meme_list_old))}
    # now we need to macth the peng memes with the filterpwm meme
    for i, meme in enumerate(meme_list):
        meme.ausfc = meme_dict[meme.meme_id].ausfc
        #meme.motif_number = meme_dict[meme.meme_id].motif_number
        meme.motif_number = i+1
    return meme_list

def rename_bamms(target_dir, input_file):
    bamm_file_prefix = os.path.splitext(os.path.basename(input_file))[0]
    meme_list = Meme.fromfile(input_file)
    for i, meme in enumerate(meme_list):
        bamm_name = os.path.join(target_dir, bamm_file_prefix + "_motif_%s.ihbcp" %(i+1))
        bamm_name_new = os.path.join(target_dir, meme.meme_id + ".ihbcp")
        os.rename(bamm_name, bamm_name_new)
        bamm_name = os.path.join(target_dir, bamm_file_prefix + "_motif_%s.ihbp" %(i+1))
        bamm_name_new = os.path.join(target_dir, meme.meme_id + ".ihbp")
        os.rename(bamm_name, bamm_name_new)


def rename_and_move_plots(directory, new_dir):
    plots = [x for x in os.listdir(directory) if x.endswith(".png")]
    for plot in plots:
        print('plot', plot)
        if plot.endswith(BAMMPLOT_SUFFIX_REV):
            new_file = plot.replace(BAMMPLOT_SUFFIX_REV, '') + '_revComp.png'
        elif plot.endswith(BAMMPLOT_SUFFIX):
            new_file = plot.replace(BAMMPLOT_SUFFIX, '') + '.png'
        else:
            continue
        old_name = os.path.join(directory, plot)
        new_name = os.path.join(new_dir, new_file)
        print('old', old_name)
        print('new', new_name)
        os.rename(old_name, new_name)


def zip_bamm_motifs(motif_ids, directory, with_reverse=True):
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
            additional_args = os.path.join(directory, motif + "_revComp.png")
            cmd.append(additional_args)
            # Use -j option to prune directory prefixes
        subprocess.run(cmd)
    # Now zip all
    plots = [os.path.join(directory, x) for x in os.listdir(directory) if x.endswith(".png") or x.endswith(".meme")]
    # Add meme file
    plots.append(os.path.join(directory.rsplit('/', maxsplit=1)[0], MEME_OUTPUT_FILE))
    archive_name = os.path.join(directory, ZIPPED_MOTIFS)
    cmd = ['zip', '-j', archive_name] + plots
    # cmd = "zip -j %s %s" % (archive_name, plots)
    # print(cmd)
    subprocess.run(cmd)


