import sys
import logging

from django.core.management.base import BaseCommand

from bammmotif.test.test_regressions import run_tests, list_tests


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--tests', nargs='+', default=[])
        parser.add_argument('--list', action='store_true')

    def handle(self, *args, **options):
        setup_logger()
        if options['list']:
            list_tests()
            return
        run_tests(options['tests'])


def setup_logger():
    formatter = logging.Formatter('|%(levelname)s| %(message)s')
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger = logging.getLogger('bammmotif.test')
    logger.addHandler(handler)
    return logger
