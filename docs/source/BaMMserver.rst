Why BaMMmotif server?
=====================
.. _Why_BaMMmotif_server:

The BaMMmotif web server enables the user to

* (a) predict *de-novo* motifs
* (b) optimize initial motifs to higher-order models
* (c) search for motif instances in custom sequences
* (d) search for similar motifs in the existing datasets
* (e) browse databases of higher order motif models for over 600 human TFs, over 300 mouse TFs and TFs for other model organisms (constantly growing)

About BaMM!motif
================
.. _About BaMMmotif:

The Bayesian Scheme
...................

.. image:: img/bayesianScheme.png
   :width: 400px
   :height: 200px
   :scale: 150 %
   :alt: Bayesian Scheme
   :align: center


Bayesian Markov model training automatically adapts the effective number of parameters to the amount of data.

In the last line, if the context GCT is so frequent at position j in the motif that its number of occurrences
outweighs the pseudo-count strength, :math:`n_j(GCT) \gg \alpha_3`, the third-order probabilities for this context
will be roughly the maximum likelihood estimate, e.g. :math:`p_j(A|GCT) ≈ n_j(GCTA)/n_{j−1}(GCT)`. However, if few
GCT were observed in comparison with the pseudo-counts, :math:`n_j(GCT) \ll \alpha_3` , the third-order probabilities
will fall back on the second-order estimate, :math:`p_j(A|GCT) \approx p_j(A|CT)`. If also :math:`n_j(CT) \ll \alpha_2`,
then likewise the second-order estimate will fall back on the first-order estimate, and hence
:math:`p_j(A|GCT) \approx p_j(A|T)`. In this way, higher-order dependencies are only learned for the fraction of
k-mer contexts that occur sufficiently often at one position j in the motif’s training instances to trump the
pseudo-counts. Throughout this work we set :math:`\alpha_0 = 1` and :math:`\alpha_k = 20 × 3^k − 1`.


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
(i.e. peak sequences from ChIP-seq measurements). The sequences do not have to be of the same length. The maximum file
upload size is limited to 2.5 Mb.

You can choose to "Load Example Data" for testing.

Example for FASTA file:
::

    >chr5:start-end
    GATGAGGGGAAGAGAAACTCAGAAGAGTTTGAAGGGCCTGGGAAGCAGGTGTGCATTCTCCTTAAGCTAGCCTGGGCATG
    ACGTCATCAAGAATTTTGCTTAAGTGGTTGGGTACAATTGGTGTACACATCAAAGAATGCGGACTTTGGATCAGGTTGGA
    GTTGGAACTCCACTGTTTGTCAACCACATGACCCCGGGCAAGTTA
    >chr17:start-end
    ATCTCGTAGGAAAGCCCCGCCTCTATCCGCATGGAGGCGGGAATTGCCACGAAGCTCCTGTGGAGGGAGAGGAAGCAGCT
    GCGGAAAGCCAATAAGAGTGGGGAATCGATGACGTCAACCAATGGGGACGCGGGGATATTACGGCCAATGAGAATGGAGA
    AGGTCCAGGACACGTGGGTGGGGGAAGCTGAGCGCTGAGACCAAG
    >chr6:start-end
    AATATGCCTAAATTTCCTCTTTGGGAACGCAAGACTTGCAGAGATGACTCCATGGAGAGCGGACTCTGCCGGCGGGAACT
    GGAGTCGTTGGTGACGTCATCCCAGTCTGATCTGTGAAGGGTAGGGCCAGCAGGCAGCACCAAAGTTCCCGTATGCGCGT
    TTTCAGTCTTCATTTAGGTCCGAATTCCCGGCATATAAGAATACT
    >chr6:start-end
    TTGGCTTGGAGATGTGGCGGGTTGCCACTTCCCTGTGGGTCTCTGCGGCACTCTTCTGCCTGGTGACTGACACCTTGGAA
    ATGAAGTTTATGACGTCATCGTTGCGGCTGGCCAATAGAAAAAGCTCCCGCGGAGAGGTGTTCCTTCCCCTTCGACTCAG
    CTTCTTCACCCGCGTGAGCGAGCGCGCGCGCGCGGAGGGGGTGGG
    >chr2:start-end
    CCCCCAGAGTAGGGAGCGGCGGCACTAGGGGATGTTGCGCATGCGCCATACGCCTGCGCAGAATCGAGTGAGTGGGAGAC
    TAGTCAAAAAGGCTGACGTCATCGCACATGTTCTGGTCATGTCTGTGTGGGGGAGACCACGGATTCGGTGCTTTTCGTAA
    GGTGTAGAAATGATTGCTCTGAAAGATACGAATTTGTTGGCTACA
    >chr9:start-end
    AAGCCCCTACGCTGCACGTAGCTGCTCCAGCTACTGAGCCAAGACTACGCAGACAGTACAAGTCTTATAACAAAGCGGAA
    CAAGCCAGATGACGTCATCCCGCTCGCCAAAGCACATCACGTGGTCTCCGCAGCACGTGACCCGTGCCTTCGCCGTAGGT
    AAAAGAATGACGCACGTCAGTTCCAGATCGTGCGTTTTACACCCC

**MMcompare Motif Database**

Databases containing trained BaMM models or PWM models from public available ChIP-seq datasets.

.. _Advanced_options:

Advanced Options
++++++++++++++++

