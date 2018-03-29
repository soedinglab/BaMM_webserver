Why BaMMmotif server?
=====================
.. _Why BaMMmotif server:

The BaMMmotif web server enables the user to

* (a) predict *de-novo* motifs
* (b) optimize initial motifs to higher-order models
* (c) search for motif instances in custom sequences
* (d) search for similar motifs in the existing datasets
* (e) browse a database of more than 450 higher order motif models for about 100 TFs (constantly growing)

How to use BaMMmotif server?
============================
.. _How to use BaMMmotif server:

*De novo* Motif Discovery
.........................
.. _De novo Motif Discovery:

We developed a new and fast method called **PEnG!motif** for searching motifs (position specific weight matrices,
PWMs) in a set of nucleotide sequences (DNA or RNA). Based on the PWMs discovered by PEnG!motif, we train BaMMs
(Bayesian Markov Models) which take positional inter-dependencies into account and give us more information about
the motifs derived from the sequence set.

Input items
+++++++++++
.. _Input items:

**Job Name** (optional)

You can specify the job name.

By default, a random job ID is generated  so that you can easily search for it later on the "Find My Job" page.

**Input Sequences** (required)

Please enter a FASTA formatted file containing DNA sequences that are enriched for a motif which you want to predict
(i.e. peak sequences from ChIP-seq measurements). The sequences need to be of the same length. The maximum file upload
size is limited to 250 Mb for registered users and 2.5 Mb for anonymous users.

You can choose to "Load Example Data" for testing.

Example for FASTA file:
::

    >chr5
    GATGAGGGGAAGAGAAACTCAGAAGAGTTTGAAGGGCCTGGGAAGCAGGTGTGCATTCTCCTTAAGCTAGCCTGGGCATG
    ACGTCATCAAGAATTTTGCTTAAGTGGTTGGGTACAATTGGTGTACACATCAAAGAATGCGGACTTTGGATCAGGTTGGA
    GTTGGAACTCCACTGTTTGTCAACCACATGACCCCGGGCAAGTTA
    >chr17
    ATCTCGTAGGAAAGCCCCGCCTCTATCCGCATGGAGGCGGGAATTGCCACGAAGCTCCTGTGGAGGGAGAGGAAGCAGCT
    GCGGAAAGCCAATAAGAGTGGGGAATCGATGACGTCAACCAATGGGGACGCGGGGATATTACGGCCAATGAGAATGGAGA
    AGGTCCAGGACACGTGGGTGGGGGAAGCTGAGCGCTGAGACCAAG
    >chr6
    AATATGCCTAAATTTCCTCTTTGGGAACGCAAGACTTGCAGAGATGACTCCATGGAGAGCGGACTCTGCCGGCGGGAACT
    GGAGTCGTTGGTGACGTCATCCCAGTCTGATCTGTGAAGGGTAGGGCCAGCAGGCAGCACCAAAGTTCCCGTATGCGCGT
    TTTCAGTCTTCATTTAGGTCCGAATTCCCGGCATATAAGAATACT
    >chr6
    TTGGCTTGGAGATGTGGCGGGTTGCCACTTCCCTGTGGGTCTCTGCGGCACTCTTCTGCCTGGTGACTGACACCTTGGAA
    ATGAAGTTTATGACGTCATCGTTGCGGCTGGCCAATAGAAAAAGCTCCCGCGGAGAGGTGTTCCTTCCCCTTCGACTCAG
    CTTCTTCACCCGCGTGAGCGAGCGCGCGCGCGCGGAGGGGGTGGG
    >chr2
    CCCCCAGAGTAGGGAGCGGCGGCACTAGGGGATGTTGCGCATGCGCCATACGCCTGCGCAGAATCGAGTGAGTGGGAGAC
    TAGTCAAAAAGGCTGACGTCATCGCACATGTTCTGGTCATGTCTGTGTGGGGGAGACCACGGATTCGGTGCTTTTCGTAA
    GGTGTAGAAATGATTGCTCTGAAAGATACGAATTTGTTGGCTACA
    >chr9
    AAGCCCCTACGCTGCACGTAGCTGCTCCAGCTACTGAGCCAAGACTACGCAGACAGTACAAGTCTTATAACAAAGCGGAA
    CAAGCCAGATGACGTCATCCCGCTCGCCAAAGCACATCACGTGGTCTCCGCAGCACGTGACCCGTGCCTTCGCCGTAGGT
    AAAAGAATGACGCACGTCAGTTCCAGATCGTGCGTTTTACACCCC

