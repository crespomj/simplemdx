# -*- coding: utf-8 -*-

"""Main module."""

from bs4 import BeautifulSoup, Tag
import logging
from past.builtins import basestring
from future.utils import iteritems
from datetime import datetime
from dateutil.relativedelta import relativedelta
from itertools import groupby
from future.moves.itertools import zip_longest
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, CheckButtons
from mpl_toolkits.mplot3d.proj3d import proj_transform

logging.basicConfig(level=logging.INFO)


class Segment(object):
    """Segment wrapper class"""

    def __getitem__(self, index):
        return self.__dict__[index]

    def __len__(self):
        if any(i for i, v in iteritems(self.__dict__) if isinstance(v, list)):
            return max(len(v) for k, v in iteritems(self.__dict__)
                       if k != 'frame' and not isinstance(v, float))
        return 1

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class DataItem(object):
    """docstring for DataItem"""

    def __init__(self, pnt):
        self._pnt = pnt
        self.data = self.parse_data()
        self.datac = self.parse_data(cont=True)

    # @property
    # def data(self):
    #     if '_data' not in dir(self):
    #         self._data = self.parse_data()
    #     return self._data

    # @property
    # def datac(self):
    #     if '_datac' not in dir(self):
    #         print("Entre")
    #         self._datac = self.parse_data(cont=True)
    #     return self._datac

    @property
    def valid(self):
        return [bool(i.X) for i in self.datac]

    @property
    def description(self):
        return self._pnt['description']

    @property
    def label(self):
        return self._pnt['label']

    @label.setter
    def label(self,val):
        self._pnt['label'] = val

    @property
    def coords(self):
        return self._pnt['coords'].split(' ')

    @property
    def nItems(self):
        return int(self._pnt['nItems'])

    @property
    def nPoints(self):
        return int(self._pnt['nPoints'])

    @property
    def nSegs(self):
        return int(self._pnt['nSegs'])

    @property
    def scaleFactor(self):
        return float(self._pnt['scaleFactor'])

    @property
    def name(self):
        return self._pnt.name

    def __getitem__(self, index):
        return self.data[index]

    def __getattr__(self, at):
        return self.__dict__[at]

    def parse_data(self, cont=False):
        data = self._pnt['data']
        assert isinstance(data, basestring)

        # If it's a text Tag, don't parse
        if self._pnt.name == 'text':
            return data
        # if self._pnt.name == 'mass':
        #     return int(data)

        # first: does it has items on it?
        if data.startswith("I "):
            return self.parse_items(data)

        # is it single item, multiple segments?
        if data.startswith("S "):
            return self.parse_segments(data, cont)

        # else, load the data to self.
        d = self.parse_coords(data)
        if isinstance(d,list):
            for n,c in enumerate(self.coords):
                self.__setattr__(c,d[n])
        else:
            self.__setattr__(self.coords[0],d)

        return d

    def parse_items(self, data):
        # does it has any segments?
        if data.startswith("S "):
            logging.debug("%s has %s item(s)",
                          self.__class__.__name__, len(data))
            lista = [self.parse_segments(item)
                     for item in data.split("I ")[1:]]
            if len(lista) == 1:
                return lista[0]
            return lista
        else:
            lista = [self.parse_coords(item) for item in data.split("I ")[1:]]
            if len(lista) == 1:
                return lista[0]
            return lista

    def formatter(self, data):
        g = float if '.' in data else int
        return list(map(g, filter(None, data.split(' '))))

    def parse_segments(self, item, cont=False):
        segments = []
        for i in item.split("S ")[1:]:
            s = Segment()
            d = i.split(' ', 1)
            s.frame = int(d[0])
            dat = self.parse_coords(d[1])
            if len(self.coords) != 1:
                for index, coord in enumerate(self.coords):
                    s.__setattr__(coord, dat[index])
            else:
                s.__setattr__(self.coords[0], dat)

            segments.append(s)
        logging.debug("Item has %s segment(s)", len(segments))
        if cont:
            # Look for the segment with greater frame (last segment usually)
            lista = sorted(segments, key=lambda x: x.frame, reverse=True)[0]
            ja = Segment()
            ja.frame = 0
            # Load segments into empty segment
            for coord in self.coords:
                # Create empty list of the length of the stream
                n = [None] * int(self._pnt.parent['nFrames'])
                for i in segments:
                    dat = getattr(i, coord)
                    if isinstance(dat, list):
                        n[i.frame:(i.frame + len(i))] = getattr(i, coord)
                    else:
                        n[i.frame:(i.frame + len(i))] = [getattr(i, coord)]
                ja.__setattr__(coord, n)
            return ja

        if len(segments) == 1:
            return segments[0]
        return segments

    def parse_coords(self, data):
        lista = []
        # give the data a format (int, char, date, whatever)
        sc = self.scaleFactor
        d = self.formatter(data)

        for n, c in enumerate(self.coords):
            j = [i / sc for i in d[n::len(self.coords)]]
            if len(j) == 1:
                lista.append(j[0])
            else:
                lista.append(j)

        if len(lista) == 1:
            return lista[0]
        return lista

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class Stream(object):
    """docstring for Stream"""

    def __init__(self, pnt=None):
        self.items = []
        if pnt:
            self.pnt = pnt
            self.load(pnt)

    def load(self, pnt):
        for i in (j for j in pnt if isinstance(j, Tag)):
            logging.debug('Adding %s label %s', i.name, i['label'])
            self.items.append(DataItem(i))

    def __getitem__(self, index):
        if isinstance(index, int):
            return self.items[index]
        elif isinstance(index, basestring):
            lista = [i for i in self.items if i.label == index]
            if not lista:
                raise KeyError("Cannot find %s in the stream", index)
            if len(lista) == 1:
                return lista[0]
            return lista

    def __getattr__(self,val):
        return self[val]

    def __iter__(self):
        return iter(self.items)

    def append(self, i):
        self.items.append(i)

    def labels(self):
        return [i.label for i in self.items]

    @property
    def freq(self):
        return float(self.pnt['frequency'])

    def __len__(self):
        return len(self.items)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def longest_common_chunk(self, labels=None):
        """Returns the longest period of time in which all
        coordinates of all DataItems are visible"""

        def f(x):
            return True if x is not None else False

        if labels:
            items = [self[i] for i in labels]
        else:
            items = self.items

        res = map(f, items[0].datac.X)
        for i in items:
            li = map(f, i.datac.X)
            res = (a and b for a, b in zip_longest(res, li, fillvalue=False))

        # Enumerate the list, group by True/False,
        # filter by True, get the max length
        j = max(((lambda y: (y[0][0], len(y)))(list(g)) for k, g in groupby(
            enumerate(res), lambda x: x[1]) if k), key=lambda z: z[1])
        # j => (position,length)
        return j

    @property
    def startTime(self):
        return int(self.pnt['startTime'])

    @property
    def nFrames(self):
        return int(self.pnt['nFrames'])


