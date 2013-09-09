---
layout: blogpost
title: Build Artifacts
category: news
---

Our Travis-CI build is now publishing build artifacts to Amazon S3. You can access them by SHA by using the following URL format:

> https://s3-us-west-2.amazonaws.com/artifacts.numenta.org/numenta/nupic/build-${SHA}.tar.gz

For example, if you want to download the artifacts created by Travic-CI build [#668](https://travis-ci.org/numenta/nupic/builds/11138478), you'd need to get the SHA for that commit, which is [61454a8](http://github.com/numenta/nupic/commit/61454a8ca2d2a3cd2fdc4101f9e4028d61a53f5c) (as shown on the Travis-CI page). Simply replace `${SHA}` in the URL above with the complete SHA for the download:

> [https://s3-us-west-2.amazonaws.com/artifacts.numenta.org/numenta/nupic/build-61454a8ca2d2a3cd2fdc4101f9e4028d61a53f5c.tar.gz](https://s3-us-west-2.amazonaws.com/artifacts.numenta.org/numenta/nupic/build-61454a8ca2d2a3cd2fdc4101f9e4028d61a53f5c.tar.gz)

**WARNING**: Clicking the link above will start a 60MB download.