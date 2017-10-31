from django.core.management.base import BaseCommand
from bammmotif.models import ChIPseq, DbParameter

from uuid import UUID
from pandas import DataFrame
import os

class Command(BaseCommand):
    args = '<location> of BaMMresults' + '<info_file> containing meta information of the dataset'
    help = 'adding encode results to the database'

    def add_arguments(self, parser):
      parser.add_argument('location', type=str)
      parser.add_argument('info_file', type=str)

    def handle(self, *args, **options):
      
      # 1. create DbParameter_entry for this Dataset:
      db_param = DbParameter(
        param_id               = 100,
        data_source            = 'ENCODE',
        species                = 'human',
        experiment             = 'ChIPseq',
        base_dir               = 'ENCODE_ChIPseq',
        motif_init_file_format = 'fasta',
        alphabet               = 'STANDARD',
        reversecomp            = True,
        modelorder             = 4,
        extend_1               = 4,
        extend_2               = 4,
        bgmodelorder           = 2,
        em                     = True,
        maxemiterations        = 1e5,
        epsilon                = 0.0010,
        fdr                    = True,
        mfold                  = 10,
        cvfold                 = 5,  
        samplingorder          = 2,
        savelogodds            = True,
        cgs                    = False,
        maxcgsiterations       = 1e5,
        noalphasampling        = True,
        location               = '/code/DB/ENCODE_ChIPseq/Results'
        )
      db_param.save()

      # 2. read info table
      info_table = DataFrame.from_csv(options['info_file'], sep="\t")
      
      # 3. insert new entries into database
      for i in range(1,len(info_table)+1):

        # check that entry has result folder in 'location' 
        if os.path.exists(str(options['location']) + '/' + db_param.base_dir + '/Results/' + info_table['FILENAME'][i] + '_summits125' + '/'):
          new_entry = ChIPseq(
            filename        = info_table['FILENAME'][i],
            lab             = info_table['LAB'][i],
            grant           = info_table['GRANT'][i],
            cell_type       = info_table['CELLTYPE'][i],
            target_name     = info_table['HGNC TARGET NAME'][i],
            ensembl_target_id = info_table['ENSEMBL TARGET ID'][i],
            treatment       = info_table['TREATMENT'][i],
            protocol        = info_table['PROTOCOL'][i],
            pos_seq_file    = str(options['location']) + '/' + db_param.base_dir + '/Source/Sequences/' + info_table['FILENAME'][i] + '_summits125' + '.fasta',
            motif_init_file = str(options['location']) + '/' + db_param.base_dir + '/Source/BindingSiteFiles/' + info_table['FILENAME'][i] + '_summits102' + '_restr5000' + '.blocks' ,
            result_location = info_table['FILENAME'][i] + '_summits125' ,
            parent          = db_param,
            )
          new_entry.save()
