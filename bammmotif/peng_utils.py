import subprocess

def get_motif_ids(fpath):
    with open(fpath) as f:
        lines = f.readlines()
        motif_ids = [x.rsplit()[-1] for x in lines if x.startswith("MOTIF")]
    return motif_ids

def plot_meme_output(tfile, motif, meme_file):
    # target_file = os.path.join(tpath, motif + ".png")
    command = "ceqlogo -i %s -f PNG -m %s -o %s" %(meme_file, motif, tfile)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(command)
    process.wait()
