#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script for updating pymorphy3 dictionaries (Russian and Ukrainian).

Please note that it is resource-heavy: it requires > 3GB free RAM and about
1GB on HDD for temporary files.

Usage:
    update.py (ru|uk) (download|compile|package|cleanup) ...
    update.py (ru|uk) all
    update.py -h | --help

Environment overrides:
    PYMORPHY3_RU_DICT_URL       Russian OpenCorpora dictionary archive URL/path
    PYMORPHY3_RU_CORPORA_URL    Russian OpenCorpora corpus archive URL/path
    PYMORPHY3_RU_DICT_SHA256    Optional SHA256 for the Russian dictionary
    PYMORPHY3_RU_CORPORA_SHA256 Optional SHA256 for the Russian corpus
    PYMORPHY3_UK_DICT_VERSION   VESUM release version (default: 6.8.6)
    PYMORPHY3_UK_DICT_URL       VESUM dict_corp_vis.txt.bz2 URL/path
    PYMORPHY3_UK_DICT_SHA256    Expected SHA256 (empty value disables checking)
"""
from __future__ import print_function

import bz2
import hashlib
import os
import shutil
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from docopt import docopt
from cookiecutter.main import cookiecutter
from pymorphy3 import opencorpora_dict


OUT_PATH = "compiled-dicts"

RU_DICT_URL = os.environ.get(
    "PYMORPHY3_RU_DICT_URL",
    "https://github.com/quazar-m/pymorphy3-dicts/releases/download/"
    "opencorpora-snapshot-2024/dict.opcorpora.xml.bz2",
)
RU_CORPORA_URL = os.environ.get(
    "PYMORPHY3_RU_CORPORA_URL",
    "https://github.com/quazar-m/pymorphy3-dicts/releases/download/"
    "opencorpora-snapshot-2024/annot.opcorpora.xml.bz2",
)

# Preserved source snapshots published in this fork.
_DEFAULT_RU_DICT_SHA256 = "f27150955c5f0978ece14348096f7d1380fc3564b08fdf99f129ede586309b6c"
_DEFAULT_RU_CORPORA_SHA256 = "dff2b07a3db865eb234515c3c2c51e370fc67b3582f32af7174625c8f2be4422"
RU_DICT_SHA256 = os.environ.get(
    "PYMORPHY3_RU_DICT_SHA256", _DEFAULT_RU_DICT_SHA256
) or None
RU_CORPORA_SHA256 = os.environ.get(
    "PYMORPHY3_RU_CORPORA_SHA256", _DEFAULT_RU_CORPORA_SHA256
) or None
RU_DICT_XML = "dict.opcorpora.xml"
RU_CORPORA_XML = "annot.corpus.xml"

UK_DICT_VERSION = os.environ.get("PYMORPHY3_UK_DICT_VERSION", "6.8.6")
UK_DICT_URL = os.environ.get(
    "PYMORPHY3_UK_DICT_URL",
    "https://github.com/brown-uk/dict_uk/releases/download/"
    "v{0}/dict_corp_vis.txt.bz2".format(UK_DICT_VERSION),
)
UK_DICT_TXT = "dict_corp_vis.txt"
UK_DICT_XML = "full-uk.xml"

# Published by GitHub for brown-uk/dict_uk release v6.8.6.
_DEFAULT_UK_SHA256 = "e33803783ac138e6f3af2cf0e9428ba146c0ecfda7f5c41fe83ae00c7af24be9"
if "PYMORPHY3_UK_DICT_SHA256" in os.environ:
    UK_DICT_SHA256 = os.environ["PYMORPHY3_UK_DICT_SHA256"] or None
elif UK_DICT_VERSION == "6.8.6":
    UK_DICT_SHA256 = _DEFAULT_UK_SHA256
else:
    UK_DICT_SHA256 = None


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as src:
        for chunk in iter(lambda: src.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(source, out_name, expected_sha256=None, retries=5):
    """Download/copy a file atomically and optionally verify SHA256."""
    part_name = out_name + ".part"
    last_error = None

    for attempt in range(1, retries + 1):
        if os.path.exists(part_name):
            os.unlink(part_name)

        try:
            if os.path.isfile(source):
                shutil.copyfile(source, part_name)
            else:
                request = Request(
                    source,
                    headers={
                        "User-Agent": (
                            "pymorphy3-dicts/1 "
                            "(+https://github.com/quazar-m/pymorphy3-dicts)"
                        )
                    },
                )
                with urlopen(request, timeout=120) as response, open(part_name, "wb") as dst:
                    shutil.copyfileobj(response, dst, 1024 * 1024)

            if not os.path.getsize(part_name):
                raise IOError("downloaded file is empty")

            actual_sha256 = _sha256(part_name)
            if expected_sha256 and actual_sha256.lower() != expected_sha256.lower():
                raise ValueError(
                    "SHA256 mismatch for {0}: expected {1}, got {2}".format(
                        source, expected_sha256, actual_sha256
                    )
                )

            os.replace(part_name, out_name)
            return actual_sha256

        except (HTTPError, URLError, OSError, ValueError) as exc:
            last_error = exc
            if os.path.exists(part_name):
                os.unlink(part_name)
            if attempt < retries:
                time.sleep(min(2 ** (attempt - 1), 8))

    raise RuntimeError(
        "Unable to download {0} after {1} attempts: {2}".format(
            source, retries, last_error
        )
    )


def _download_bz2(source, out_name, expected_sha256=None):
    archive_name = out_name + ".bz2"
    _download(source, archive_name, expected_sha256=expected_sha256)

    part_name = out_name + ".part"
    try:
        with bz2.open(archive_name, "rb") as src, open(part_name, "wb") as dst:
            shutil.copyfileobj(src, dst, 1024 * 1024)
        if not os.path.getsize(part_name):
            raise IOError("unpacked file is empty")
        os.replace(part_name, out_name)
    finally:
        if os.path.exists(part_name):
            os.unlink(part_name)
        if os.path.exists(archive_name):
            os.unlink(archive_name)


def _validate_xml(path):
    """Cheap sanity check: make sure a root XML element can be parsed."""
    try:
        parser = ET.iterparse(path, events=("start",))
        next(parser)
    except (ET.ParseError, StopIteration) as exc:
        raise ValueError("{0} does not look like valid XML".format(path)) from exc


class RussianBuilder(object):
    def download(self):
        print("Downloading OpenCorpora dictionary...")
        try:
            _download_bz2(
                RU_DICT_URL,
                RU_DICT_XML,
                expected_sha256=RU_DICT_SHA256,
            )
            _validate_xml(RU_DICT_XML)
        except Exception as exc:
            raise RuntimeError(
                "Russian dictionary source is unavailable. "
                "Set PYMORPHY3_RU_DICT_URL to a trusted mirror or local "
                "dict.opcorpora.xml.bz2 snapshot."
            ) from exc

        print("Downloading OpenCorpora corpus...")
        try:
            _download_bz2(
                RU_CORPORA_URL,
                RU_CORPORA_XML,
                expected_sha256=RU_CORPORA_SHA256,
            )
            _validate_xml(RU_CORPORA_XML)
        except Exception as exc:
            raise RuntimeError(
                "Russian corpus source is unavailable. "
                "Set PYMORPHY3_RU_CORPORA_URL to a trusted mirror or local "
                "annot.opcorpora.xml.bz2 snapshot."
            ) from exc
        print("")

    def compile(self):
        print("Compiling the dictionary")
        subprocess.check_call([
            "./build-dict.py", RU_DICT_XML, OUT_PATH,
            "--lang", "ru",
            "--corpus", RU_CORPORA_XML,
            "--source-name", "opencorpora.org",
            "--clear",
        ])
        print("")

    def package(self):
        print("Creating Python package")
        cookiecutter(
            template="cookiecutter-pymorphy3-dicts",
            no_input=True,
            overwrite_if_exists=True,
            extra_context={
                "lang": "ru",
                "lang_full": "Russian",
                "version": get_version(corpus=True, timestamp=False),
                "data_license": (
                    "`Creative Commons Attribution-Share Alike 3.0 "
                    "<https://creativecommons.org/licenses/by-sa/3.0/>`_"
                ),
            },
        )

    def cleanup(self):
        shutil.rmtree(OUT_PATH, ignore_errors=True)
        for path in (RU_DICT_XML, RU_CORPORA_XML):
            if os.path.exists(path):
                os.unlink(path)


class UkrainianBuilder(object):
    def download(self):
        print("Downloading VESUM {0} dictionary...".format(UK_DICT_VERSION))
        _download_bz2(
            UK_DICT_URL,
            UK_DICT_TXT,
            expected_sha256=UK_DICT_SHA256,
        )

        print("Converting VESUM dictionary to OpenCorpora XML...")
        subprocess.check_call(["lt_convert.py", UK_DICT_TXT, UK_DICT_XML])
        _validate_xml(UK_DICT_XML)
        print("")

    def compile(self):
        print("Compiling the dictionary")
        subprocess.check_call([
            "./build-dict.py", UK_DICT_XML, OUT_PATH,
            "--lang", "uk",
            "--source-name", "github.com/brown-uk/dict_uk",
            "--clear",
        ])
        print("")

    def package(self):
        print("Creating Python package")
        cookiecutter(
            "cookiecutter-pymorphy3-dicts",
            no_input=True,
            overwrite_if_exists=True,
            extra_context={
                "lang": "uk",
                "lang_full": "Ukrainian",
                "version": get_version(corpus=False, timestamp=True),
                "data_license": (
                    "`Creative Commons Attribution-NonCommercial-ShareAlike 4.0 "
                    "<https://creativecommons.org/licenses/by-nc-sa/4.0/>`_"
                ),
            },
        )

    def cleanup(self):
        shutil.rmtree(OUT_PATH, ignore_errors=True)
        for path in (UK_DICT_TXT, UK_DICT_XML):
            if os.path.exists(path):
                os.unlink(path)


def get_version(corpus=False, timestamp=False):
    meta = dict(opencorpora_dict.load(OUT_PATH).meta)
    if corpus:
        tpl = "{format_version}.{source_revision}.{corpus_revision}"
    else:
        tpl = "{format_version}.{source_revision}.1"
    if timestamp:
        tpl += ".%s" % (int(time.time()))
    return tpl.format(**meta)


if __name__ == "__main__":
    args = docopt(__doc__)

    if args["all"]:
        args["download"] = args["compile"] = args["package"] = True

    if args["ru"]:
        builder = RussianBuilder()
    elif args["uk"]:
        builder = UkrainianBuilder()
    else:
        raise ValueError("Language is not known")

    if args["download"]:
        builder.download()

    if args["compile"]:
        builder.compile()

    if args["package"]:
        builder.package()

    if args["cleanup"]:
        builder.cleanup()