class MarkerStream(Stream):
    """docstring for MarkerStream"""

    def __init__(self, pnt):
        self.references = Stream()
        self.angle3d = Stream()
        self.angle = Stream()
        super(MarkerStream, self).__init__(pnt)

    def load(self, pnt):
        for i in (j for j in pnt if isinstance(j, Tag)):
            if i.name == 'track':
                logging.debug('Adding marker label %s', i['label'])
                self.items.append(DataItem(i))
            elif i.name == 'reference':
                logging.debug('Adding reference label %s', i['label'])
                self.references.append(DataItem(i))
            elif i.name == 'angle3d':
                logging.debug('Adding angle3d label %s', i['label'])
                self.angle3d.append(DataItem(i))
            elif i.name == 'angle':
                logging.debug('Adding angle label %s', i['label'])
                self.angle.append(DataItem(i))
            else:
                logging.warning("Where should %s %s be put?",
                                i.name, i['label'])

    def __getitem__(self, index):
        if isinstance(index, int):
            return self.items[index]
        elif isinstance(index, basestring):
            lista = [i for i, v in enumerate(self.items) if v.label == index]
            if len(lista) == 1:
                return self.items[lista[0]]
            raise KeyError("More than one marker with label %s", index)

    def toPandas(self):
        ini, leng = self.longest_common_chunk()

        dat = {}
        for i in self.items:
            dat[i.label] = {}
            for c in ['X', 'Y', 'Z']:
                dat[i.label][c] = i.datac[c]
        return dat

    def plot(self, labels=None):
        # inipos,rang = self.longest_common_chunk()
        if labels:
            items = [self[i] for i in labels]
        else:
            items = self.items
            labels = self.labels()

        inipos = 0
        rang = max(len(i.datac.X) for i in self.items)

        def update_graph(num):
            num = int(num)
            for i in items:
                data = self[i.label].datac
                X = data.X[num:1 + num]
                Y = data.Y[num:1 + num]
                Z = [-j if j else None for j in data.Z[num:1 + num]]
                if not (X[0] and Y[0] and Z[0]):
                    X[0] = Y[0] = Z[0] = 0
                    graphs[i.label].set_visible(False)
                    graphs[i.label].set_data(X, Z)
                    graphs[i.label].set_3d_properties(Y)
                else:
                    graphs[i.label].set_visible(True and check.get_status()[0])
                    graphs[i.label].set_data(X, Z)
                    graphs[i.label].set_3d_properties(Y)
            for i in self.references.items:
                data = self.references[i.label].datac
                X = data.X[num:1 + num]
                Y = data.Y[num:1 + num]
                Z = [-j if j else None for j in data.Z[num:1 + num]]
                if not (X[0] and Y[0] and Z[0]):
                    X[0] = Y[0] = Z[0] = 0
                    rraphs[i.label].set_visible(False)
                    rraphs[i.label].set_data(X, Z)
                    rraphs[i.label].set_3d_properties(Y)
                else:
                    rraphs[i.label].set_visible(True and check.get_status()[1])
                    rraphs[i.label].set_data(X, Z)
                    rraphs[i.label].set_3d_properties(Y)
            title.set_text('3D Markers Plot, time={}'.format(
                (inipos + num) / self.freq))

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.axis('scaled')
        ax.set_xlim([-2, 2])
        ax.set_ylim([-1, 1])
        fig.tight_layout(True)

        title = ax.set_title('3D Markers Plot')

        axamp = plt.axes([0.25, .03, 0.50, 0.04])
        samp = Slider(axamp, 'Time', inipos, rang - 1, valinit=0)
        samp.on_changed(update_graph)

        rax = plt.axes([0.05, 0.4, 0.1, 0.15])
        check = CheckButtons(rax, ('markers', 'references'), (True, True))

        def func(label):
            status = check.get_status()
            for i in graphs.values():
                i.set_visible(i.get_visible() and status[0])
            for i in rraphs.values():
                i.set_visible(i.get_visible() and status[1])
            fig.canvas.draw_idle()

        check.on_clicked(func)

        graphs = {}
        rraphs = {}
        for i in items + self.references.items:
            X = Y = Z = [0]
            if i.name == 'track':
                g, = ax.plot(
                    X, Z, Y, label=i.label, linestyle="", marker="o", picker=5)
                g.set_visible(False)
                graphs[i.label] = g
            elif i.name == 'reference':
                r, = ax.plot(
                    X, Z, Y, label=i.label, linestyle="", marker="o", picker=5)
                r.set_visible(False)
                rraphs[i.label] = r

        annot = ax.annotate("", xy=(0, 0), xytext=(20, 20),
                            textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="w"),
                            arrowprops=dict(arrowstyle="->"))

        annot.set_visible(False)

        def hover(event):
            vis = annot.get_visible()
            for curve in ax.get_lines():
                cont, ind = curve.contains(event)
                if cont and curve.get_visible():
                    annot.xy = (event.xdata, event.ydata)
                    annot.set_text(curve.get_label())
                    annot.get_bbox_patch().set_facecolor(curve.get_color())
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                else:
                    if vis:
                        annot.set_visible(False)
                        fig.canvas.draw_idle()

        fig.canvas.mpl_connect('motion_notify_event', hover)
        plt.show()

    def toTRC(self, filename=None, labels=None):
        """ Converts markerStream to an OpenSIM trc's file
            To avoid NaN values, the longest common chunk is used """

        if not filename:
            filename = self.pnt.parent['label'][:-4] + '.trc'

        if labels:
            items = []
            for i in labels:
                items.append(self[i])
        else:
            items = self.items
            labels = self.labels()

        freq = self.freq
        ind, rang = self.longest_common_chunk(labels)

        if not filename.endswith(".trc"):
            filename = filename + ".trc"

        firstFrame = ind
        lastFrame = ind + rang

        nrows = lastFrame - firstFrame + 1
        units = 'm'

        # Starting header generation

        header1 = ['PathFileType', '4', '(X/Y/Z)', filename]
        trc_header = []
        trc_header.append('\t'.join(header1) + '\n')

        header2 = ['DataRate', 'CameraRate',
                   'NumFrames', 'NumMarkers',
                   'Units', 'OrigDataRate',
                   'OrigDataStartFrame', 'OrigNumFrames']

        trc_header.append('\t'.join(header2) + '\n')

        header3 = [str(freq), str(freq), str(nrows), str(nrows),
                   str(units), str(freq), str(firstFrame), str(lastFrame)]
        trc_header.append('\t'.join(header3) + '\n')

        header4 = ['Frame#', 'Time', '\t\t\t'.join(labels)]
        trc_header.append('\t'.join(header4) + '\n')

        header5 = ['X' + str(x + 1) + '\tY' + str(x + 1) + '\tZ' +
                   str(x + 1) + '\t' for x, y in enumerate(labels)]
        trc_header.append('\t\t' + "".join(header5) + '\n')

        def linewriter():
            """ Data line generator """
            f = ind
            while f < lastFrame:
                frameAndTime = "{}\t{:.2f}".format(f, f / freq)
                xyz = "\t".join("{}\t{}\t{}".format(
                    i.datac.X[f], i.datac.Y[f], i.datac.Z[f]) for i in items)
                yield("{}\t{}\n".format(frameAndTime, xyz))
                f = f + 1

        lines = linewriter()

        with open(filename, 'w') as file:
            for row in trc_header:
                file.write("%s" % row)

            for l in lines:
                file.write("%s" % l)


