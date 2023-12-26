# napari-psf-extractor

[![License GNU GPL v3.0](https://img.shields.io/pypi/l/napari-psf-extractor.svg?color=green)](https://github.com/hoogenboom-group/napari-psf-extractor/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-psf-extractor.svg?color=green)](https://pypi.org/project/napari-psf-extractor)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-psf-extractor.svg?color=green)](https://python.org)
[![tests](https://github.com/hoogenboom-group/napari-psf-extractor/workflows/tests/badge.svg)](https://github.com/hoogenboom-group/napari-psf-extractor/actions)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/napari-psf-extractor)](https://napari-hub.org/plugins/napari-psf-extractor)

<p align="center">
  <b>A simple plugin to extract precise models of the Point Spread Functions of images</b>
</p>

![starting-widget.png](assets%2Fstarting-widget.png)

----------------------------------

## Installation

To install `napari-psf-extractor`, you can use [pip]. First, run the following command to install the PSF-Extractor dependency:

```bash
pip install git+https://github.com/hoogenboom-group/PSF-Extractor@master
```

Once the dependency is installed, proceed to install the napari-psf-extractor plugin:
```bash
pip install napari-psf-extractor
```

Alternatively, you can also install the plugin directly through [napari-hub](https://www.napari-hub.org/plugins/napari-psf-extractor).

## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.
To provide a better understanding of the project's class structure, 
refer to the [diagram](https://excalidraw.com/#json=OnNq6zdySLQLvsN3Qttyl,LyPUf_FpsP5EeG98t40fXA) linked here.

## License

Distributed under the terms of the [GNU GPL v3.0] license,
"napari-psf-extractor" is free and open source software

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

----------------------------------

This [napari] plugin was generated with [Cookiecutter] using [@napari]'s [cookiecutter-napari-plugin] template.

[napari]: https://github.com/napari/napari
[Cookiecutter]: https://github.com/audreyr/cookiecutter
[@napari]: https://github.com/napari
[MIT]: http://opensource.org/licenses/MIT
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[GNU GPL v3.0]: http://www.gnu.org/licenses/gpl-3.0.txt
[GNU LGPL v3.0]: http://www.gnu.org/licenses/lgpl-3.0.txt
[Apache Software License 2.0]: http://www.apache.org/licenses/LICENSE-2.0
[Mozilla Public License 2.0]: https://www.mozilla.org/media/MPL/2.0/index.txt
[cookiecutter-napari-plugin]: https://github.com/napari/cookiecutter-napari-plugin

[file an issue]: https://github.com/hoogenboom-group/napari-psf-extractor/issues

[napari]: https://github.com/napari/napari
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/