**Search on both strands** (optional)

When checked, the reverse complementary sequences are used for motif search as well.

Select this option when motifs can occur on both strands. Transcription factors and micro RNAs can usually bind on
both strands (in reverse orientation). Deselect if you are searching for directional motifs.

Advanced Options
++++++++++++++++
.. _Advanced options:

**Model Settings**

*Model Order*

The model order *k* defines up to which order the BaMM will be optimized. A zeroth-order BaMM is equivalent to a PWM.
A first-order BaMM model takes dinucleotide probabilities into account. Registered users can learn models up to 8th-
order while anonymous users are limited to forth-order models (due to the computation time and resource).

*adding flanking positions*

The extend options allow the user to add uniformly initialized positions to the left and/or right of the motif
initialization. The number corresponds to the amounts of nucleotide appended to either side of the motif.

**Model Initialization**

BaMM!motif requires either a PWM, a BaMM or a list of known binding sites for initialization.

By default, BaMM!motif uses **PEnG!motif** to find seeding patterns in your input sequences. It generates MEME-formatted
files which contain a bunch of PWMs of the motifs ranked by ausfc scores.

You can also provide a custom file for initialization.

*Motif Init File Format*

When you decide to use a custom file for motif initialization you can upload files in 3 different formats here.

The **PWM** file is MEME-like format and looks like:
::

    MOTIF TGASTCATC
    letter-probability matrix: alength= 4 w= 9 nsites= 14428
    0.0025 0.0005 0.0020 0.9950
    0.0272 0.0243 0.9241 0.0244
    0.9370 0.0283 0.0149 0.0198
    0.0144 0.4522 0.5203 0.0132
    0.0207 0.0144 0.0094 0.9556
    0.0150 0.9506 0.0245 0.0099
    0.9695 0.0146 0.0034 0.0125
    0.0118 0.2790 0.0681 0.6410
    0.1644 0.5324 0.1150 0.1881

    MOTIF CACTAG
    letter-probability matrix: alength= 4 w= 6 nsites= 12819
    0.0005 0.9992 0.0000 0.0003
    0.9899 0.0009 0.0004 0.0088
    0.0000 0.9814 0.0184 0.0002
    0.0016 0.0563 0.0052 0.9369
    0.9977 0.0000 0.0000 0.0023
    0.0001 0.0022 0.9977 0.0000

The **BindingSites** file contains blocks of enriched nucleotide patterns:
::

    GTGAGTCATC
    ATGACTCATC
    ATGAGTCACC
    ATGAGTCACC
    ATGACTCACT
    ATGACTCATC
    ATGAGTCACC
    GTGACTCATC
    ATGACTCATC
    ATGACTCATC
    ATGAGTCATA
    GTGACTCATA
    GTGACTCACG
    GTGAGTCATC
    ATGAGTCATA
    GTGACTCACT
    ATGACTCACA
    CTGAGTCATC
    ATGAGTCACC
    ATGACTCATA
    ATGACTCACC
    ATGACTCATT
    ATGAGTCATG
    ATGAGTCACT
    GTGACTCACC

