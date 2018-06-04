from collections import OrderedDict
import subprocess
import logging

from .misc import ignore_sigterm

logger = logging.getLogger(__name__)


class CommandlineModule:
    def __init__(self, command_name, config, defaults={}, enforce_exit_zero=True):
        cmd_flag_templates = OrderedDict()
        options = OrderedDict()
        for option_name, flag_template in config:
            option_value = None
            if option_name in defaults:
                option_value = defaults[option_name]
            options[option_name] = option_value
            cmd_flag_templates[option_name] = flag_template

        self._command_name = command_name
        self._cmd_flag_templates = cmd_flag_templates
        self._options = options
        self._with_log_file = None
        # This should bt the last line in this Method.
        self._enforce_exit_zero = enforce_exit_zero
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
        elif name.startswith('_') or name in self.__dict__:
            return super().__getattr__(name)
        else:
            raise OptionError('unknown option %r' % name)

    @property
    def command_tokens(self):
        if isinstance(self._command_name, str):
            cmd_tokens = [self._command_name]
        else:
            cmd_tokens = list(self._command_name)

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
    def with_log_file(self):
        return super().__getattribute__("_with_log_file")

    def set_log_file(self, val):
        if isinstance(val, (type(None), str)):
            super().__setattr__("_with_log_file", val)

    @property
    def options(self):
        return self._options

    @property
    def defaults(self):
        return self._defaults

    def run(self, **kw_args):
        extra_args = {
            'universal_newlines': True,
            'preexec_fn': ignore_sigterm,
        }
        extra_args.update(kw_args)

        logger.debug("executing: %s",  ' '.join(self.command_tokens))
        if self.with_log_file is not None:
            with open(self.with_log_file, "a") as f:
                proc = subprocess.run(self.command_tokens, stdout=f, stderr=f, **extra_args)
        else:
            proc = subprocess.run(self.command_tokens, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, **extra_args)
        if proc.returncode != 0:
            if self._enforce_exit_zero:
                raise CommandFailureException(' '.join(self.command_tokens))

        return proc


class OptionError(ValueError):
    pass


class CommandFailureException(Exception):
    pass