**General settings**

*Search on both strands*

When checked, the reverse complementary sequences are used for motif search as well.

Select this option when motifs can occur on both strands. Transcription factors and micro RNAs can usually bind on
both strands (in reverse orientation). Deselect if you are searching for directional motifs.

*Background Sequences*

You can upload a FASTA file containing background sequences if available. It will be used for generating the background
model for motif learning and evaluation.

*Background Model Order*

The background model order *K* defines up to which order the background model will be learned. The background model is
a *K*-order homogeneous Markov model. The default *K* is 2, which means that the background model will be derived from
3-mer frequencies of the background sequences. We recommend a background model of 2 for a realistic model of the genomic
input. For very short motifs, a background model order of 1 or even 0 may be required to find the motif.

**Seeding stage**

*Pattern Length*

The length of patterns on the sequences to be searched.

*Z-Score Threshold*

Z-score threshold for basic patterns. Patterns with lower than this Z-score threshold will not be considered.

*Count Threshold*

Patterns with fewer than this amount of counts will be be considered.

*IUPAC Optimization Score*

Scoring function that is used for optimizing to the IUPAC patterns. There are three options:

* LOGPVAL: calculate optimization scores based on p-value on the log scale
* MUTUAL_INFO: calculate optimization scores based on the mutual information of patterns
* ENRICHMENT: calculate optimization scores based on expected pattern counts

*Skip EM*

When checked, the Expectation-Maximization (EM) step will be skipped for optimization.

**Model Settings**

*Model Order*

The model order *k* defines up to which order the BaMM will be optimized. A zeroth-order BaMM is equivalent to a PWM.
A first-order BaMM model takes dinucleotide probabilities into account. Registered users can learn models up to 8th-
order while anonymous users are limited to forth-order models (due to the computation time and resource).

*Flanking extension*

The extend options allow the user to add uniformly initialized positions to the left and/or right of the motif
initialization. The number corresponds to the amounts of nucleotide appended to both ends of the motif. If the
initializer only consists of the informative core motif, enlarging the motif allows to learn the information in the
flanking regions.

**Additional settings**

*Run motif scanning*

When checked, the input sequences will be scanned for occurrences of the optimized motif. It generates the motif
distribution plot on the results page.

*Motif scanning p-value cutoff*

Only motif positions with a p-value smaller than this cutoff will be reported as binding positions. The p-values
are computed by fitting the high-scoring tail of the log-odds score distribution on sequences generated with the
background model with an exponential function, which give good fits.

*Run motif evaluation*

When checked, the performance of the optimized motif on the input sequence set will be evaluated. It generates the
performance plots.

*Run motif-motif compare*

When checked, the optimized motifs will be compared with the motifs in the selected database.

*MMcompare e-value cutoff*

The e-value limit will be used to define a threshold for motif comparisons between the query model and the database.

Submission
++++++++++
.. _Submission:

Submit your job by clicking "BaMM!" button at the bottom. This will lead you to a page where you can view your job
status (while the job is running) and the result (when the job is complete).


Motif Scan
..........
.. _Motif Scan:

This provides you the functionality to scan your sequence set for occurrences of an input motif model.

The query motif(s) can be one or multiple PWMs in a `MEME-format <http://meme-suite.org/doc/meme-format.html>`_ files
(version 4 or above)

or

a single BaMM model, which the foreground motif model file is with extension `.ihbcp` and the background motif model
is in the file with extension `.hbcp`.

The **advanced options** are explained :ref:`here <Advanced_options>`.

You can have an overview of the motif distribution on the sequence set with the relative distance to the peak summit.

Motif Database:
...............
.. _Motif Database:

In this database, we provide over 1000 higher-order models learned from ChIP-seq data for non-redundant transcription
factors for 5 organisms. Among them:

* 613 motif models for ``Homo sapiens`` (human)
* 354 motif models for ``Mus musculus`` (mouse)
* 19 motif models for ``Rattus norvegicus`` (rat)
* 16 motif models for ``Danio rerio`` (zebrafish)
* 34 motif models for ``Schizosaccharomyces pombe`` (yeast)

Original datasets are provided by the `GTRD project <http://gtrd.biouml.org/>`_ .

The size of our database is consistently growing.

Besides, we also offers external links to 0th-order models present in other public datasets such as
`JASPAR <http://jaspar.genereg.net/>`_ and `HOCOMOCO <http://hocomoco11.autosome.ru/>`_ .

Motif-Motif Comparison
......................
.. _Motif-Motif Comparison:

With this function, you can search with your input motif model through the existing databases and find similar motifs.

The query motif(s) can be one or multiple PWMs in a `MEME-format <http://meme-suite.org/doc/meme-format.html>`_ files
(version 4 or above)

or

a single BaMM model, which the foreground motif model file is with extension `.ihbcp` and the background motif model
is in the file with extension `.hbcp`.


How to use a motif model as a seed for further analysis?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++
.. _How to use a motif model as a seed for further analysis:

On each detailed results page of each motif, you can click the `USE THIS MODEL FOR MOTIF SEARCH` option for searching
this motif on your input sequences.

How do I obtain my job results?
...............................
.. _How do I obtain my job results:

You can obtain your job results on the page that you are redirected to after submitting your job. You can also search
for it on the "Find My Job" page with your job ID. This result will be kept for up to 15 days.