The **BaMM**-formatted file (usually with .ihbcp suffix) contains conditional probabilities for each *k*-mer at each position:
::

    6.576e-01 9.077e-02 2.376e-01 1.397e-02
    6.576e-01 9.077e-02 2.376e-01 1.397e-02 6.576e-01 9.077e-02 2.376e-01 1.397e-02 6.576e-01 9.077e-02 2.376e-01 1.397e-02 6.576e-01 9.077e-02 2.376e-01 1.397e-02
    6.576e-01 9.077e-02 2.376e-01 1.397e-02 6.576e-01 9.077e-02 2.376e-01 1.397e-02 6.576e-01 9.077e-02 2.376e-01 1.397e-02 6.576e-01 9.077e-02 2.376e-01 1.397e-02 6.576e-01 9.077e-02 2.376e-01 1.397e-02 6.576e-01 9.077e-02 2.376e-01 1.397e-02 6.576e-01 9.077e-02 2.376e-01 1.397e-02 6.576e-01 9.077e-02 2.376e-01 1.397e-02 6.576e-01 9.077e-02 2.376e-01 1.397e-02 6.576e-01 9.077e-02 2.376e-01 1.397e-02 6.576e-01 9.077e-02 2.376e-01 1.397e-02 6.576e-01 9.077e-02 2.376e-01 1.397e-02 6.576e-01 9.077e-02 2.376e-01 1.397e-02 6.576e-01 9.077e-02 2.376e-01 1.397e-02 6.576e-01 9.077e-02 2.376e-01 1.397e-02 6.576e-01 9.077e-02 2.376e-01 1.397e-02

    5.641e-05 4.102e-04 4.905e-05 9.995e-01
    6.031e-07 3.452e-04 3.872e-07 9.996e-01 4.294e-06 2.490e-05 2.333e-06 1.000e+00 1.177e-06 5.591e-04 2.244e-06 9.994e-01 1.534e-05 1.833e-04 1.764e-05 9.998e-01
    6.031e-07 3.452e-04 3.872e-07 9.996e-01 4.294e-06 2.490e-05 2.333e-06 1.000e+00 1.177e-06 5.591e-04 2.244e-06 9.994e-01 1.534e-05 1.833e-04 1.764e-05 9.998e-01 6.031e-07 3.452e-04 3.872e-07 9.996e-01 4.294e-06 2.490e-05 2.333e-06 1.000e+00 1.177e-06 5.591e-04 2.244e-06 9.994e-01 1.534e-05 1.833e-04 1.764e-05 9.998e-01 6.031e-07 3.452e-04 3.872e-07 9.996e-01 4.294e-06 2.490e-05 2.333e-06 1.000e+00 1.177e-06 5.591e-04 2.244e-06 9.994e-01 1.534e-05 1.833e-04 1.764e-05 9.998e-01 6.031e-07 3.452e-04 3.872e-07 9.996e-01 4.294e-06 2.490e-05 2.333e-06 1.000e+00 1.177e-06 5.591e-04 2.244e-06 9.994e-01 1.534e-05 1.833e-04 1.764e-05 9.998e-01

    1.197e-04 5.324e-05 9.147e-01 8.509e-02
    1.197e-04 5.324e-05 9.147e-01 8.511e-02 1.154e-04 5.300e-05 9.130e-01 8.686e-02 1.197e-04 5.324e-05 9.147e-01 1.705e-01 6.390e-05 5.626e-06 9.149e-01 8.467e-02
    1.197e-04 5.324e-05 9.147e-01 8.512e-02 1.140e-04 5.290e-05 9.118e-01 8.803e-02 1.197e-04 5.324e-05 9.147e-01 1.705e-01 1.160e-05 3.908e-06 9.135e-01 8.648e-02 1.197e-04 5.324e-05 9.147e-01 8.511e-02 1.154e-04 5.299e-05 9.129e-01 8.687e-02 1.197e-04 5.324e-05 9.147e-01 1.762e-01 5.495e-04 3.594e-06 8.862e-01 1.124e-01 1.197e-04 5.324e-05 9.147e-01 8.512e-02 1.154e-04 5.300e-05 9.136e-01 8.625e-02 1.197e-04 5.324e-05 9.147e-01 1.931e-01 4.276e-06 1.047e-05 9.294e-01 6.938e-02 1.197e-04 5.324e-05 9.147e-01 8.511e-02 1.154e-04 5.300e-05 9.129e-01 8.688e-02 1.197e-04 5.324e-05 9.147e-01 1.705e-01 3.922e-05 3.445e-06 9.249e-01 7.482e-02

    9.600e-01 1.404e-03 3.318e-02 5.416e-03
    9.602e-01 1.429e-03 3.297e-02 5.378e-03 9.600e-01 1.402e-03 3.314e-02 9.644e-03 9.935e-01 1.356e-03 1.587e-04 4.977e-03 6.174e-01 1.363e-03 3.721e-01 9.112e-03
    9.602e-01 1.429e-03 3.297e-02 5.378e-03 9.600e-01 1.402e-03 3.314e-02 9.644e-03 9.935e-01 1.356e-03 1.587e-04 4.977e-03 6.174e-01 1.363e-03 3.721e-01 9.112e-03 9.602e-01 1.429e-03 3.297e-02 5.378e-03 9.600e-01 1.402e-03 3.314e-02 9.645e-03 9.936e-01 1.326e-03 1.550e-04 4.906e-03 6.180e-01 1.359e-03 3.715e-01 9.092e-03 9.602e-01 1.429e-03 3.297e-02 5.378e-03 9.600e-01 1.402e-03 3.314e-02 9.644e-03 9.935e-01 1.356e-03 1.587e-04 4.977e-03 6.280e-01 1.325e-03 3.618e-01 8.860e-03 9.603e-01 1.437e-03 3.290e-02 5.366e-03 9.600e-01 1.402e-03 3.313e-02 1.105e-02 9.936e-01 1.356e-03 3.034e-06 4.976e-03 6.005e-01 1.366e-03 3.888e-01 9.315e-03

    1.888e-02 6.247e-01 3.503e-01 6.167e-03
    1.958e-02 6.138e-01 3.606e-01 1.941e-03 1.761e-02 4.885e-01 4.888e-01 5.053e-03 2.342e-03 9.502e-01 4.646e-02 1.028e-03 8.912e-03 5.351e-01 4.175e-01 4.397e-01
    1.949e-02 6.141e-01 3.605e-01 1.933e-03 1.761e-02 4.885e-01 4.889e-01 5.053e-03 2.342e-03 9.502e-01 4.648e-02 1.028e-03 8.912e-03 5.351e-01 4.175e-01 4.397e-01 1.957e-02 6.139e-01 3.605e-01 1.940e-03 1.761e-02 4.885e-01 4.888e-01 5.053e-03 2.342e-03 9.502e-01 4.646e-02 1.028e-03 8.899e-03 5.357e-01 4.169e-01 7.361e-01 2.044e-02 6.080e-01 3.653e-01 2.019e-03 1.734e-02 4.504e-01 5.275e-01 4.748e-03 2.342e-03 9.502e-01 4.646e-02 1.028e-03 6.753e-03 5.072e-01 4.417e-01 3.424e-01 7.173e-03 6.971e-01 2.943e-01 5.361e-04 1.748e-02 4.848e-01 4.927e-01 5.016e-03 7.781e-04 9.810e-01 1.773e-02 5.415e-04 8.531e-03 5.417e-01 4.085e-01 4.197e-01

    1.472e-01 3.000e-03 2.894e-01 5.603e-01
    3.011e-02 6.401e-04 1.026e-01 8.667e-01 2.319e-01 4.488e-03 4.098e-01 3.539e-01 7.011e-03 4.268e-04 9.210e-02 9.004e-01 6.726e-02 1.465e-03 1.589e-01 7.724e-01
    1.405e-02 3.164e-04 7.682e-02 9.088e-01 2.083e-01 3.050e-03 4.171e-01 3.715e-01 5.328e-03 3.981e-04 9.011e-02 9.042e-01 5.942e-02 1.383e-03 1.565e-01 7.827e-01 3.011e-02 6.400e-04 1.026e-01 8.666e-01 2.321e-01 4.492e-03 4.081e-01 3.553e-01 6.405e-03 4.043e-04 8.420e-02 9.089e-01 6.730e-02 1.465e-03 1.589e-01 7.724e-01 3.011e-02 6.405e-04 1.027e-01 8.665e-01 5.447e-01 2.359e-02 3.149e-01 1.168e-01 6.913e-03 4.232e-04 9.133e-02 9.013e-01 6.722e-02 1.465e-03 1.589e-01 7.724e-01 3.012e-02 6.402e-04 1.026e-01 8.666e-01 2.414e-01 4.076e-03 4.404e-01 3.159e-01 7.118e-03 3.884e-04 9.073e-02 9.000e-01 5.390e-02 1.150e-03 1.280e-01 8.170e-01

