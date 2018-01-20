# Web site link prediction / category prediction example:

This example shows how to use the [CategoryEncoder][1] with [HTMPredictionModel][2].

This model uses the [MSNBC.com Anonymous Web Data Data Set][3] provided by
[UCI Machine Learning Repository][4] to predict the next page the user is more
likely to click. Each page is assigned a category and the user behavior is
recorded as navigating from one page category to another. The dataset contains
one user session per line. See [dataset][3] description for more information.

For the purpose of this demonstration, the model will be trained on the
first 100 user sessions and try to predict a random session from the learned
sessions.
 
### Run with:
```  
python category.py
```

### Sample output:
```text
msn-news =>  [('msn-news', 0.7031011653364857), ('msn-sports', 0.098782932865573186), ('local', 0.09628347069810296), ('business', 0.036498954845523027), ('misc', 0.034768759842799299), ('on-air', 0.012582545969564769), ('tech', 0.010893265854891272), ('frontpage', 0.0009154183858699781)]
misc =>  [('misc', 0.97788222241832634), ('msn-news', 0.0071864481211450244), ('on-air', 0.0013848870313082704), ('weather', 0.0012649674683700371), ('frontpage', 0.0012326541657018705), ('local', 0.0011969337521356949), ('tech', 0.0011441419212440014), ('news', 0.00098610236045355111)]
misc =>  [('misc', 0.94555359706862396), ('msn-news', 0.018396834626330089), ('local', 0.0037233988351468841), ('on-air', 0.0033488069534847878), ('msn-sports', 0.0029782362605700343), ('weather', 0.0027037157246749687), ('frontpage', 0.002686636964143888), ('tech', 0.0024181861034995116)]
msn-news =>  [('msn-news', 0.9445268415131437), ('local', 0.012960467538507051), ('msn-sports', 0.0049154164342347503), ('tech', 0.0038496786122632423), ('misc', 0.0031394838323674165), ('on-air', 0.0030221992553965196), ('business', 0.0029327258767482484), ('living', 0.0027395156499587874)]
local =>  [('local', 0.95747948161613805), ('health', 0.0038068005820566285), ('weather', 0.0029171356157681448), ('on-air', 0.0028917931323782608), ('msn-news', 0.0028684922170422521), ('news', 0.0028495160686956853), ('misc', 0.0028390773338124241), ('tech', 0.0028110410214578318)]
local =>  [('local', 0.95460829898504818), ('health', 0.0041393892771206028), ('misc', 0.0035966504175385617), ('weather', 0.0034513649716954274), ('on-air', 0.0034357019196297176), ('msn-news', 0.00332153187543453), ('sports', 0.0029098119638373606), ('news', 0.002861324442412353)]
local =>  [('local', 0.95710911024407541), ('health', 0.0036670807364758261), ('misc', 0.0030526812454136406), ('news', 0.0030013483724507708), ('business', 0.0029610874617448562), ('sports', 0.0029034305013417943), ('on-air', 0.0028704531735915416), ('msn-news', 0.0028200202131798981)]
local =>  [('local', 0.95693590840081144), ('health', 0.0037110785325983903), ('misc', 0.0031163157539374283), ('frontpage', 0.0029947624235611738), ('on-air', 0.0029321341124427434), ('news', 0.0028891122328150664), ('sports', 0.0028222092649283288), ('weather', 0.0028188673279437013)]
local =>  [('local', 0.95094745833121752), ('misc', 0.0071280025645480919), ('health', 0.0041265473150833175), ('weather', 0.0036442575110895606), ('news', 0.0032163461815174167), ('msn-news', 0.0030830564735804342), ('business', 0.0030208749104647763), ('on-air', 0.0029563561063416116)]
misc =>  [('misc', 0.95764331862590035), ('local', 0.0053311633338171517), ('frontpage', 0.0033305186106399659), ('msn-news', 0.0032718939811115194), ('on-air', 0.0030047505736160609), ('weather', 0.0030045712783401406), ('living', 0.0025554224137823403), ('msn-sports', 0.0025419502621839142)]
local =>  [('local', 0.95298541093950784), ('on-air', 0.0056152438804696805), ('health', 0.0040221745708244232), ('tech', 0.0032120648624282214), ('news', 0.003097781445257828), ('msn-news', 0.0030880088317398443), ('misc', 0.0029669314591515028), ('sports', 0.0028788396613503892)]
on-air =>  [('on-air', 0.85282674731943664), ('msn-news', 0.053865322232753324), ('weather', 0.025778853090665126), ('misc', 0.021342451463348195), ('local', 0.020276010656154825), ('news', 0.014923541684664973), ('summary', 0.0036045879195257462), ('health', 0.0027994637450614993)]
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
