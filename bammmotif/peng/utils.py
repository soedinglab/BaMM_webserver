import os
from os import path
import shutil
import subprocess
import logging
import csv
import re

from django.shortcuts import get_object_or_404
from django.core.files import File
from django.conf import settings

from ..utils.meme_reader import meme_drop_unselected_motifs, Meme
from ..utils import (
    get_job_output_folder,
    get_job_input_folder,
)
from bammmotif.peng.io import (
    peng_meme_directory,
    get_temporary_job_dir,
    get_bmscore_filename,
    get_motif_init_file
)

from .settings import (
    MEME_PLOT_DIRECTORY,
    MEME_OUTPUT_FILE,
    PENG_OUTPUT,
    SELECTED_MOTIFS,
    ZIPPED_MOTIFS,
    MOTIF_SELECT_IDENTIFIER,
    EXAMPLE_FASTA_FILE,
    FILTERPWM_OUTPUT_FILE,
    peng_meme_directory,
    BAMMPLOT_SUFFIX,
    BAMMPLOT_SUFFIX_REV,
    BAMMPLOT_SUFFIX_REV_STAMP,
    BAMMPLOT_SUFFIX_STAMP,
    BAMM_MOTIF_INIT_FILE,
)

from .models import PengJob
from webserver.settings import BAMM_INPUT

logger = logging.getLogger(__name__)


def upload_example_fasta_for_peng(job):
    out_filename = EXAMPLE_FASTA_FILE
    with open(settings.EXAMPLE_FASTA) as fh:
        job.fasta_file.save(out_filename, File(fh))


def copy_peng_to_bamm(peng_id, bamm_id, post):
    bamm_output_dir = path.join(get_job_output_folder(bamm_id), PENG_OUTPUT)
    bamm_plot_output_directory = path.join(bamm_output_dir, MEME_PLOT_DIRECTORY)
    if not path.exists(bamm_plot_output_directory):
        os.makedirs(bamm_plot_output_directory)

    # copy meme.out
    meme_path_src = os.path.join(peng_meme_directory(peng_id), MEME_OUTPUT_FILE)
    meme_path_dst = get_motif_init_file(str(bamm_id))
    selected_motifs = get_selected_motifs(post)
    meme_drop_unselected_motifs(meme_path_src, meme_path_dst, selected_motifs)

    # copy results of filterPWM
    filterpwm_src = os.path.join(get_job_output_folder(peng_id), FILTERPWM_OUTPUT_FILE)

    logger.debug('copying %s -> %s', filterpwm_src, bamm_output_dir)
    shutil.copy(filterpwm_src, bamm_output_dir)

    # copy input file
    peng_input = os.path.join(get_job_input_folder(peng_id))
    bamm_input = os.path.join(get_job_input_folder(bamm_id))
    if not path.exists(bamm_input):
        os.makedirs(bamm_input)
    # TODO: Is this supposed to be multiple files??
    for file in os.listdir(peng_input):
        logger.debug('copying %s -> %s', filterpwm_src, bamm_output_dir)
        src = os.path.join(peng_input, file)
        shutil.copy(src, bamm_input)


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


def get_selected_motifs(post_data):
    motif_ids = []
    for motif_key in (x for x in post_data.keys() if x.endswith(MOTIF_SELECT_IDENTIFIER)):
        motif_ids.append(motif_key.replace(MOTIF_SELECT_IDENTIFIER, ''))
    return motif_ids


def save_selected_motifs(post_data, peng_pk, bamm_pk):
    peng_plot_output_directory = path.join(peng_meme_directory(peng_pk), MEME_PLOT_DIRECTORY)
    peng_save_directory = path.join(peng_meme_directory(bamm_pk), SELECTED_MOTIFS)
    if not path.exists(peng_save_directory):
        os.makedirs(peng_save_directory)

    selected_motif_ids = set(get_selected_motifs(post_data))

    split_pat = re.compile(r'[^a-zA-Z]')
    for file in os.listdir(peng_plot_output_directory):
        motif, *_ = re.split(split_pat, path.basename(file))
        if motif in selected_motif_ids:
            src = path.join(peng_plot_output_directory, file)
            dest = path.join(peng_save_directory, file)
            logger.debug('copying %s -> %s', src, dest)
            shutil.copy(src, dest)


def upload_example_fasta(job_pk):
    job = get_object_or_404(PengJob, pk=job_pk)
    out_filename = "ExampleData.fasta"
    with open(settings.EXAMPLE_FASTA) as fh:
        job.fasta_file.save(out_filename, File(fh))
        job.save()
    print(job.fasta_file.name)

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
        if plot.endswith(BAMMPLOT_SUFFIX_REV_STAMP):
            new_file = plot.replace(BAMMPLOT_SUFFIX_REV_STAMP, '') + '_revComp.png'
        elif plot.endswith(BAMMPLOT_SUFFIX_STAMP):
            new_file = plot.replace(BAMMPLOT_SUFFIX_STAMP, '') + '.png'
        elif plot.endswith(BAMMPLOT_SUFFIX):
            new_file = plot.replace(BAMMPLOT_SUFFIX, '_zip') + '.png'
        elif plot.endswith(BAMMPLOT_SUFFIX_REV):
            new_file = plot.replace(BAMMPLOT_SUFFIX_REV, '_revComp_zip') + '.png'
        else:
            continue
        old_name = os.path.join(directory, plot)
        new_name = os.path.join(new_dir, new_file)
        os.rename(old_name, new_name)


def zip_bamm_motifs(motif_ids, directory, with_reverse=True):
    for motif in motif_ids:
        cmd = ['zip']
        cmd.append('-j')
        archive_name = os.path.join(directory, motif + ".zip")
        if os.path.exists(archive_name):
            os.remove(archive_name)
        cmd.append(archive_name)
        args = os.path.join(directory, motif + "_zip.png")
        cmd.append(args)
        # Now add meme file
        meme_file = os.path.join(directory, motif + ".meme")
        cmd.append(meme_file)
        if with_reverse:
            additional_args = os.path.join(directory, motif + "_revComp_zip.png")
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

def copy_bmscores(peng_id, bamm_id):
    bamm_input = get_job_input_folder(str(bamm_id))
    bmf_path = os.path.join(get_temporary_job_dir(peng_id), get_bmscore_filename(peng_id))
    shutil.copy(bmf_path, bamm_input)

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
    for i, meme in enumerate(meme_list, start=1):
        meme.ausfc = meme_dict[meme.meme_id].ausfc
        meme.motif_number = i
    return meme_list