*Motif InitFile*

A file contains initial motif model(s) in one of the formats (PWM, BindingSites or BaMM) mentioned above.

*Motif Background File*

It is also a **BaMM**-formatted file which contains conditional probabilities for each *k*-mer at each position learned
from a background sequence set. It is highly recommended to upload it (usually the .hbcp file generated by BaMMmotif)
when your initial model is BaMM-formatted.

**Background Model**

Background model is used for generating background sequences for evaluating the foreground model. By default, the
background model is derived from the trimer frequencies of the positive sequences. If background sequences are provided
by the user, the background model is then derived from the given sequences.

*Background Order K*

The background order describes the order of the background BaMM. The default *K* is 2, which means that the background
model will be derived from the 3-mer frequencies of the background sequences.

*Background Sequences*

A FASTA-formatted file with background sequences can be provided in order to learn the background BaMM. These sequences
should reflect the genomic background of the positive input sequences without being enriched for a motif.

If no background sequence file is provided, the background model is learned from the *K*-mer frequencies of the positive
sequences.

**Expectation Maximization Optimization**

*Motif prior probability*

By default, your initial models are optimized by applying an expectation maximization algorithm.

q-value indicates the prior knowledge about the probability of the sequences from ChIP-seq contains the initial motif.

**Motif Position**

