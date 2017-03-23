from django.core.management.base import BaseCommand
from bammmotif.models import ChIPseq, DbParameter

class Command(BaseCommand):
    args = '<foo bar ...>'
    help = 'adding encode results to the database'

    def add_arguments(self, parser):
      parser.add_argument('database', type=str)

    def _read_database(self,db_folder):
        entries = []
        return entries

    def handle(self, *args, **options):
#    db_public_id      = models.SmallIntegerField(db_column='db_public_ID', primary_key=True)  # Field name made lowercase.
#    filename          = models.CharField(max_length=255)
#    lab               = models.CharField(max_length=12)
#    grant             = models.CharField(max_length=12)
#    cell_type         = models.CharField(max_length=12)
#    target_name       = models.CharField(max_length=12)
#    ensembl_target_id = models.CharField(max_length=15)
#    treatment         = models.CharField(max_length=25)
#    protocol          = models.CharField(max_length=15)
#    pos_seq_file      = models.CharField(max_length=120)
#    motif_init_file   = models.CharField(max_length=120)
#    result_location   = models.CharField(max_length=80)
#    parent            = models.ForeignKey(DbParameter, blank=True, null=True, on_delete=models.CASCADE)

      entries = self._read_database(options['database'])
    
      #insert new entries
      for e in entries:
        new_entry = ChIPseq(db_public_id = e[0],
                            filename = e[1],
                            lab = e[2],
                            grant = e[3],
                            cell_type = e[4],
                            target_name = e[5],
                            ensembl_target_id = e[6],
                            treatment = e[7],
                            protocol = e[8],
                            pos_seq_file = e[9],
                            motif_init_file = e[10],
                            result_location = e[11])
        new_entry.save()




class Command(BaseCommand):
  help = 'adding proteins to the database'
  
  def add_arguments(self, parser):
    parser.add_argument('database', type=str)
    parser.add_argument('fasta_file', type=str)
    
  def _read_fasta(self, fasta_file):
    proteins = []
    with open(fasta_file) as fh:
      name = ""
      description = ""
      sequence = ""
      
      for line in fh:
        if len(line) > 0 and line[0] == ">":
          line = line.strip()
          if len(sequence) > 0:
            proteins.append((name, description, sequence))
            
          name = line[1:].split()[0]
          if name.find("|") > -1:
            name = line.split("|")[1]
            
          description = " ".join(line[1:].split()[1:])
          sequence = ""
        else:
          sequence += line
      
      if len(sequence) > 0:
        proteins.append((name, description, sequence))

    return proteins
    
  
  def handle(self, *args, **options):
#     protein_id = models.CharField(max_length=32, null=False)
#     db = models.CharField(max_length=25)
#     sequence = models.CharField(max_length=10000)
#     length = models.IntegerField(null=False, default=0)

    proteins = self._read_fasta(options['fasta_file'])
    database = options['database']
    
    #insert new entries
    for p in proteins:
      try:
        protein = Protein.objects.get(protein_id = p[0], db = database)
        protein.protein_id = p[0]
        protein.db = database
        protein.description = p[1]
        protein.sequence = p[2]
        protein.length = len(p[2])
        protein.save()
      except Protein.DoesNotExist:
        if len(p[2]) <= 10000:
          protein = Protein(protein_id = p[0], db = database, sequence = p[2], length = len(p[2]), description=p[1])
          protein.save()