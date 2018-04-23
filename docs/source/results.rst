What does the results page show?
================================
.. _What does the results page show:

BaMMmotif outputs the best three motifs after seeding all possible motifs and optimized the top 3 motifs.

For each motif, the IUPAC code, PWM sequence logos for both sense and anti-sense sequences, AvRec score and
fractional occurrence ratio are shown.

When you click on one motif, or scroll down the page, you will find more details, such as 1st- and 2nd-order sequence
logos for the positive strand, which show the amount of information contributed by each order over and above what is
provided by lower orders, for each oligonucleotide and position (:ref:`details <How to interpret BaMMmotif logos>`).

You will also see two measures for the motif performance, namely, p-value statistics and Recall-TP/FP ratio curves for
the motif evaluated either with the assumption that all input sequences are positives (left panel) or by re-estimating the
null distribution and getting a new positive:negative ratio (right panel). The corresponding area-under-the curve
(AvRev values) are calculated (:ref:`detals <How to interpret evaluation plots>`). This hopefully helps you estimate
the suitability of a motif model to predict binding sites in your input data set.

The last plot shows the motif position distribution in your sequence set. If you search on both strands, it will show
your the motif distribution on both strands.

All the settings for obtaining these models are listed at the bottom of the results page.

You can download all the models by clicking "DOWNLOAD ALL" button or each individual model by clicking "DOWNLOAD".

How to interpret BaMMmotif logos?
=================================
.. _How to interpret BaMMmotif logos:

We developed sequence logos for higher orders to visualise the BaMMs. We split the relative entropy
:math:`H(p_{motif}|p_{bg}) = \sum_{x}^{}{ p_{motif}(x) log_2[ p_{motif}(x) / p_{bg}(x)]}` into a sum of terms, one
for each order. The logos show the amount of information contributed by each order over and above what is provided by
lower orders, for each oligo-nucleotide and position.

In the 0th-order sequence logo, the higher of the four bases on each column is determined by their relative frequencies.
More frequent bases are depicted on top of less frequent bases. Consequently, the consensus sequence can be assembled
from the top bases, while the vertical order of bases in each column corresponds to their order of predominance.

This 0th-order sequence logo was designed to reflect the characteristics of the PWM model and has been widely used.
However, it is not suited to illustrate dependencies between binding site positions. Thus, we generate higher-order
logos for you. In the higher-order logos, the height of both columns and *k*-mers corresponds to the contribution to the
information content that is not yet described in a lower order, in other words, the information you can gain by taking
into consideration of the dependencies between positions in the motif. Note that *k*-mers can exhibit negative
contributions to the information content.

.. image:: img/BaMM_seq_logos.png
   :width: 400px
   :height: 200px
   :scale: 150 %
   :alt: Sequence logos
   :align: center


How to interpret evaluation plots?
==================================
.. _How to interpret evaluation plots:

**Evaluation plots and AvRec score**

.. image:: img/evaluation_plots.png
   :width: 450px
   :height: 450px
   :scale: 150 %
   :alt: Evaluation plots
   :align: center

We generate background sequences from a second-order Markov model trained on all input sequences and ask how well
the input sequences (positives) are separated from the background sequences (negatives). As usual we define true
positives (TP) as predictions that are correct, false positives (FP) as predictions that are incorrect,and
false negatives (FN) as positive test cases that have not been predicted. The precision is defined as the fraction of
predictions that are correct, TP/(TP+FP), and the recall (= sensitivity) is the fraction of true motif instances that
are actually predicted, TP/(TP+FN).

The TP/FP ratio is normalized to the case where positives:negatives=1:1. We then plot the recall-TP/FP ratio curve,
with TP/FP ratio plotted on a logarithmic y-scale, e.g. between 1 and 100. The area under this curve summarizes the
performance of the model for the entire range of TP/FP values that are relevant in practice, without putting undue
emphasis on any specific region. It can be interpreted as the average model recall (AvRec) over the given range of
TP/FP ratio. This gives the motif performance on the input data set, The area under the Recall-TP/FP ratio curve is
calculated for positives:negative=1:1 and we name it as **dataset AvRec**. In addition, if the TP/FP ratio is above 1
for the case where positives:negatives=1:10, a dash curve for it will be depicted on the plot.
Additionally, the p-value density plot is shown, which indicates how we define each term.

(Note that **dataset AvRec** is used as the **zoops_score** for motif reranking in the seeding phase.)

