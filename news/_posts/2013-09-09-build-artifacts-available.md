---
layout: blogpost
title: Build Artifacts
category: news
---

Our Travis-CI build is now publishing build artifacts to Amazon S3. You can access them by SHA by using the following URL format:

> https://s3-us-west-2.amazonaws.com/artifacts.numenta.org/numenta/nupic/nupic-linux64-${SHA}.tar.gz

For example, if you want to download the artifacts created by Travic-CI build [#678](https://travis-ci.org/numenta/nupic/builds/11200458), you'd need to get the SHA for that commit, which is [51baca9](http://github.com/numenta/nupic/commit/51baca950e9c7dd81d8f472723c88ca299dc4f0f) (as shown on the Travis-CI page). Simply replace `${SHA}` in the URL above with the complete SHA for the download:

> [https://s3-us-west-2.amazonaws.com/artifacts.numenta.org/numenta/nupic/nupic-linux64-51baca950e9c7dd81d8f472723c88ca299dc4f0f.tar.gz](https://s3-us-west-2.amazonaws.com/artifacts.numenta.org/numenta/nupic/nupic-linux64-51baca950e9c7dd81d8f472723c88ca299dc4f0f.tar.gz)

**WARNING**: Clicking the link above will start a 60MB download.
