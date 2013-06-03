---
layout: blogpost
title: Introducing NuPIC
---

Welcome to the NuPIC open source project.  This is a good place to be if you are interested in machine intelligence and brain modeling.

I started studying brain theory over thirty years ago.  At that time most computer scientists didn’t think the brain was relevant to AI and most biologists thought the brain was so complicated that it would take hundreds of years to decipher how it works.  Today both these viewpoints have changed.  We are making good progress in understanding how the brain works and many people believe that emulating the brain is the best path to machine intelligence.

In 2005 I wrote a book (along with Sandra Blakeslee) that described the neocortex as a hierarchy of nearly identical memory regions where each region learns and recalls sequences.   Sequence memory is a huge part of how we understand the world.  We need sequence memory to understand speech, touch, and vision.  We also use it to generate behavior.  But learning sequences from millions of noisy sensory bits is tricky.  In 2009, after several years of studying this problem, we think we figured it out.  We now understand how hundreds of thousands of neurons (arranged in layers as observed in the neocortex) learn the spatial and temporal patterns in sensory data.  Since the fall of 2009 we tested this theory extensively and embedded the algorithms in a product called Grok.

We call the theory the Cortical Learning Algorithm (CLA) and the code we wrote to implement the CLA is the heart of NuPIC.  As of today you can access this code and experiment with and modify the CLA yourself.

In this blog entry I want to articulate my hopes and fears for NuPIC.  Let’s start with what I hope we will accomplish.

I hope NuPIC will accelerate the creation of machine intelligence.  The CLA is a unique theory of how large ensembles of real neurons work together in the neocortex.  If we are right about this, then the CLA is a major building block of biological intelligence and it will also be a major building block of machine intelligence.  Here’s a rough analogy -- going from understanding a single neuron to a layer of neurons is like going from an isolated transistor to an integrated circuit.

And just like a single integrated circuit is not a computer, the CLA is not an intelligent machine; it is just an important component.  There is a tremendous amount of work to be done.  We need to better characterize the CLA on how it works with different types of data.  We need to make the CLA faster in both HW and SW.  We need mathematical analysis of the CLA to know its theoretical limits.  We need to figure out how to use the CLA to generate motor behavior, something that is done in every region of the neocortex.  And we need to combine CLAs in hierarchies.  I hope NuPIC contributors will work on all these problems.

I hope some contributors will accelerate our progress by creating better documentation, better code examples, and better educational materials.   We need to create a reading list and references to relevant science papers.

And finally I hope that some people will embed NuPIC in clever new products.

Now my fears.  I fear that expectations will get ahead of reality.  Two years after my book was published I ran into someone at a conference.  He said he loved **On Intelligence** but was now disappointed.  He wanted to know why I had not made much progress since the book came out.  Let me be frank.  The CLA is based on novel concepts that present a steep learning curve.  This stuff is not easy.  I can assure you that once you understand it, you will see a beauty in it.  But most people take months to deeply understand the CLA.  The tasks of creating hierarchies of CLAs and adding in motor capabilities are very difficult.  Even just using the CLA in its current form is not trivial due to the learning required.

Understanding the brain and building fantastically intelligent machines is a grand quest for humanity.  It is worth struggling, overcoming obstacles, and working hard to achieve this quest.  If you want something quick and easy to work on, this isn’t it.  NuPIC is for those who are crazy enough to pursue grand dreams but who are grounded enough to make practical progress today.



> Jeff Hawkins <br/>
> Founder, Numenta Inc.