Besides, given the p-value distribution from both input and background sequences, we use `fdrtool` to re-estimate
the null distribution and the ratio between positives and negatives, which is shown by the orange dash line
in the motif p-value statistics plot. In this way, we can estimate the motif quality independent from the initial
assumption that all input sequences are positives. The area under the Recall-TP/FP ratio curve is calculated for
positives:negative=1:1. We call this averaged recall as **motif AvRec**.


What downloaded package contains
================================
.. _What downloaded package contains:

MEME-format PWM models
......................
.. _MEME-format PWM models:

By default, BaMM!motif uses our in-house tool **PEnG!motif** to find seeding patterns in your input sequences.
It generates `MEME-format <http://meme-suite.org/doc/meme-format.html>`_ files (saved as `.meme` file) which
contain a bunch of PWMs of the motifs ranked by `zoops_scores`. The occurrences of predicted motifs are estimated
and shown as `occur`.

These PWMs are used as seeds for further refinement into BaMM models.

Here is an example for MEME-format file generated by our PEnG!motif:
::

    MEME version 4

    ALPHABET= ACGT

    Background letter frequencies
    A 0.25864 C 0.240258 G 0.241035 T 0.260067

    MOTIF TGASTCATCSC
    letter-probability matrix: alength= 4 w= 11 nsites= 32240 bg_prob= 0 opt_bg_order= 2 log(Pval)= -20070.6 zoops_score= 0.763 occur= 0.939
    0.00000011 0.00000020 0.00000005 0.99999958
    0.00000019 0.00000019 0.99973792 0.00026177
    0.99776745 0.00222652 0.00000086 0.00000516
    0.00043767 0.31039140 0.68885416 0.00031674
    0.00000172 0.00001118 0.00000463 0.99998242
    0.00015724 0.99983966 0.00000142 0.00000168
    0.99997258 0.00000054 0.00002521 0.00000166
    0.00000828 0.25723305 0.00413273 0.73862594
    0.02208222 0.92982459 0.00702223 0.04107105
    0.16592142 0.34808874 0.35102692 0.13496293
    0.07382397 0.51519489 0.17385206 0.23712915

    MOTIF ATTRTTTGTTTT
    letter-probability matrix: alength= 4 w= 12 nsites= 13728 bg_prob= 0.0 opt_bg_order= 2 log(Pval)= -893.0211792 zoops_score= 0.252 occur= 0.621
    0.68648666 0.00624365 0.03511349 0.27215624
    0.27477601 0.00371415 0.06135688 0.66015303
    0.00009623 0.00107756 0.00017856 0.99864769
    0.56885940 0.00127072 0.42884308 0.00102682
    0.00040802 0.00205148 0.00037785 0.99716270
    0.00159969 0.00023089 0.00047653 0.99769294
    0.00016588 0.00006246 0.01915511 0.98061651
    0.24886248 0.01232569 0.70805818 0.03075366
    0.00018377 0.14974646 0.01920011 0.83086962
    0.08978166 0.01159330 0.00815281 0.89047223
    0.00074780 0.00028864 0.00068021 0.99828333
    0.27042452 0.00127012 0.01194946 0.71635598

BaMM models
...........
.. _BaMM models:

The optimized foreground model is in **BaMM**-format file with extension `.ihbcp` (inhomogeneous bamm conditional probability)
contains probabilities of the BaMM model. While blank lines separate BaMM positions, lines 1 to k+1 of each BaMM
position contain the (conditional) probabilities for order 0 to order k. For instance, the format for a BaMM of order
2 and length W is as follows:

**Filename extension: `.ihbcp`**

P\ :sub:`1`\ (A) P\ :sub:`1`\ (C) P\ :sub:`1`\ (G) P\ :sub:`1`\ (T)

P\ :sub:`1`\ (A|A) P\ :sub:`1`\ (C|A) P\ :sub:`1`\ (G|A) P\ :sub:`1`\ (T|A) P\ :sub:`1`\ (A|C) P\ :sub:`1`\ (C|C) P\ :sub:`1`\ (G|C) ... P\ :sub:`1`\ (T|T)

P\ :sub:`1`\ (A|AA) P\ :sub:`1`\ (C|AA) P\ :sub:`1`\ (G|AA) P\ :sub:`1`\ (T|AA) P\ :sub:`1`\ (A|AC) P\ :sub:`1`\ (C|AC) P\ :sub:`1`\ (G|AC) ... P\ :sub:`1`\ (T|TT)


P\ :sub:`2`\ (A) P\ :sub:`2`\ (C) P\ :sub:`2`\ (G) P\ :sub:`2`\ (T)