class emgStream(Stream):
    """docstring for emgStream"""

    def __init__(self, pnt):
        super(emgStream, self).__init__(pnt)

    def __getitem__(self, index):
        if isinstance(index, int):
            return self.items[index]
        elif isinstance(index, basestring):
            return [i for i in self.items if i.label == index][0]


class sessionMDXstream(Stream):
    """docstring for sessionMDXstream"""

    def __init__(self, pnt):
        super(sessionMDXstream, self).__init__(pnt)

        d = (
            ('name', 'First name'),
            ('lastname', 'Last name'),
            ('pathology', 'Pathology'),
            ('clinician', 'Clinician'),
            ('taxid', 'Tax ID'),
            ('address', 'Address'),
            ('phone', 'Phone number'),
            ('sex', 'Sex'),
            ('code', 'Internal code'),
            ('patient_notes', 'Patient notes'),
            ('session_notes', 'Session notes'),
            ('filename', 'File name'),
            ('protocol', 'Protocol'),
            ('measureset', 'Measures set'),
            ('mass','mTB'),
            ('height','dTH'),
            ('asis_breadth','dAB'),
            ('right_pelvis_depth','dRPD'),
            ('left_pelvis_depth','dLPD'),
            ('right_leg_length','dRLL'),
            ('left_leg_length','dLLL'))

        for j, k in d:
            self.__setattr__(j, self[k].data)

    @property
    def birthday(self):
        return datetime.strptime(self['Birthday'].data, "%d/%m/%Y").date()

    @property
    def date(self):
        return datetime.strptime(self['Session date'].data, "%d/%m/%Y").date()

    @property
    def age(self):
        return relativedelta(self.date, self.birthday).years


