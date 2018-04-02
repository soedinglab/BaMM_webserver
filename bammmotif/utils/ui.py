from collections import defaultdict

from django import forms
from ..models import MotifDatabase


class DBChoiceField(forms.ModelChoiceField):

    def __init__(self):
        dbs = MotifDatabase.objects.all().order_by('display_name')
        super().__init__(queryset=dbs, empty_label=None)

    def label_from_instance(self, obj):
        return obj.display_name


HELP_TEXTS = defaultdict(str, {
    'job_name': (
        'You can give your job a name to better distinguish between multiple runs.'
    ),
    'Input_Sequences': (
        'A fasta file with bound sequences.'
    ),
    'reverse_Complement': 'When checked, motifs can be both on the plus and minus strand.',
    'model_order': 'The order of the BaMM. A model of order 0 corresponds to a PWM model.',
    'extend': (
        'Extends the motif by adding extra positions to the left and right of the initializer '
        'motif. If the initializer only consists of the informative core motif, enlarging the '
        'motif allows to also learn the flanking regions.'
    ),
    'background_Order': (
        'The order for the background model. We recommend a background order of 2 for a '
        'realistic model of the genomic input. For very short motifs a background order of 1 '
        'or even 0 may be required to find the motif.'
    ),
    'Background_Sequences': (
        'A fasta file with sequences that represent the genomic background of the input '
        'sequences. If not provided, the background is estimated from the input sequences.'
    ),
    'score_Seqset': (
        'Scan the input sequences for motif occurences. Required for plotting '
        'motif localization.'
    ),
    'score_Cutoff': (
        'Only motif positions with an e-value smaller than this will be reported as '
        'binding positions.'
    ),
    'FDR': (
        'Evaluate the performance of the motif on the input set. Required for plotting '
        'performance plots.'
    ),
    'motif_db': 'Motif database used for annotating trained models.',
    'p_value_cutoff': (
        'The p-value limit will be used to define a threshold for motif comparisons '
        'between the inserted model and the database.'
    ),
    'pattern_length': 'Length of patterns to be searched.',
    'zscore_threshold': (
        'Patterns with a z-score threshold lower than this will not be considered.'
    ),
    'count_threshold': (
        'Patterns with less than this amount of counts will not be considered.'
    ),
    'objective_function': (
        'The scoring function used for the optimization to IUPAC patterns.'
    ),
    'no_em': (
        'When checked, the Expectation Maximization step will be skipped.'
    ),
    'max_refined_motifs': (
        'Maximum number of seed motifs that will be refined with the BaMM algorithm.'
    ),
})

# defining aliases
HELP_TEXTS['fasta_file'] = HELP_TEXTS['Input_Sequences']
HELP_TEXTS['bg_sequences'] = HELP_TEXTS['Background_Sequences']
HELP_TEXTS['bg_model_order'] = HELP_TEXTS['background_Order']
