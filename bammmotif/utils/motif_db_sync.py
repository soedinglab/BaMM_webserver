import logging
import os
from os import path

import yaml


logger = logging.getLogger()


def sync_databases(database_dir):
    loaded_databases = get_loaded_databases()
    available_databases = get_available_databases(database_dir)

    new_db, del_db, upd_db, cur_db = check_db_status(loaded_databases, available_databases)

    for motif_db in cur_db:
        logger.info('motif database %r at version %s up-to-date', motif_db.db_id, motif_db.version)

    for motif_db in new_db:
        load_motif_db(database_dir, motif_db)
        logger.info('loaded motif database %r at version %s', motif_db.db_id, motif_db.version)

    for motif_db in del_db:
        unload_motif_db(motif_db)
        logger.info('unloaded motif database %r with version %s', motif_db.db_id, motif_db.version)

    for motif_db in upd_db:
        unload_motif_db(motif_db)
        load_motif_db(database_dir, motif_db)
        logger.info('updated motif database %r to version %s', motif_db.db_id, motif_db.version)


class MalformattedMotifDatabase:
    pass


def load_motif_db(database_dir, motif_db):
    config_file = path.join(database_dir, dir_node, 'database_config.yaml')
    with open(config_file) as yaml_config:
        try:
            db_config = yaml.load(yaml_config)
            motif_db_entry = MotifDatabase()
            for field in MotifDatabase._meta.get_fields():
                if field.name in db_config:
                    motif_db_entry.__setattr__(field.name, db_config[db_config[field.name]]) 
            motif_db_entry.name = motif_db.db_id
            motif_db_entry.save()
        except yaml.YAMLError as exc:
            raise MalformattedMotifDatabase(exc)


def unload_motif_db(motif_db):
    MotifDatabase.objects.get(name=motif_db.db_id).delete()


class MotifDatabaseDescriptor():

    def __init__(self, db_id, version):
        self._db_id = db_id
        self._version = version

    @property
    def version(self):
        return self._version

    @property
    def db_id(self):
        return self._db_id


def get_loaded_databases():
    motif_dbs = []
    for motif_db in MotifDatabase.objects.all():
        motif_dbs.append(MotifDatabaseDescriptor(motif_db.name, motif_db.version))
    return motif_dbs


def get_available_databases(database_dir):

    databases = []
    for dir_node in os.listdir(database_dir):
        if not path.isdir(dir_node):
            continue
        config_file = path.join(database_dir, dir_node, 'database_config.yaml')
        if not path.isfile(config_file):
            continue

        with open(config_file) as yaml_config:
            try:
                db_config = yaml.load(yaml_config)
                databases.append(MotifDatabaseDescriptor(dir_node, db_config['version']))
            except yaml.YAMLError as exc:
                logger.error(exc)
                continue
    return databases


def check_db_status(current_databases, available_databases):
    current_set = {db.db_id: db.version for db in current_databases}
    available_set = {db.db_id: db.version for db in current_databases}

    up_to_date_dbs = []
    update_dbs = []
    unload_dbs = []
    load_dbs = []
    for motif_db in available_databases:
        if motif_db.db_id in current_set:
            if motif_db.version == current_set[motif_db.db_id]:
                up_to_date_dbs.append(motif_db)
            else:
                update_dbs.append(motif_db)
        else:
            load_dbs.append(motif_db)

    for motif_db in current_set:
        if motif_db not in available_set:
            unload_dbs.append(motif_db)

    return load_dbs, unload_dbs, update_dbs, up_to_date_dbs