P\ :sub:`2`\ (A|A) P\ :sub:`2`\ (C|A) P\ :sub:`2`\ (G|A) P\ :sub:`2`\ (T|A) P\ :sub:`2`\ (A|C) P\ :sub:`2`\ (C|C) P\ :sub:`2`\ (G|C) ... P\ :sub:`2`\ (T|T)

P\ :sub:`2`\ (A|AA) P\ :sub:`2`\ (C|AA) P\ :sub:`2`\ (G|AA) P\ :sub:`2`\ (T|AA) P\ :sub:`2`\ (A|AC) P\ :sub:`2`\ (C|AC) P\ :sub:`2`\ (G|AC) ... P\ :sub:`2`\ (T|TT)

...

P\ :sub:`w`\ (A) P\ :sub:`w`\ (C) P\ :sub:`w`\ (G) P\ :sub:`w`\ (T)

P\ :sub:`w`\ (A|A) P\ :sub:`w`\ (C|A) P\ :sub:`w`\ (G|A) P\ :sub:`w`\ (T|A) P\ :sub:`w`\ (A|C) P\ :sub:`w`\ (C|C) P\ :sub:`w`\ (G|C) ... P\ :sub:`w`\ (T|T)

P\ :sub:`w`\ (A|AA) P\ :sub:`w`\ (C|AA) P\ :sub:`w`\ (G|AA) P\ :sub:`w`\ (T|AA) P\ :sub:`w`\ (A|AC) P\ :sub:`w`\ (C|AC) P\ :sub:`w`\ (G|AC) ... P\ :sub:`w`\ (T|TT)


**BaMM Background Model**

The homogeneous Markov model derived from the K-mer frequencies of the positive sequenced is used as
background model for evaluating the foreground model. It is saved in a file with extension `.hbcp`
(homogeneous bamm conditional probabilities):

P(A) P(C) P(G) P(T)

P(A|A) P(C|A) P(G|A) P(T|A) P(A|C) P(C|C) P(G|C) ... P(T|T)

P(A|AA) P(C|AA) P(G|AA) P(T|AA) P(A|AC) P(C|AC) P(G|AC) ... P(T|TT)


The background model is important for generating BaMM sequence logos.

BaMM Sequence Logo
..................
.. _BaMM Sequence Logo:

BaMM sequences logos for 0th-order on both the original strand and its reverse complement. The 1st- and 2nd-order logos
are shown only for the original strand.

These logos are saved in `.png` files.

Motif Occurrence and Distribution
.................................
.. _Motif Occurrence and Distribution:

**Motif Occurrence**

The motif occurrences with a p-value above certain value are reported in the file with extension `.occurrence`. It
contains information such as:

::

  chrom	seq_length	strand	start..end	pattern	p-value	e-value

This can be converted to a `.bed` file if the #CHROM information is properly given by the input FASTA file.

This `.occurrence` file is used for generating the motif distribution plot.

**Motif Distribution**

Motif distribution plot shows the relative motif positions to peak summit, if the input sequences are extracted
by peak callers. If motif is learned on both strands, it will show the motif distribution on both strands.

Motif Evaluation
................
.. _Motif Evaluation:


**zoops.stats file**

The `.zoops.stats` file contains the TPs (true positives), FPs (false positives), FDR (false discovery rate), Recall
p-values for both positive and background sequences, with the assumption that in the data set there is zero or one
occurrence of each motif per sequence (`zoops`). It is used for generating the evaluation plots and `bmscore` file.

**Evaluation plots**

The evaluation plots for motif on the data set are saved with extension `_dataRRC` and `_dataPval`.

The evaluation plots for motif only are saved with extension `_motifRRC` and `_motifPval`.

These plots are saved in both `.png` and `.pdf` files.

**bmscore file**

The `.bmscore` file keeps track of the AvRec score, motif occurrences for both dataset (the dataset_avrec and data_occur)
and motif only (the motif_avrec and motif_occur) for the top three optimized motifs obtained from the seeding phase.

Find my job
===========
.. _Find my job:

All the recently submitted jobs are listed on the "Find my job" page. You can also search for them by entering the job ID.

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

We guarantee that the results will be accessible via job id for at least 3 months.

What is the maximal size of input sequence file that I can upload?
..................................................................
.. _maximal size of input sequence file:

You can upload input sequence file with a maximal size of 50 MB.

For larger sequence files, you can either use our commandline tools, or run the webserver locally after adapting the ``MAX_UPLOAD_FILE_SIZE`` configuration option.
You can find detailed instructions in the `README <https://github.com/soedinglab/BaMM_webserver/blob/master/README.md>`_ in the webserver's github repository.

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
