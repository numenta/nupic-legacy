---
layout: blogpost
title: Predicting Movement with IR Sensors
guest: Erik Blas
category: news
---

### My Experience at the First NuPIC Hackathon

##### a guest blog post by **[{{ page.guest }}](https://github.com/ravaa)**

On April 24, 2013 Numenta hosted their first hackathon, a private event commemorating the recent release of NuPIC (Numenta Platform for Intelligent Computing) to the OSS world. 

You can find the project on [github](http://github.com/numenta/nupic), and more information on the the [main page of this site](http://numenta.org).

One could not begin to describe my initial excitement at receiving an invitation to attend. I've been inspired by Jeff Hawkin's work since I stumbled across his [2007 TED talk](http://www.ted.com/talks/jeff_hawkins_on_how_brain_science_will_change_computing.html), and later reading his book [On Intelligence](http://www.amazon.com/Jeff-Hawkins/e/B001KHNZ7C/ref=sr_ntt_srch_lnk_1?qid=1373225752&sr=8-1).

This being my first hackathon, I decided to just assume it was going to be like a typical crunch time day. Introduction pow wow and problem scoping, each person swarms or picks up their piece of the puzzle, and we go about the process of turning `b1p2` (1 beer to 2 pizza slices) into code. 

This pretty much took place in fits and starts, as this is the first initial offering of NuPIC we were working with. Documentation was (still is) sparse, and there were no community established workflows for getting new **OPF clients** off the ground. Up until just a few weeks prior, all the code we were working with was in use only for Grok Solutions' clients. 

Strangers in a strange land, we were.

There was a lot of confusion on just how to use the software. Numenta provided a [VM with pre-baked environments](https://github.com/numenta/nupic/wiki/Running-Nupic-in-a-Virtual-Machine) using Vagrant and Virtual Box. A few successfully built the software on their own platform of choice. The static binding of certain libs and some of the build steps had a propensity to make porting difficult, as well as the reliance on Python 2.6.8.

Once building was no longer an issue (in general), the next part was getting all of the tests and experiments running. Environment issues played the lead gremlin in this instance, but once the proper library paths were exported we were victorious! 

#### The OPF

The [Open Prediction Framework](https://github.com/numenta/nupic/wiki/Online-Prediction-Framework) ties together all the desperate parts of the CLA functions and HTM regions. To break it down, you're working with a data stream and its subsequent encoding. A data stream can be (and often is for pre-training) a CSV file, live streaming data, a generator, etc.. the OPF client doesn't care as long as it's iterable and returns a `sensorRecord` object.

A client takes the data stream, and feeds it to an instance of a model, one record at a time, which then returns your prediction result for the next N steps (depending on your model configuration). This result and a bunch of meta is stored for you in a dict known as a `modelResult`.

*Steps* here mean the feeding of 1 record into a model and its return of the `modelResult` object, not necessarily tied to clock time. Models can either be pre-trained and loaded from disk, or an instance of a new model.

#### Data and Encoders

A lot of us spent the majority of our time trying to figure the best encoding schema for our data, once we managed to wrap our heads around the OPF. This has remained true for all of my current projects with the OPF, and I suspect will be the stickiest point for other novices.

One has to be able to conceptualize your problem as a sequence, temporal or otherwise, and then piecemeal that sequence into individual parts, associative in some way to the inference you're looking for. For my demo, *[predepic](https://github.com/ravaa/nupic/tree/master/predipic)*, it turned out to be a simple classification problem: Which sensor shows the most activity, and thus indicates my position?

Once you get past this point, it's a matter of running test sequences and tweaking your **model parameters** (I may write more on this in a subsequent post).

### Demos

#### Watch the Footage

No, seriously [they're cool, and I cannot give them justice](http://numenta.org/news/2013/06/25/hackathon-outcome.html).

Here's mine:

<iframe class="youtube-player" type="text/html" width="600" height="385" src="http://www.youtube.com/embed/_bFmvlLmvcY?start=725" allowfullscreen="allowfullscreen" frameborder="0">
</iframe>
<br/>
<br/>

#### Implications Gleaned from the Demos

One key thing that jumped out at me, is the different types of data we were able to feed to NuPIC models, and achieve high value results. With the only real project-specific work being contained in model parameters! 

Everything from midi file data to record classification strings, and NuPIC munched on them all. All one needs is an encoder to handle the record types, and you can go far with the encoders provided by the OPF.

### Concluding Thoughts, and What I'm Up To

The immensely gracious hosting and helpfulness of the Numenta staff cannot be overstated! Beyond the gloriously delicious food, endless supply of beer and other essentials, and the ample and comfortable workspaces, the conversations over NuPIC and the work going forward blew me away the most. 

Special shout out to:
* [Ian](http://nupic.markmail.org/search/?q=from%3Aidanforth%40embodiedai.com), for lending me your parts and helping me refine my project! 
* [Matt](http://nupic.markmail.org/search/from:matt%40numenta.org), you're tireless work in the community is awesome man. Do you not sleep?
* [Jeff](http://nupic.markmail.org/search/from:jhawkins%40numenta.org), your efforts continue to inspire! Thank you, for opening this project to the community. 
* [Subutai](http://nupic.markmail.org/search/from:subutai%40numenta.org), for your conversations and explanations.
* [Scott](http://nupic.markmail.org/search/from:scott%40numenta.org), I'm not sure many of our projects would have gotten off the grown without your help and quick production of simple examples.
* Office Management Staff, for keeping us alive and making everyone feel at home!
* Pete, for not laughing at my lame html and javascript skills while simultaneously making my web console not suck.
* Winfried, for the fascinating discussions. I'm nerding out on the implications of your work!

Maybe it was the sleep deprivation (both leading up to and during the event), but I walked away with a whole new mindset. I'll never see anything the same way again. I look for the subtle sequencing behind it all, and wonder if I can encode it.

### *Woah*

At this point, I plan to continue solving the build problem. Having NuPIC build easily across platforms is vital for widespread adoption. We need more minds on this project to extend and improve our understanding of this model of intelligence. 

I'm also working on distributing model work load and selective evolution. I'll save the details for posts as I build and work on these, but the bit "selective evolution" bears some explanation.

Selective evolution of models is the idea of running multiple model instances, with the same encoders tuned differently, being fed the same data. One chooses the model with the best predictive performance to continue forward.

I'd recommend anyone interested head into the **<a href="irc://irc.freenode.net/nupic">#nupic</a>** channel on IRC and post to the mailing list. I can be found on IRC as @rava, and also [on the mailing list](http://nupic.markmail.org/search/?q=erik#query:erik%20from%3A%22Erik%20Blas). 

Also, here is [my personal fork of NuPIC](http://github.com/ravaa/nupic) (it's a mess in there).

> Erik Blas <br/>
> [Google+](https://plus.google.com/u/0/114228187192137856927/posts)

[Comments on Reddit]()