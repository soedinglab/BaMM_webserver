Understanding the output
########################

The BaMM webserver offers a wide variety of analyzes and plots. In this section we try describe in detail what they show and how it can be used and interpreted in your own analysis.

Motif overview
**************

The result start with an overview table of the motifs.

.. image:: img/motif_overview.png
  :width: 600px
  :align: center

For each motif, it shows the IUPAC sequence, the 0th order motif representation (PWM) and if available the estimated performance of the motif and fraction of sequence that contain the motif.

The motif and all analyzes can be downloaded by clicking the button in the last column.


Sequence logos
**************

We developed sequence logos for higher orders to visualise the BaMMs. 

For this we split the relative entropy

.. math::
        H(p_{motif}|p_{bg}) = \sum_{x}^{}{ p_{motif}(x) log_2[ p_{motif}(x) / p_{bg}(x)]}
        
into a sum of terms, one
for each order. The logos show the amount of information contributed by each order over and above what is provided by
lower orders, for each kmer and position.

In the 0th-order sequence logo, the height of the four bases on each column is determined by their relative frequencies.
More frequent bases are depicted on top of less frequent bases. Consequently, the consensus sequence can be assembled
from the top bases, while the vertical order of bases in each column corresponds to their order of predominance.

This 0th-order sequence logo was designed to reflect the characteristics of the PWM model and has been widely used.
However, it is not suited to illustrate dependencies between binding site positions. 

We therefore also provide higher-order logos. In the higher-order logos, the height of both columns and *k*-mers corresponds to the contribution to the
information content that is not yet described in a lower order, in other words, the information you can gain by taking
into consideration of the dependencies between positions in the motif. Note that *k*-mers can exhibit negative
contributions to the information content.

.. image:: img/BaMM_seq_logos.png
   :width: 400px
   :height: 200px
   :scale: 150 %
   :alt: Sequence logos
   :align: center

AvRec evaluation
****************

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

Besides, given the p-value distribution from both input and background sequences, we use the `fdrtool` :cite:`strimmer2008fdrtool` to re-estimate
the null distribution and the ratio between positives and negatives, which is shown by the orange dash line
in the motif p-value statistics plot. In this way, we can estimate the motif quality independent from the initial
assumption that all input sequences are positives. The area under the Recall-TP/FP ratio curve is calculated for
positives:negative=1:1. We call this averaged recall as **motif AvRec**.


Motif distribution plot
***********************

.. image:: img/motif_distribution_plot.png
  :width: 500px
  :align: center

The motif distribution plot shows the distribution of motif occurences over the input sequences relative to the middle of the sequences.

In a ChIP-seq experiment primary motifs should have a higher enrichment around the middle of the sequence. Factors of co-binding motifs often show a less clear positional preference.

The plot can be influenced by varying the ``Motif scan p-value cut-off``.
When setting to a low p-value, only highly significant motif positions are used for generating this plot.


Motif-motif comparison
**********************

Workflows that use Motif-motif compare to annotate motifs with a collection of motifs in our database will produce a result similar to this.

.. image:: img/mmcompare_annotation.png
  :width: 600px
  :align: center

The results are sorted by significance, given by the e-value score.
The e-value is the expected number of hits when searching a scrambeled motif against the database.

The button in the last column can be used to find detailed information for the motif in our database. From there the motif can be used to scan your sequences for occurences.



