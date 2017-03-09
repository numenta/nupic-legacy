## Swarming

> Swarming is a process that automatically determines the best model for a given dataset. By "best", we mean the model that most accurately produces the desired output. Swarming figures out which optional components should go into a model (encoders, spatial pooler, temporal pooler, classifier, etc.), as well as the best parameter values to use for each component.

We have plans to replace the current swarming library with a more universal parameter search library. This codebase is currently unmaintained. We currently have no API documentation for it.

[![Swarming in NuPIC](http://img.youtube.com/vi/xYPKjKQ4YZ0/hqdefault.jpg)](http://www.youtube.com/watch?v=xYPKjKQ4YZ0)

- [Running Swarms](Running-Swarms)
- [Swarming Algorithm](Swarming-Algorithm)
