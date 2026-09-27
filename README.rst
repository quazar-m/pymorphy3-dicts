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

By default the original OpenCorpora URLs are used::

    https://opencorpora.org/files/export/dict/dict.opcorpora.xml.bz2
    https://opencorpora.org/files/export/annot/annot.opcorpora.xml.bz2

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

.. _pymorphy3: https://github.com/no-plagiarism/pymorphy3
.. _VESUM / dict_uk: https://github.com/brown-uk/dict_uk
