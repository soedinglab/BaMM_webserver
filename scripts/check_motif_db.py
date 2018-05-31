import argparse
import sys
import os
from os import path

import yaml


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('motif_db')
    parser.add_argument('--pwm_db', action='store_true')
    return parser


class ValidationError(Exception):
    pass


def main():
    parser = create_parser()
    args = parser.parse_args()
    is_pwm_db = args.pwm_db

    for db_file in os.listdir(args.motif_db):
        if path.isfile(db_file):
            print('Unexpected file %r' % db_file, file=sys.stderr)
            sys.exit(1)
        else:
            try:
                check_if_valid_motif_db(path.join(args.motif_db, db_file), is_pwm_db)
            except ValidationError as e:
                print(str(e), 'in database %s' % db_file, file=sys.stderr)
                sys.exit(1)


MANDATORY_FILES = ['database_config.yaml', 'model_specifications.yaml', 'motifs.yaml']
MANDATORY_DIRS = ['models']
MOTIF_FILE_EXTENSIONS = [
    '.ihbcp',
    '-logo-order-0.png',
    '-logo-order-0_revComp.png',
    '-logo-order-0_stamp.png',
    '-logo-order-0_stamp_revComp.png',
]
FILE_EXTENSIONS = ['.hbcp']


def check_if_valid_motif_db(db, is_pwm_db):
    for file in MANDATORY_FILES:
        if not path.isfile(path.join(db, file)):
            raise ValidationError('Missing file %s' % file)

    for dir in MANDATORY_DIRS:
        if not path.isdir(path.join(db, dir)):
            raise ValidationError('Missing directory %s' % dir)

    check_motif_file_existance(db, is_pwm_db)


def check_motif_file_existance(db, is_pwm_db):
    model_descr_file = path.join(db, 'motifs.yaml')
    with open(model_descr_file, 'r') as stream:
        try:
            motif_models = yaml.load(stream)['models']
        except yaml.YAMLError:
            raise ValidationError('malformed model description file')

        defined_models = set()
        for model in motif_models:
            filename = model['filename']
            defined_models.add(filename)

            for ext in MOTIF_FILE_EXTENSIONS:
                motif_basename = '%s_motif_1%s' % (filename, ext)
                motif_filepath = path.join(db, 'models', filename, motif_basename)
                if not path.isfile(motif_filepath):
                    raise ValidationError('Missing mandatory file %s' % motif_filepath)

            if not is_pwm_db:
                for ext in FILE_EXTENSIONS:
                    motif_filepath = path.join(db, 'models', filename, filename + ext)
                    if not path.isfile(motif_filepath):
                        raise ValidationError('Missing mandatory file %s' % motif_filepath)

        model_dir = path.join(db, 'models')
        print(len(os.listdir(model_dir)))
        print(len(defined_models))
        for motif in os.listdir(model_dir):
            if motif not in defined_models:
                raise ValidationError('model %s not registered' % motif)


if __name__ == '__main__':
    main()
