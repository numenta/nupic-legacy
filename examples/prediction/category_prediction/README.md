# Web site data prediction / category prediction example:

This example shows how to use the [SDRCategoryEncoder][1] with [HTMPredictionModel][2] to analyze web site traffic data by extracting temporal patterns from user sessions described as a sequences of web page categories.

We will use the [MSNBC.com Anonymous Web Data][3] data set provided by [UCI Machine Learning Repository][4] to predict the next page the user is more likely to click. In this data set each page is assigned a category and the user behavior is recorded as navigating from one page to another.

Dataset characteristics:

  - Number of users: 989,818
  - Average number of visits per user: 5.7
  - Number of categories: 17
  - Number of URLs per category: 10 to 5,000

See [dataset][3] description for more information.

### Run with:
```  
python webdata.py
```

### Sample output:
```text
The following table shows the encoded SDRs for every page category in the dataset
+---------------+-----------------------------------------------------------------------------+
| Page Category | Encoded SDR (on bit indices)                                                |
+---------------+-----------------------------------------------------------------------------+
| bbs           | [ 19  26 115 171 293 364 390 442 470 477 550 598 624 670 705 719 744 748    |
|               |  788 850 956]                                                               |
| business      | [ 48 104 144 162 213 280 305 355 376 403 435 628 694 724 780 850 854 870    |
|               |  891 930 955]                                                               |
| frontpage     | [  4   7  35  37  48  91 118 143 155 313 339 410 560 627 736 762 795 864    |
|               |  885 889 966]                                                               |
| health        | [  50   67  124  209  214  229  288  337  380  402  437  474  566  584  614 |
|               |   661  754  840  846  894 1008]                                             |
| living        | [195 198 209 219 261 317 332 348 353 369 371 375 399 495 501 556 595 758    |
|               |  799 813 920]                                                               |
| local         | [  3  48 221 275 284 457 466 516 574 626 645 688 699 761 855 867 899 925    |
|               |  942 987 997]                                                               |
| misc          | [ 40  61  90 106 127 179 202 208 217 373 417 523 577 580 722 751 865 925    |
|               |  926 928 938]                                                               |
| msn-news      | [  29   71   72   74  149  241  261  263  276  365  465  528  529  575  577 |
|               |   661  781  799  830  980 1019]                                             |
| msn-sports    | [119 138 150 164 197 263 391 454 510 581 589 614 661 700 724 742 809 886    |
|               |  889 978 989]                                                               |
| news          | [  18   44   71  109  191  322  333  337  375  402  447  587  653  660  794 |
|               |   837  853  913  936  954 1019]                                             |
| on-air        | [  27   80  134  158  187  199  214  286  374  439  445  484  490  590  670 |
|               |   771  823  934  952  965 1014]                                             |
| opinion       | [163 165 216 241 251 260 307 336 382 449 493 540 607 668 679 717 736 866    |
|               |  888 902 981]                                                               |
| sports        | [  20   39   65  141  147  230  232  248  332  361  467  476  689  847  851 |
|               |   862  866  889  936  958 1010]                                             |
| summary       | [ 32  34 106 206 302 340 414 564 566 568 596 619 645 657 761 813 879 888    |
|               |  897 944 997]                                                               |
| tech          | [108 276 327 372 411 431 479 577 592 606 650 690 747 756 763 913 936 949    |
|               |  961 981 983]                                                               |
| travel        | [149 164 179 239 316 319 365 427 437 470 632 729 739 748 787 818 821 824    |
|               |  834 906 919]                                                               |
| weather       | [  9  12  21  38  45 146 203 205 284 400 471 506 520 532 595 613 621 639    |
|               |  805 970 987]                                                               |
+---------------+-----------------------------------------------------------------------------+

Start Learning page sequences using the first 10000 user sessions
Learned 10000 Sessions
Finished Learning

Start Inference using a new user session from the dataset
User Session to Predict:  ['on-air', 'misc', 'misc', 'misc', 'on-air', 'misc', 'misc', 'misc', 'on-air', 'on-air', 'on-air', 'on-air', 'tech', 'msn-news', 'tech', 'msn-news', 'local', 'tech', 'local', 'local', 'local', 'local', 'local', 'local']
+----------+---------------------------------------------------------------------------------------+
|   Page   | Prediction                                                                            |
+----------+---------------------------------------------------------------------------------------+
|  on-air  | ('on-air', 'misc', 'frontpage', 'news', 'summary', 'msn-news', 'weather', 'local')    |
+----------+---------------------------------------------------------------------------------------+
|   misc   | ('misc', 'frontpage', 'on-air', 'local', 'msn-news', 'msn-sports', 'news', 'sports')  |
+----------+---------------------------------------------------------------------------------------+
|   misc   | ('misc', 'frontpage', 'on-air', 'local', 'msn-news', 'msn-sports', 'news', 'sports')  |
+----------+---------------------------------------------------------------------------------------+
|   misc   | ('misc', 'frontpage', 'on-air', 'local', 'msn-news', 'msn-sports', 'news', 'sports')  |
+----------+---------------------------------------------------------------------------------------+
|  on-air  | ('on-air', 'misc', 'frontpage', 'news', 'summary', 'msn-news', 'weather', 'local')    |
+----------+---------------------------------------------------------------------------------------+
|   misc   | ('misc', 'frontpage', 'on-air', 'local', 'msn-news', 'msn-sports', 'news', 'sports')  |
+----------+---------------------------------------------------------------------------------------+
|   misc   | ('misc', 'frontpage', 'on-air', 'local', 'msn-news', 'msn-sports', 'news', 'sports')  |
+----------+---------------------------------------------------------------------------------------+
|   misc   | ('misc', 'frontpage', 'on-air', 'local', 'msn-news', 'msn-sports', 'news', 'sports')  |
+----------+---------------------------------------------------------------------------------------+
|  on-air  | ('on-air', 'misc', 'frontpage', 'news', 'summary', 'msn-news', 'weather', 'local')    |
+----------+---------------------------------------------------------------------------------------+
|  on-air  | ('on-air', 'misc', 'frontpage', 'news', 'summary', 'msn-news', 'weather', 'local')    |
+----------+---------------------------------------------------------------------------------------+
|  on-air  | ('on-air', 'misc', 'frontpage', 'news', 'summary', 'msn-news', 'weather', 'local')    |
+----------+---------------------------------------------------------------------------------------+
|  on-air  | ('on-air', 'misc', 'frontpage', 'news', 'summary', 'msn-news', 'weather', 'local')    |
+----------+---------------------------------------------------------------------------------------+
|   tech   | ('tech', 'frontpage', 'news', 'msn-news', 'on-air', 'business', 'local', 'sports')    |
+----------+---------------------------------------------------------------------------------------+
| msn-news | ('msn-news', 'frontpage', 'local', 'weather', 'misc', 'on-air', 'msn-sports', 'tech') |
+----------+---------------------------------------------------------------------------------------+
|   tech   | ('tech', 'frontpage', 'news', 'msn-news', 'on-air', 'business', 'local', 'sports')    |
+----------+---------------------------------------------------------------------------------------+
| msn-news | ('msn-news', 'frontpage', 'local', 'weather', 'misc', 'on-air', 'msn-sports', 'tech') |
+----------+---------------------------------------------------------------------------------------+
|  local   | ('local', 'frontpage', 'misc', 'news', 'msn-news', 'on-air', 'weather', 'sports')     |
+----------+---------------------------------------------------------------------------------------+
|   tech   | ('tech', 'frontpage', 'news', 'msn-news', 'on-air', 'business', 'local', 'sports')    |
+----------+---------------------------------------------------------------------------------------+
|  local   | ('local', 'frontpage', 'misc', 'news', 'msn-news', 'on-air', 'weather', 'sports')     |
+----------+---------------------------------------------------------------------------------------+
|  local   | ('local', 'frontpage', 'misc', 'news', 'msn-news', 'on-air', 'weather', 'sports')     |
+----------+---------------------------------------------------------------------------------------+
|  local   | ('local', 'frontpage', 'misc', 'news', 'msn-news', 'on-air', 'weather', 'sports')     |
+----------+---------------------------------------------------------------------------------------+
|  local   | ('local', 'frontpage', 'misc', 'news', 'msn-news', 'on-air', 'weather', 'sports')     |
+----------+---------------------------------------------------------------------------------------+
|  local   | ('local', 'frontpage', 'misc', 'news', 'msn-news', 'on-air', 'weather', 'sports')     |
+----------+---------------------------------------------------------------------------------------+
|  local   | ('local', 'frontpage', 'misc', 'news', 'msn-news', 'on-air', 'weather', 'sports')     |
+----------+---------------------------------------------------------------------------------------+

Compute prediction accuracy by checking if the next page in the sequence is within the predicted pages calculated by the model:
 - Prediction Accuracy: 0.614173228346
 - Accuracy Predicting Top 3 Pages: 0.825196850394

```

----------------------------------------------------------------------------------------
References:
- http://nupic.docs.numenta.org/stable/api/algorithms/encoders.html#nupic.encoders.category.CategoryEncoder
- http://nupic.docs.numenta.org/stable/api/opf/models.html#nupic.frameworks.opf.htm_prediction_model.HTMPredictionModel
- https://archive.ics.uci.edu/ml/datasets/MSNBC.com+Anonymous+Web+Data
- Lichman, M. (2013). UCI Machine Learning Repository [http://archive.ics.uci.edu/ml].
  Irvine, CA: University of California, School of Information and Computer Science

[1]: http://nupic.docs.numenta.org/stable/api/algorithms/encoders.html#nupic.encoders.category.CategoryEncoder
[2]: http://nupic.docs.numenta.org/stable/api/opf/models.html#nupic.frameworks.opf.htm_prediction_model.HTMPredictionModel
[3]: https://archive.ics.uci.edu/ml/datasets/MSNBC.com+Anonymous+Web+Data
[4]: http://archive.ics.uci.edu/ml
