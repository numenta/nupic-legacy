---
layout: blogpost
title: CLA Quiz Office Hour
category: blog
---

Tomorrow at 4PM Pacific, we're holding an [Office Hour](https://plus.google.com/b/100642636108337517466/events/crmrf6k58s77hlgk4v30bll8hp8) for anyone interested to join in and talk about the [Cortical Learning Algorithms]({{ site.baseurl/cla-white-paper.html }}), as implemented by Numenta within [NuPIC]({{ site.baseurl/nupic.html }}). Jeff Hawkins and Numenta VP of Engineering Subutai Ahmad will be at this event to go through the _CLA Quiz_, a serious of challenging questions about how NuPIC algorithms work. These questions were originally created for new employees and interns to research in order to better understand the CLA. Tomorrow, we're going to be asking you!

If you're interested in taking part, or just joining in to listen, please use your Google account and request an RSVP to our [Office Hour](https://plus.google.com/b/100642636108337517466/events/crmrf6k58s77hlgk4v30bll8hp8). We'll be happy to invite you. If you can't make it, the video will be <a href="http://www.youtube.com/watch?v=rSpYyUN4iP0" rel="prettyPhoto" title="NLP With NuPIC">posted on YouTube</a>.

### The CLA Quiz

<ol start="0">
    <li>
        <p/>Is an untrained CLA spatial pooler just a “random hash” (random mapping from input to output vector)?  Why or why not? What happens to the output of the spatial pooler if you randomly change one bit in the input.
    </li>
    <li>
        <p/>Can you do spatial pooling with small numbers?  For example, is it reasonable to have an SP with 20 columns? If not, why are large numbers important in SDR's?
        <ol type="a">
            <li>
                <p/>What's the difference between picking "5 columns out of 50" vs "50 out of 500"?  Both have 10% sparsity.
            </li>
            <li>
                <p/>What's the difference between picking "50 out of 100" vs "50 out of 1000"? Both will output 50 1's.
            </li>
        </ol>
    </li>
    <li>
        <p/>Suppose the input vector (input to the SP) is 10,000 bits long, with 5% sparsity. What is the right value of coincInputPoolPct? How do you figure this out?
    </li>
    <li>
        <p/>How does the SDR representation of input A in isolation, and input B in isolation, compare with the SDR representation of input A overlapped with B?  Alternatively, how does the representation of a horizontal line and the representation of a vertical line compare with the representation of a cross?
    </li>
    <li>
        <p/>Suppose we have an input vector that is 10,000 bits long.  Suppose the spatial pooler has 500 columns, of which 50 are active at any time.
        <ol type="a">
            <li>
                <p/>Can we distinguish many patterns, or a small number? Which patterns are likely to be confused? 
            </li>
            <li>
                <p/>What happens to the SDR representation if we add noise to the patterns?
            </li>
            <li>
                <p/>What happens if we add occlusions?
            </li>
        </ol>
    </li>
    <li>
        <p/>What are disadvantages of SDR's?
    </li>
    <li>
        <p/>How does online learning happen in the SP?
    </li>
</ol>

<br/>
<br/>

#### Whoa! that's deep

These questions a bit over your head? Looking for a primer on these technologies before you attend? Here are some resources:

<ul>
    <li>
        <a href="{{ site.baseurl }}/cla-white-paper.html">CLA White Paper</a>
    </li>
    <li>
        <a href="http://www.youtube.com/watch?v=z6r3ekreRzY" rel="prettyPhoto" title="">Tutorial: CLA Basics</a>
    </li>
    <li>
        <a href="http://www.youtube.com/watch?v=QBs-2_wl_JM" rel="prettyPhoto" title="CLA Deep Dive">CLA Deep Dive</a>
    </li>
</ul>

<br/>

> Matt Taylor <br/>
> Open Source Community Flag-Bearer <br/>
> Numenta, Inc.

[Comments on Reddit](http://www.reddit.com/r/MachineLearning/comments/1qdu8i/cla_quiz_office_hour/)