class Parser(object):
    def __init__(self, filename):
        self.norm = self.trial = self.sessionMDX = False
        self.filename = filename
        with open(self.filename, 'rb') as f:
            self.soup = BeautifulSoup(f.read().decode('utf-8'), 'lxml-xml')
        trial = self.soup.emxDataFile.find('trial')
        if trial:
            self.root = trial
            # Checking if session_mdx
            t = trial.static.find('text')
            if t and t['IDlabel']:
                logging.info("Session MDX detected")
                self.sessionMDX = True
            else:
                logging.info("Trial MDX detected")
                self.trial = True

            if self.format == "1.1":
                self.date = datetime.strptime(trial['date'], "%d/%m/%Y").date()
            else:
                self.date = datetime.strptime(trial['date'], "%d-%m-%Y").date()
            self.description = trial['description']
            self.label = trial['label']
            self.time = datetime.strptime(
                trial['time'], "%H:%M:%S").time() if trial['time'] else None

        norm = self.soup.emxDataFile.norm
        if norm:
            logging.info("Normative ENB detected")
            self.norm = True
            self.root = norm

    @property
    def format(self):
        return self.soup.emxDataFile['format']

    @property
    def sourceApp(self):
        return self.soup.emxDataFile['sourceApp']

    @property
    def markers(self):
        if not self.trial:
            raise KeyError("Marker stream available only on a trial MDX")

        if "_markerStream" in dir(self):
            return self._markerStream

        stream = self.root.find_all('track', label='c7')
        if stream:
            self._markerStream = MarkerStream(stream[0].parent)
            return self._markerStream
        else:
            raise KeyError("Could not find a marker stream")

    @property
    def emg(self):
        if not self.trial:
            raise KeyError("EMG stream available only on a trial MDX")

        stream = self.root.find_all('emg')
        if stream:
            return emgStream(stream[0].parent)
        else:
            raise KeyError("Could not find an emg stream")

    @property
    def static(self):
        stream = self.root.static
        if stream:
            return Stream(stream)
        else:
            raise KeyError("Could not find a static stream")

    @property
    def cycle(self):
        stream = self.root.cycle
        if stream:
            return Stream(stream)
        else:
            raise KeyError("Could not find a cycle stream")

    @property
    def session(self):
        if self.sessionMDX:
            stream = self.root.static
            if stream:
                return sessionMDXstream(stream)


if __name__ == '__main__':
    a = Parser('../tests/test_files/2148~aa~Descalzo con bastón.mdx')
    # for i in m.references:
    #     print(i.label)
    print(a.session.age)