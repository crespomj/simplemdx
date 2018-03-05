=====
Usage
=====

To use simplemdx in a project::

    import simplemdx

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

=======
Streams
=======

Every stream has its own metadata, such as frequency, start time and number of frames::

	a = Parser('myfile.mdx')
	m = a.markers # marker stream

	m.freq
	m.nFrames
	m.startTime

==============
Marker streams
==============

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