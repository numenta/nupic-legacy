## The Online Prediction Framework (OPF)

The OPF is a Python-only convenience library that uses the [Network API](network.html). The primary classes it exposes to users are the [`CLAModel`](opf-models.html#clamodel) and the [`ModelFactory`](opf-models.html#modelfactory).

Online Prediction Framework (OPF) is a framework for working with and deriving predictions from online learning algorithms, including HTM. OPF is designed to work in conjunction with a larger architecture, as well as in a standalone mode (i.e. directly from the command line). It is also designed such that new model algorithms and functionalities can be added with minimal code changes.

More complete documentation on the OPF can be found on the [Online Prediction Framework](https://github.com/numenta/nupic/wiki/Online-Prediction-Framework) wiki page. Here are some examples of applications using the OPF interface:

- [`examples/opf/clients/cpu`](https://github.com/numenta/nupic/tree/master/examples/opf/clients/cpu)
- [`examples/opf/clients/hotgym/prediction/one_gym`](https://github.com/numenta/nupic/tree/master/examples/opf/clients/hotgym/prediction/one_gym)
- [`examples/opf/clients/hotgym/anomaly`](https://github.com/numenta/nupic/tree/master/examples/opf/clients/hotgym/anomaly)
- [`examples/opf/clients/hotgym/anomaly/one_gym`](https://github.com/numenta/nupic/tree/master/examples/opf/clients/hotgym/anomaly/one_gym)
