from bammmotif.test.test_regressions import run_tests, list_tests
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    
    def add_arguments(self, parser):
        parser.add_argument('--tests', nargs='+', default=[])
        parser.add_argument('--list', action='store_true')

    def handle(self, *args, **options):
        if options['list']:
            list_tests()
            return
        run_tests(options['tests'])