By selecting this function, it will scan your input sequences with the initial/optimized motifs and find the most
probable site for the motif to occur till a p-value cutoff (determined by the motif score limit).
You will also get the distribution plot indicating the relative position of the motif from the sequence center.

*Motif score limit*

The motif score limit defines up to which similarity a motif position on a sequence will be counted as a motif instance.
The higher this score, the fewer the reported motif positions.

**Motif Evaluation**

By selecting this function, the initial/optimized BaMM model will be evaluated by calculating the false-discovery-rate
(FDR) and sensitivity values, and the area under the sensitivity-FDR curve (AUSFC).

The AUSFC score is a good measure of motif model quality. The AUSFC score is normalised to the range of FDR values on
the x axis, :math:`log( 0.5 ) − log( 10^{−4} )`. The AUSFC score has the great advantage that is summarises the
performance of the model for the entire range of FDR values that are relevant in practice, without putting undue
emphasis on any specific region. It can be interpreted as the mean model sensitivity, averaged over the log false
discovery rate.

Submission
++++++++++
.. _Submission:

Submit your job by clicking "BaMM!" button at the bottom. This will lead you to a page where you can view your job
status (while the job is running) and the result (when the job is complete).

Motif-Motif Comparison
......................
.. _Motif-Motif Comparison:

With this function, you can search with your input motif model through the existing databases and find similar motifs.

Motif Scan
..........
.. _Motif Scan:

This function allows you to scan your sequence set for occurrences of an input motif model. You can give an overview of
the motif distribution on the sequence set and a detailed look at motif occurrences.

Motif Database:
...............
.. _Motif Database:

In this database, we provide over 450 higher-order models learned from ChIP-seq data for about 100 transcription factors.
The size of our database is consistently growing.

These models are learned by applying BaMM!motif with model order of 2.

What does the BaMM database contain?
++++++++++++++++++++++++++++++++++++
.. _What does the BaMM database contain:

Currently our database contains 445 higher order BaMM models derived from ENCODE ChIP-Seq data of 94 human transcription
factor measurements from various laboratories. We will continuously enlarge this database with higher order BaMM models
predicted on further publicly available data sets such as PBM data and HT-SELEX.

How to search for a specific entry in the database?
+++++++++++++++++++++++++++++++++++++++++++++++++++
.. _How to search for a specific entry in the database:

Follow the link "Motif Database" from the home website and enter the name of your protein target of interest. You will
obtain a list of all database entries which contain your protein name. Details for each entry can be viewed by clicking
the "more..." button. By clicking the "DOWNLOAD MODEL" button, you can download all the plots for the chosen motif model.

.. How to use a motif model as a seed for further analysis?
.. .. _How to use a motif model as a seed for further analysis:


How to interpret BaMM results?
==============================
.. _How to interpret BaMM results:

How do I obtain my job results?
...............................
.. _How do I obtain my job results:

You can obtain your job results on the page that you are redirected to after submitting your job. You can also search
for it on the "Find My Job" page with your job ID.

What does the result page show?
...............................
.. _What does the result page show:

