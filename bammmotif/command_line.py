from collections import OrderedDict
import subprocess
import sys
import os
import shutil


class CommandlineModule:
    def __init__(self, command_name, config):
        cmd_flag_templates = OrderedDict()
        options = OrderedDict()
        for option_name, flag_template in config:
            options[option_name] = None
            cmd_flag_templates[option_name] = flag_template

        self._command_name = command_name
        self._cmd_flag_templates = cmd_flag_templates
        self._options = options
        self._initialized = True

    def __setattr__(self, name, value):
        if '_initialized' not in self.__dict__:
            super().__setattr__(name, value)
        elif name in self._options:
            self._options[name] = value
        else:
            raise OptionError('unknown option %r' % name)

    def __getattr__(self, name):
        if '_initialized' not in self.__dict__:
            return super().__getattr__(name)
        elif name in self._options:
            return self._options[name]
        elif name in self.__dict__:
            return super().__getattr__(name)
        else:
            raise OptionError('unknown option %r' % name)

    @property
    def command_tokens(self):
        cmd_tokens = [self._command_name]
        for option_name, option_value in self._options.items():
            if option_value is None:
                continue
            flag_tmpl = self._cmd_flag_templates[option_name]
            if flag_tmpl is not None:
                cmd_tokens.append(flag_tmpl)
            if isinstance(option_value, str):
                cmd_tokens.append('%s' % option_value)
            elif isinstance(option_value, bool):
                if not option_value:
                    del cmd_tokens[-1]
                    # cmd_tokens.append('%s' % option_value)
            elif isinstance(option_value, list):
                for item in option_value:
                    if isinstance(item, str):
                        cmd_tokens.append('%s' % item)
                    else:
                        cmd_tokens.append(str(item))
            else:
                cmd_tokens.append(str(option_value))
        return cmd_tokens

    @property
    def options(self):
        return self._options

    @property
    def defaults(self):
        return self._defaults

    def run(self, **kw_args):
        extra_args = {
            'universal_newlines': True
        }
        extra_args.update(kw_args)
        print("Command line tokens")
        print(self.command_tokens)
        print(os.getcwd())
        return subprocess.run(self.command_tokens, **extra_args)


class OptionError(ValueError):
    pass


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
        'meme_output': 'out.meme',
        'json_output': 'out.json',
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
        if not os.path.exists(self.options['temp_dir']):
            os.mkdir(self.options['temp_dir'])

    def remove_temp_directory(self):
        shutil.rmtree(self.options['temp_dir'])

    @classmethod
    def from_job(cls, peng_job):
        spm = cls()
        for key, val in peng_job.__dict__.items():
            if key in spm.options and val:
                spm.options[key] = val

        print("PENG_JOB")
        print(peng_job.__dict__)
        print("SPM")
        print(spm.__dict__)
        return spm

    def run(self, **kw_args):
        self.create_temp_directory()
        super().run(**kw_args)
        self.remove_temp_directory()

class ValidateFasta(CommandlineModule):
    def __init__(self):
        pass


class BammMatch(CommandlineModule):
    def __init__(self):
        pass

class FDRPlotSimple(CommandlineModule):
    def __init__(self):
        pass

class PlotHOBindingSitesLogo(CommandlineModule):
    def __init__(self):
        pass

def zip_files(zipname, file_list):
    zipcmd = 'zip %s %s' % (zipname, " ".join(file_list))
    process = subprocess.Popen(zipcmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ret = process.communicate()
    if process.returncode != 0:
        return False
    sys.stdout.write(ret[0].decode('ascii'))
    return True

def execute_command_get_bg_model_order(params, job):
    command = 'python3 /code/bammmotif/static/scripts/getbgModelOrder.py ' + params
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ret = process.communicate()
    # TODO: What to do if check fails?
    if process.returncode != 0:
        pass
    sys.stdout.write(ret[0].decode('ascii'))
    bg_order = [int(x) for x in ret[0].strip().decode('ascii').split()]
    for val in bg_order:
        job.backgroud_Order = val
        job.save()
        print("BG order = " + str(job.background_Order) + "\n")
        sys.stdout.flush()
    process.wait()
    return job
