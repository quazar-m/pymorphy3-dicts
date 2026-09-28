pymorphy3-dicts
===============

Scripts for building and packaging dictionaries for `pymorphy3`_.

The repository contains build/update scripts and a cookiecutter package
template; dictionary data itself is downloaded from the corresponding upstream
projects.

Russian dictionary
------------------

The Russian build still uses the OpenCorpora XML format because
``build-dict.py`` and pymorphy3's probability builder are designed around it.

The historical OpenCorpora download endpoint is no longer reliable, so the
download code now:

* uses HTTPS;
* retries failed downloads;
* downloads atomically instead of piping ``curl`` into ``bunzip2``;
* validates that decompression/XML parsing succeeds;
* allows trusted mirrors or local snapshots to be supplied explicitly.

By default both Russian sources are served from the
`opencorpora-snapshot-2024`_ GitHub Release in this fork::

    https://github.com/quazar-m/pymorphy3-dicts/releases/download/opencorpora-snapshot-2024/dict.opcorpora.xml.bz2
    https://github.com/quazar-m/pymorphy3-dicts/releases/download/opencorpora-snapshot-2024/annot.opcorpora.xml.bz2

The release preserves the Internet Archive captures from
2024-04-23 12:25:38 UTC (dictionary) and
2024-06-24 22:27:34 UTC (annotated corpus). The release also contains
``SHA256SUMS`` and ``SOURCES.md`` with provenance information.

The build pins SHA256 by default::

    dict.opcorpora.xml.bz2:
      f27150955c5f0978ece14348096f7d1380fc3564b08fdf99f129ede586309b6c
    annot.opcorpora.xml.bz2:
      dff2b07a3db865eb234515c3c2c51e370fc67b3582f32af7174625c8f2be4422

This removes the default build dependency on both the live OpenCorpora host
and Internet Archive availability.

For a mirror or an offline build, override them::

    PYMORPHY3_RU_DICT_URL=/srv/mirror/dict.opcorpora.xml.bz2 \
    PYMORPHY3_RU_CORPORA_URL=/srv/mirror/annot.opcorpora.xml.bz2 \
    python update.py ru all

HTTP(S) mirror URLs work as well. Optional SHA256 pins can be supplied with
``PYMORPHY3_RU_DICT_SHA256`` and ``PYMORPHY3_RU_CORPORA_SHA256``.

A Russian build requires both files. The dictionary XML supplies morphology
and paradigms; the annotated corpus is used to estimate ``P(tag|word)``.

Ukrainian dictionary
--------------------

The obsolete Google Drive file is no longer used. Ukrainian data now comes
from the actively maintained `VESUM / dict_uk`_ releases.

The default pinned source is VESUM ``v6.8.6`` asset
``dict_corp_vis.txt.bz2``. Its published SHA256 is checked before conversion::

    e33803783ac138e6f3af2cf0e9428ba146c0ecfda7f5c41fe83ae00c7af24be9

The archive is decompressed locally and then converted to OpenCorpora XML with
LT3OpenCorpora before compilation::

    python update.py uk all

To build another VESUM release, set ``PYMORPHY3_UK_DICT_VERSION`` together
with the corresponding ``PYMORPHY3_UK_DICT_SHA256``. A custom/local source can
be selected with ``PYMORPHY3_UK_DICT_URL``.

Licensing
---------

Python code in this repository is MIT licensed.

Source dictionary data keeps its upstream license:

* OpenCorpora Russian data: CC BY-SA 3.0.
* Current VESUM Ukrainian data: CC BY-NC-SA 4.0.

Generated package README files receive the appropriate data license during the
build.

Build
-----

Install build requirements::

    pip install -r requirements-build.txt

Then run one of::

    python update.py ru all
    python update.py uk all

Individual ``download``, ``compile``, ``package`` and ``cleanup`` stages are
also supported.

After generating a package, build its wheel and source distribution locally::

    ./build-package.sh ru
    ./build-package.sh uk

The generated package's ``release.sh`` is build-only as well and runs
``python -m build .``. Publishing is intentionally handled separately.

.. _pymorphy3: https://github.com/no-plagiarism/pymorphy3
.. _VESUM / dict_uk: https://github.com/brown-uk/dict_uk
.. _opencorpora-snapshot-2024: https://github.com/quazar-m/pymorphy3-dicts/releases/tag/opencorpora-snapshot-2024
