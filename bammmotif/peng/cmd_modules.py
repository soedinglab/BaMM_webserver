import os
from os import path
import shutil

from .settings import (
    MEME_OUTPUT_FILE,
    JSON_OUTPUT_FILE,
    FILTERPWM_INPUT_FILE,
    FILTERPWM_OUTPUT_FILE,
    PATH_TO_FILTERPWM_SCRIPT,
)
from ..utils.commandline import CommandlineModule
from ..command_line import transfer_options


class ShootPengModule(CommandlineModule):

    defaults = {
        'pattern_length': 10,
        'zscore_threshold': 10,
        'count_threshold': 1,
        'bg_model_order': 2,
        'strand': 'BOTH',
        'iupac_optimization_score': 'LOGPVAL',
        'enrich_pseudocount_factor': 0.005,
        'no_em': True,
        'em_threshold': 0.08,
        'em_max_iterations': 100,
        'no-merging': True,
        'bit_factor_threshold': 0.4,
        'use_default_pwm': False,
        'pwm_pseudo_counts': 10,
        'n_threads': 1,
        'em_saturation_threshold': 1E4,
        'silent': True,
        'meme_output': MEME_OUTPUT_FILE,
        'json_output': JSON_OUTPUT_FILE,
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
            ('objective_function', '--iupac_optimization_score'),
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
        self.remove_temp_directory()


class FilterPWM(CommandlineModule):

    defaults = {
        'input_file': FILTERPWM_INPUT_FILE,
        'output_file': FILTERPWM_OUTPUT_FILE,
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

        #def _set_directory(self, directory):
    #    self.input_file = os.path.join(directory, self.defaults['input_file'])
    #    self.output_file = os.path.join(directory, self.defaults['output_file'])

    @classmethod
    def init_with_extra_directory(cls, directory):
        obj = cls()
        obj.input_file = os.path.join(directory, FilterPWM.defaults['input_file'])
        obj.output_file = os.path.join(directory, FilterPWM.defaults['output_file'])
        return obj


class PlotMeme(CommandlineModule):

    defaults = {
        'output_file_format': 'PNG',
        'reverse_complement': False
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