BaMMmotif outputs the best five motifs after seeding all possible motifs and optimized the top 5 motifs.
It shows the parameter settings used for obtaining the result.

For each model, the IUPAC code, PWMs for both sense and anti-sense sequences, AUSFC score (see **Motif Evaluation** for
details) and occurrence ratio are shown.

When you click on one motif, or scroll down the page, you will find more details, such as 1st- and 2nd-order sequence
logos, which show the amount of information contributed by each order over and above what is provided by lower orders,
for each oligonucleotide and position.

You will also see three measures for the motif performance, namely, Sensitivity-False Discovery Rate curve,
partial Receiver Operating Characteristic (pROC) curve, Precision-Recall curve and their corresponding
area-under-the curve (AUC value). This hopefully makes it easy for you to estimate the suitablity of a motif model to
predict binding sites in your dataset.

The last plot shows the motif position distribution in your sequence set. If you search on both strands, it will show
your the motif distribution on both strands.

You can download all the models by clicking "DOWNLOAD ALL" button or each individual model by clicking "DOWNLOAD MODEL".


How to interpret BaMMmotif logos?
.................................
.. _How to interpret BaMMmotif logos:

In the 0th-order sequence logo, the higher of the four bases on each column is determined by their relative frequencies.
More frequent bases are depicted on top of less frequent bases. Consequently, the consensus sequence can be assembled
from the top bases, while the vertical order of bases in each column corresponds to their order of predominance.

This 0th-order sequence logo was designed to reflect the characteristics of the PWM model and has been widely used.
However, it is not suited to illustrate dependencies between binding site positions. Thus, we generate higher-order
logos for you. In the higher-order logos, the height of both columns and *k*-mers corresponds to the contribution to the
information content that is not yet described in a lower order, in other words, the information you can gain by taking
into consideration of the dependencies between positions in the motif. Note that *k*-mers can exhibit negative
contributions to the information content.


Command line tools
==================
.. _Command line tools:

Here are the stand-alone tools which can be downloaded from our Github repository and used via command lines:

PEnG!motif
..........
.. _PEnGmotif:

The command line version of PEnG!motif can be downloaded from our GitHub `PEnGmotif repository`_.

BaMM!motif
..........
.. _BaMMmotif:

The command line version of BaMM!motif can be downloaded from our GitHub `BaMMmotif repository`_.

BaMMScan
........
.. _BaMMScan:

The command line version of BaMMScan can be downloaded from our GitHub `BaMMmotif repository`_.

FDR analysis
............
.. _FDR:

The command line version of FDR can be downloaded from our GitHub `BaMMmotif repository`_.


How to use these tools via command lines?
.........................................
.. _How to use these tools via command lines:

A detailed description of how to use the command line tool can be found in the README section of the respective GitHub
repository.


FAQs
====
.. _FAQs:

Why shall I register?
.....................
.. _Why shall I register:

The BaMM!motif algorithm and its results are **freely** available for **all users** without registration.

However, registering for a BaMM account makes working with the BaMMmotif server even more convenient.

In logged in mode, the user can see all his running and finished jobs in a structured list to keep track of the job
status more easily. This is only possible if a job can be assigned to a defined user, hence only limited to registered
users. Moreover, you will be notified via e-mail once your jobs are finished.

How can I register?
...................
.. _How can I register:

For registering at BaMM!motif, click the "Log in" button on the top right corner and follow the link to register
a new account. The only information required is a username (can be an acronym), a valid e-mail address, and a password.
E-mail addresses will only be used by the BaMM!motif web server to inform the user of the finished jobs. There will
be no advertisements or spam mails and absolutely no forwarding of your confidential information to any third parties.

How long are the results available?
...................................
.. _How long are the results available:

Currently, the results will be kept for 4 weeks for unregistered users.

Citing and References
=====================
.. _Citing and References:

Please cite our paper: `BaMMmotif paper`_ DOI: 10.1093/nar/gkw521

Contact
=======
.. _Contact:

bamm(at)mpibpc(dot)mpg(dot)de

.. external links:

.. _PEnGmotif repository: https://github.com/soedinglab/PEnG-motif
.. _BaMMmotif repository: https://github.com/soedinglab/BaMMmotif
.. _BaMMmotif paper: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5291271/





