===============
simplemdx
===============


.. image:: https://img.shields.io/pypi/v/simplemdx.svg
        :target: https://pypi.python.org/pypi/simplemdx

.. image:: https://img.shields.io/travis/marnunez/simplemdx.svg
        :target: https://travis-ci.org/marnunez/simplemdx

.. image:: https://ci.appveyor.com/api/projects/status/xb07amo9s7stk37r?svg=true
     :target: https://ci.appveyor.com/project/marnunez/simplemdx
     :alt: Windows build status

.. image:: https://readthedocs.org/projects/simplemdx/badge/?version=latest
        :target: https://simplemdx.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/marnunez/simplemdx/shield.svg
     :target: https://pyup.io/repos/github/marnunez/simplemdx/
     :alt: Updates

.. image:: https://coveralls.io/repos/github/marnunez/simplemdx/badge.svg?branch=master
     :target: https://coveralls.io/github/marnunez/simplemdx?branch=master
     :alt: Coverage




A simple BTS MDX file parser and toolkit written in Python based on BeautifulSoup_


* Free software: GNU General Public License v3
* Documentation: https://simplemdx.readthedocs.io.


Features
--------

simplemdx gives access to:

* trial MDXs (marker coordinates, emg channels, etc)
* session and patient MDXs (antropometric data, subject metadata)
* normative ENB files (joint angles normatives, emg normatives, etc)

Usage
-----

To load the contents of a trial mdx::

    from simplemdx.parser import Parser

    a = Parser('myfile.mdx')

Once loaded, you can access its metadata::

    label = a.label
    date = a.date

It also loads all it's streams, and names them according to their contents. The named streams can be:

* markers
* emg
* static
* cycle


Streams
-------

Every stream has its own metadata, such as frequency, start time and number of frames::

    a = Parser('myfile.mdx')
    m = a.markers # marker stream

    m.freq
    m.nFrames
    m.startTime


Marker streams
--------------

Markers can be retrieved from the stream by index or label::

    c7 = a.markers['c7']
    m = a.markers[0] # The first marker on the stream

This stream can be converted to an OpenSIM .trc file like this::

    m.toTRC()

By default, it creates a trc file with the same label as the trial mdx and all the included markers. It's important to note that it will output the largest common chunk of data (the largest interval of time for which all markers are visible). This is to avoid None data in the .trc file. One can restrict the output to certain markers and change the output filename::

    m.toTRC(filename='my_trc_output.trc',labels=['c7','rasis','lasis'])

As a simple way to inspect the stream, one can plot it::

    m.plot()

will display a simple matplotlib scatter plot with the markers and the references

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
.. _BeautifulSoup: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
