import os
from bammmotif.peng.io import peng_meme_directory


class Meme(object):
    def __init__(self, meme_id, logpval, nsites):
        self.meme_id = meme_id
        self.number = None
        self._logpval = float(logpval)
        self.nsites = nsites
        self.select = False
        self._ausfc = None

    @property
    def logpval(self):
        return round(self._logpval, 3)

    @property
    def ausfc(self):
        return round(self._ausfc, 10)

    @logpval.setter
    def logpval(self, val):
        self._logpval = float(val)

    @ausfc.setter
    def ausfc(self, val):
        self._ausfc = float(val)

    @classmethod
    def fromdict(cls, meme_dict):
        return cls(
            meme_dict["meme_id"],
            meme_dict["log(Pval)"],
            meme_dict["nsites"],
        )



    @classmethod
    def fromfile(cls, fpath):
        meme_list = []
        with open(fpath) as f:
            fcont = f.read().split("\n\n")
            for elem in fcont:
                if not elem.startswith("MOTIF"):
                    continue
                meme_args = elem.split("\n")
                meme_property_dict = {}
                meme_property_dict["meme_id"] = meme_args[0].split(maxsplit=1)[1]
                letter_prop_mat = meme_args[1].replace("letter-probability-matrix:", "").split()
                for i in range(0, len(letter_prop_mat), 2):
                    prop = letter_prop_mat[i].replace("=", "")
                    meme_property_dict[prop] = letter_prop_mat[i+1]
                meme_list.append(Meme.fromdict(meme_property_dict))
        return meme_list


def split_meme_file(fpath, directory):
    with open(fpath) as f:
        fcont = f.read().split("\n\n")
        meme_header = "\n\n".join(fcont[:3])
        for elem in fcont:
            if not elem.startswith("MOTIF"):
                continue
            meme_id = elem.split("\n")[0].split(maxsplit=1)[1]
            fname = os.path.join(directory, meme_id + ".meme")
            with open(fname, "w") as d:
                outstring = meme_header + "\n\n" + elem
                d.write(outstring)


def meme_drop_unselected_motifs(src_path, dest_path, selected_motifs):
    selected_memes = set(selected_motifs)
    with open(src_path, "r") as f:
        fcont = f.read().split("\n\n")
        meme_header = "\n\n".join(fcont[:3])
        remaining_motifs = meme_header + "\n\n"
        for elem in fcont:
            if not elem.startswith("MOTIF"):
                continue
            meme_id = elem.split("\n")[0].split(maxsplit=1)[1]
            if meme_id not in selected_memes:
                continue
            remaining_motifs += "\n\n" + elem
        with open(dest_path, "w") as t:
            t.write(remaining_motifs)


def load_meme_dict(fpath):
    with open(fpath) as f:
        fcont = f.read().split("\n\n")
        meme_property_dict = {}
        for elem in fcont:
            if not elem.startswith("MOTIF"):
                continue
            meme_args = elem.split("\n")
            meme_id = meme_args[0].split(maxsplit=1)[1]
            meme_property_dict[meme_id] = {}
            letter_prop_mat = meme_args[1].replace("letter-probability-matrix:", "").split()
            for i in range(0, len(letter_prop_mat), 2):
                prop = letter_prop_mat[i].replace("=", "")
                meme_property_dict[meme_id][prop] = letter_prop_mat[i+1]
    return meme_property_dict


def load_logpval_from_dict(meme_dict):
    logpval_dict = {key: meme_dict[key]['log(Pval)'] for key in meme_dict}
    return logpval_dict

def load_nsites_from_dict(meme_dict):
    nsites_dict = {key: meme_dict[key]['nsites'] for key in meme_dict}
    return nsites_dict

def get_n_motifs(pk):
    meme_directory = os.path.join(peng_meme_directory(pk), "selected_motifs")
    return len([x for x in os.listdir(meme_directory) if x.endswith(".meme")])


def get_motif_ids(meme_file):
    motif_ids = []
    with open(meme_file) as infile:
        for line in infile:
            line = line.strip()
            if line.startswith('MOTIF'):
                motif_id = line.replace('MOTIF', '').strip()
                motif_ids.append(motif_id)
    return motif_ids
