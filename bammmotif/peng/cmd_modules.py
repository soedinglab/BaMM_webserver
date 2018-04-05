import os
from os import path
import shutil

from .settings import (
    MEME_OUTPUT_FILE,
    JSON_OUTPUT_FILE,
    FILTERPWM_INPUT_FILE,
    FILTERPWM_OUTPUT_FILE,
    PATH_TO_FILTERPWM_SCRIPT,
    ZIPPED_MOTIFS,
)
from ..utils.commandline import CommandlineModule
from ..command_line import transfer_options


class ShootPengModule(CommandlineModule):

    objective_functions = [
        'LOGPVAL',
        'MUTUAL_INFO',
        'ENRICHMENT',
    ]
    defaults = {
        'pattern_length': 10,
        'zscore_threshold': 10,
        'count_threshold': 5,
        'bg_model_order': 2,
        'strand': 'BOTH',
        'optimization_score': 'MUTUAL_INFO',
        'enrich_pseudocount_factor': 0.005,
        'no_em': False,
        'em_threshold': 0.08,
        'em_max_iterations': 20,
        'no_merging': False,
        'bit_factor_threshold': 0.4,
        'use_default_pwm': False,
        'pwm_pseudo_counts': 10,
        'n_threads': 1,
        'em_saturation_threshold': 1E4,
        'silent': True,
        'temp_dir': 'temp',
        'bg_sequences': None
    }

    def __init__(self):
        config = [
            ('fasta_file', None),
            ('meme_output', '-o'),
            ('json_output', '-j'),
            ('temp_dir', '-d'),
            ('bg_sequences', '--background-sequences'),
            ('pattern_length', '-w'),
            ('zscore_threshold', '-t'),
            ('count_threshold', '--count-threshold'),
            ('bg_model_order', '--bg-model-order'),
            ('strand', '--strand'),
            ('objective_function', '--optimization_score'),
            ('enrich_pseudocount_factor', '--enrich_pseudocount_factor'),
            ('no_em', '--no-em'),
            ('em_saturation_threshold', '-a'),
            ('em_threshold', '--em-threshold'),
            ('em_max_iterations', '--em-max-iterations'),
            ('no_merging', '--no-merging'),
            ('bit_factor_threshold', '-b'),
            ('use_default_pwm', '--use-default-pwm'),
            ('pwm_pseudo_counts', '--pseudo-counts'),
            ('n_threads', '--threads'),
            ('silent', '--silent'),
        ]
        # Build temp directory
        super().__init__('shoot_peng.py', config)

    def create_temp_directory(self):
        if not path.exists(self.options['temp_dir']):
            os.mkdir(self.options['temp_dir'])

    def remove_temp_directory(self):
        shutil.rmtree(self.options['temp_dir'])

    @classmethod
    def from_job(cls, peng_job):
        spm = cls()
        transfer_options(peng_job, spm)
        return spm

    def run(self, **kw_args):
        self.create_temp_directory()
        super().run(**kw_args)


class FilterPWM(CommandlineModule):

    defaults = {
        'model_db': None,
        'n_neg_perm': 10,
        'highscore_fraction': 0.1,
        'evalue_threshold': 0.1,
        'seed': 42,
        'min_overlap': 2,
        'output_score_file': None
    }

    #TODO: Make this a little bit more flexible.
    def __init__(self):
        config = [
            ('input_file', None),
            ('output_file', None),
            ('model_db', '--model_db'),
            ('n_neg_perm', '--n_neg_perm'),
            ('highscore_fraction', '--highscore_fraction'),
            ('evalue_threshold', '--evalue_threshold'),
            ('seed', '--seed'),
            ('min_overlap', '--min_overlap'),
            ('n_processes', '--n_processes'),
            ('output_score_file', '--output_score_file')
        ]
        super().__init__(['python', PATH_TO_FILTERPWM_SCRIPT], config)
        self._load_defaults()
        #self._set_directory(directory)

    def _load_defaults(self):
        for key, val in self.defaults.items():
            self.options[key] = val


class PlotMeme(CommandlineModule):

    defaults = {
        'output_file_format': 'PNG',
        'reverse_complement': False,
    }

    def __init__(self):
        config = [
            ('input_file', '-i'),
            ('output_file_format', '-f'),
            ('motif_id', '-m'),
            ('output_file', '-o'),
            ('reverse_complement', '-r')
        ]
        super().__init__('ceqlogo', config)

    @classmethod
    def from_dict(cls, options):
        pm = cls()
        for key, val in options.items():
            if key in pm.options:
                pm.options[key] = val
        return pm

    @staticmethod
    def plot_meme_list(motifs, input_file, output_directory):
        meme_plotter = PlotMeme()
        meme_plotter.output_file_format = PlotMeme.defaults['output_file_format']
        for motif in motifs:
            meme_plotter.input_file = input_file
            meme_plotter.motif_id = motif
            meme_plotter.output_file = os.path.join(output_directory, motif + ".png")
            meme_plotter.reverse_complement = False
            meme_plotter.run()
            # Now plot reverse complement
            meme_plotter.output_file = os.path.join(output_directory, motif + "_rev.png")
            meme_plotter.reverse_complement = True
            meme_plotter.run()


class ZipMotifs(CommandlineModule):

    defaults = {
        'strip_filepath': True,
    }

    def __init__(self):
        config = [
            ('strip_filepath', '-j'),
            ('argslist', None),
        ]
        super().__init__('zip', config)

    def run(self):
        super().run()

    @staticmethod
    def zip_motifs(motif_ids, directory, with_reverse=True):
        for motif in motif_ids:
            archive_name = os.path.join(directory, motif + '.zip')
            if os.path.exists(archive_name):
                os.remove(archive_name)
            argslist = [archive_name]
            argslist.append(os.path.join(directory, motif + "_zip.png"))
            argslist.append(os.path.join(directory, motif + ".meme"))
            if with_reverse:
                argslist.append(os.path.join(directory, motif + "_revComp_zip.png"))
            zm = ZipMotifs()
            zm.strip_filepath = ZipMotifs.defaults['strip_filepath']
            zm.argslist = argslist
            zm.run()
        archive_name = os.path.join(directory, ZIPPED_MOTIFS)
        argslist = [archive_name]
        plots = [os.path.join(directory, x) for x in os.listdir(directory) if x.endswith(".png") or x.endswith(".meme")]
        plots.append(os.path.join(directory.rsplit('/', maxsplit=1)[0], MEME_OUTPUT_FILE))
        argslist += plots
        zm = ZipMotifs()
        zm.strip_filepath = ZipMotifs.defaults['strip_filepath']
        zm.argslist = argslist
        zm.run()
