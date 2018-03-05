.. highlight:: python3
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
* Compatible with Python 2.7 and 3.4 onwards
* Linux, OSX and Windows support

simplemdx gives access to:

* trial MDXs (marker coordinates, emg channels, etc)
* session and patient MDXs (antropometric data, subject metadata)
* normative ENB files (joint angles normatives, emg normatives, etc)

Usage
-----

To load the contents of a trial mdx

.. code:: python

    from simplemdx.parser import Parser

    a = Parser('myfile.mdx')

Once loaded, metadata can be accessed like:

.. code:: python

    label = a.label
    date = a.date


It also loads all it's streams, and names them according to their contents. The named streams can be:

* markers
* emg
* static
* cycle


Streams
-------

Every stream has its own metadata(such as frequency, start time and number of frames

.. code:: python

    a = Parser('myfile.mdx')
    m = a.markers # marker stream

    m.freq
    m.nFrames
    m.startTime


Marker streams
--------------

Markers can be retrieved from the stream by index or label

.. code:: python

    c7 = a.markers['c7']
    m = a.markers[0] # The first marker on the stream

or iterated

.. code:: python

    for marker in a.markers:
        print(marker.label)

This stream can be converted to an OpenSIM .trc file like this

.. code:: python

    a.markers.toTRC()

By default, it creates a trc file with the same label as the trial mdx and all the included markers.
It is important to note that it will output the largest common chunk of data (the largest interval of time for which all markers are visible). This is to avoid None data in the .trc file. One can restrict the output to certain markers and change the output filename

.. code:: python

    a.markers.toTRC(filename='my_trc_output.trc',labels=['c7','rasis','lasis'])

As a simple way to inspect the stream, one can plot it

.. code:: python

    a.markers.plot()

This will display a simple matplotlib 3D scatter plot with the markers and the references

Data items
----------

The data for the streams inner tags are stored in DataItems. BTS follows an Item/Segment approach for storing most of it. For retrieving a segment of a marker, one can call the data attribute


.. code:: python

    c7 = a.markers['c7']
    s = c7.data

data will return a Segment object, or a list of Segment objects. Each Segment has a list for each coordinate (for a marker example, X, Y and Z) and the Segment's starting frame

.. code:: python

    seg = c7.data
    if isintance(seg,Segment):
        print("First frame: {}".format(seg.frame))
        print("X data: {}".format(seg.X))

addicionally, data can be retrieved as a continuous stream using datac instead of data. This will merge all segments into one, added a None padding. and return a single Segment starting at frame 0.

.. code:: python

    segc = c7.datac
    print("X data: {}".format(seg.X))


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
.. _BeautifulSoup: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
