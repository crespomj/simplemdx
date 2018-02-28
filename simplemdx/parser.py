# -*- coding: utf-8 -*-

"""Main module."""

from bs4 import BeautifulSoup, Tag
import logging
from past.builtins import basestring
from future.utils import iteritems
from datetime import datetime

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

    @property
    def data(self):
        return self.parse_data()

    @property
    def datac(self):
        return self.parse_data(cont=True)

    @property
    def description(self):
        return self._pnt['description']

    @property
    def label(self):
        return self._pnt['label']

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
        self.parse_data()
        return self.__dict__[at]

    def parse_data(self, cont=False):
        data = self._pnt['data']
        assert isinstance(data, basestring)

        # If it's a text Tag, don't parse
        if self._pnt.name == 'text':
            return data
        if self._pnt.name == 'mass':
            return int(data)

        # first: does it has items on it?
        if data.startswith("I "):
            return self.parse_items(data)

        # is it single item, multiple segments?
        if data.startswith("S "):
            return self.parse_segments(data, cont)

        # else, load the data to self.
        d = self.parse_coords(data)
        for n, c in enumerate(self.coords):
            if isinstance(d, list) and len(d) == 1:
                self.__dict__[c] = d[n][0]
            else:
                self.__dict__[c] = d

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
                # Create empty list of length (last segment's frame +
                # last segement's length)
                n = [None] * (lista.frame + len(lista))
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

    def __iter__(self):
        return iter(self.items)

    def append(self, i):
        self.items.append(i)

    @property
    def freq(self):
        return float(self.pnt['frequency'])

    def __len__(self):
        return len(self.items)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


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
            ('measureset', 'Measures set'))

        for j, k in d:
            self.__setattr__(j, self[k].data)

    @property
    def mass(self):
        return self['mTB'].data / self['mTB'].scaleFactor

    @property
    def height(self):
        return self['dTH'].data / self['dTH'].scaleFactor

    @property
    def birthday(self):
        return datetime.strptime(self['Birthday'].data, "%d/%m/%Y").date()

    @property
    def date(self):
        return datetime.strptime(self['Session date'].data, "%d/%m/%Y").date()


class Parser(object):
    def __init__(self, filename):
        self.norm = self.trial = self.sessionMDX = False
        self.filename = filename
        f = open(self.filename, 'rb')
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

        stream = self.root.find_all('track', label='c7')
        if stream:
            return MarkerStream(stream[0].parent)
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