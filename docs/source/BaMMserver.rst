Welcome to BaMMmotif server
***************************

Why BaMMmotif server?
=====================
.. _Why BaMMmotif server:

The BaMMmotif web server enables the user to

* (a) train higher-order BaMM models
* (c) search for motif instances in custom sequences
* (d) search for similar motifs in our BaMM databases
* (e) perform keyword searches on our BaMM database

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

Submit your job by clicking the submit button at the bottom. This will lead you to a page where you can view your job
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

BaMMmotif outputs a refined model for each seed.
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

How long are the results available?
...................................
.. _How long are the results available:

Currently, the results will be kept for at least 4 weeks for unregistered users.

Citing and References
=====================
.. _Citing and References:

Please cite our paper: `BaMMmotif paper`_ .DOI: 10.1093/nar/gkw521

Contact
=======
.. _Contact:

bamm(at)mpibpc(dot)mpg(dot)de

.. external links:

.. _PEnGmotif repository: https://github.com/soedinglab/PEnG-motif
.. _BaMMmotif repository: https://github.com/soedinglab/BaMMmotif2
.. _BaMMmotif paper: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5291271/
