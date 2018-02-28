from parser import DataItem


class Converter(object):
    """docstring for Converter"""

    def __init__(self, marker_stream):
        super(Converter, self).__init__()
        self.mStream = marker_stream

    def toTRC(self, filename):
        FirstFrame = ms.startTime * ms.frequency
        LastFrame = ms.nFrames
        NumFrames = ms.nFrames
        nrows = LastFrame - FirstFrame + 1
        units = 'mm'
        f = ms.frequency

        # Comienzo la generación de los headers

        header1 = ['PathFileType', '4', '(X/Y/Z)', filename + '.trc']
        trc_header = []
        trc_header.append('\t'.join(header1) + '\n')

        header2 = ['DataRate', 'CameraRate', 'NumFrames', 'NumMarkers',
                   'Units', 'OrigDataRate', 'OrigDataStartFrame', 'OrigNumFrames']
        trc_header.append('\t'.join(header2) + '\n')

        header3 = [str(f), str(f), str(nrows), str(len(ms.track.keys())),
                   str(units), str(f), str(FirstFrame), str(LastFrame)]
        trc_header.append('\t'.join(header3) + '\n')

        header4 = ['Frame#', 'Time', '\t\t\t'.join(ms.track.keys())]
        trc_header.append('\t'.join(header4) + '\n')

        header5 = ['X' + str(x + 1) + '\tY' + str(x + 1) + '\tZ' +
                   str(x + 1) + '\t' for x, y in enumerate(ms.track.keys())]
        trc_header.append('\t\t' + "".join(header5) + '\n')
