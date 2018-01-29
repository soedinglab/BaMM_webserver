JOB_INPUT_DIRECTORY = 'Input'
JOB_OUTPUT_DIRECTORY = 'Output'
PENG_OUTPUT = 'pengoutput'
PENG_INPUT = 'Input'
PENG_TEMP_DIRECTORY = "temp"
SELECTED_MOTIFS = 'selected_motifs'
MEME_PLOT_DIRECTORY = 'meme_plots'
MEME_OUTPUT_FILE = 'out.meme'
MOTIF_SELECT_IDENTIFIER = "_select"
JSON_OUTPUT_FILE = "out.json"
BMSCORE_SUFFIX = ".bmscore"
PENG_PLOT_LOGO_ORDER = 0

PENG_OUTPUT_MEME = 'out.meme' # replace MEME_OUTPUT_FILE
PENG_OUTPUT_JSON = 'out.json' # replace JSON_OUTPUT_FILE
PWM2BAMM_DIRECTORY = 'converttemp'
BAMMPLOT_SUFFIX_STAMP = '-logo-order-0_stamp.png'
BAMMPLOT_SUFFIX_REV_STAMP = '-logo-order-0_stamp_revComp.png'
BAMMPLOT_SUFFIX = '-logo-order-0.png'
BAMMPLOT_SUFFIX_REV = '-logo-order-0_revComp.png'


#Filter PWM
PATH_TO_FILTERPWM_SCRIPT = '/ext/filterPWMs/filterPWM.py'
FILTERPWM_INPUT_FILE = MEME_OUTPUT_FILE
#Overwrite for now
FILTERPWM_OUTPUT_FILE = 'out_filtered.meme'

#Meme plotting
MEME_PLOT_INPUT = FILTERPWM_OUTPUT_FILE

FASTA_VALIDATION_SCRIPT = '/code/bammmotif/static/scripts/valid_fasta'
ZIPPED_MOTIFS = 'motif_all.zip'
EXAMPLE_FASTA_FILE = 'ExampleData.fasta'

#ERROR MESSAGES
NOT_ENOUGH_MOTIFS_SELECTED_FOR_REFINEMENT = "Please select at least one motif to start refinement!"

# models related variables
ALLOWED_JOBMODES = [
    "peng",
]

# Use this from now on. These should replace the over functions over time.

# Only use the following functions temporary.

# END



