{{ cookiecutter.distribution_name }}
==========================================================

{{ cookiecutter.lang_full }} dictionaries for `pymorphy3`_.

.. _pymorphy3: https://github.com/no-plagiarism/pymorphy3

Installation
------------

Install::

    $ pip install {{ cookiecutter.distribution_name }}

Usage
-----

To use these dictionaries with pymorphy3 create ``MorphAnalyzer`` with
``lang='{{ cookiecutter.lang }}'`` parameter::

    >>> import pymorphy3
    >>> morph = pymorphy3.MorphAnalyzer(lang='{{ cookiecutter.lang }}')

To get a path to the installed dictionary data use
``{{ cookiecutter.package_name }}.get_path()``.

Development
-----------

The build scripts are maintained at
https://github.com/quazar-m/pymorphy3-dicts. The repository doesn't contain
the dictionary data itself; data is fetched from the documented upstream
source and compiled during the release process.

License
-------

Python code in this package is MIT licensed.

The dictionary data is licensed under
{{ cookiecutter.data_license }}.
