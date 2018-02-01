import os
from os import path
import shutil
import subprocess
import logging

from django.shortcuts import get_object_or_404
from django.core.files import File
from django.conf import settings

from ..utils.meme_reader import update_and_copy_meme_file
from ..utils import (
    get_job_output_folder,
    get_job_input_folder,
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
    JOB_OUTPUT_DIRECTORY,
    peng_meme_directory,
)

logger = logging.getLogger(__name__)


def upload_example_fasta_for_peng(job):
    out_filename = EXAMPLE_FASTA_FILE
    with open(settings.EXAMPLE_FASTA) as fh:
        job.fasta_file.save(out_filename, File(fh))


def copy_peng_to_bamm(peng_id, bamm_id, post):
    peng_save_directory = path.join(peng_meme_directory(peng_id), SELECTED_MOTIFS)
    bamm_output_dir = path.join(get_job_output_folder(bamm_id), PENG_OUTPUT)
    bamm_plot_output_directory = path.join(bamm_output_dir, MEME_PLOT_DIRECTORY)
    if not path.exists(bamm_plot_output_directory):
        os.makedirs(bamm_plot_output_directory)

    for file in os.listdir(peng_save_directory):
        src = path.join(peng_save_directory, file)
        dest = bamm_plot_output_directory
        logger.debug('copying %s -> %s', src, dest)
        shutil.copy(src, dest)

    # copy meme.out
    meme_path_src = os.path.join(peng_meme_directory(peng_id), MEME_OUTPUT_FILE)
    meme_path_dst = os.path.join(bamm_output_dir, MEME_OUTPUT_FILE)
    update_and_copy_meme_file(meme_path_src, meme_path_dst, peng_save_directory)

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


def save_selected_motifs(request, pk):
    peng_plot_output_directory = path.join(peng_meme_directory(pk), MEME_PLOT_DIRECTORY)
    peng_save_directory = path.join(peng_meme_directory(pk), SELECTED_MOTIFS)
    if not path.exists(peng_save_directory):
        os.makedirs(peng_save_directory)
    selected_motifs = [x.replace(MOTIF_SELECT_IDENTIFIER, "") for x in request.keys() if x.endswith(MOTIF_SELECT_IDENTIFIER)]
    min_requirement_for_refinement = False
    for file in os.listdir(peng_plot_output_directory):
        if any([file.startswith(x) for x in selected_motifs]):
            min_requirement_for_refinement = True
            src = path.join(peng_plot_output_directory, file)
            dest = path.join(peng_save_directory, file)
            shutil.copy(src, dest)
            logger.debug('copying %s -> %s', src, dest)
    return min_requirement_for_refinement


def upload_example_fasta(job_pk):
    job = get_object_or_404(Peng, pk=job_pk)
    out_filename = "ExampleData.fasta"
    with open(settings.EXAMPLE_FASTA) as fh:
        job.fasta_file.save(out_filename, File(fh))
        job.save()
    print(job.fasta_file.name)
