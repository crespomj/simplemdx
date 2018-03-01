#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `simplemdxparser` package."""

import pytest

from click.testing import CliRunner

from simplemdx import cli

import os
from datetime import date, time
from simplemdx.parser import Segment, Stream, MarkerStream, emgStream, Parser
from past.builtins import basestring


test_files_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'test_files')


class TestParser(object):
    """pytest class for the parser"""

    def trialMDX(self):
        return Parser(os.path.join(test_files_dir, u'1477~ac~Walking 01.mdx'))

    def sessionMDX(self):
        return Parser(os.path.join(test_files_dir, u'2148~aa~Descalzo con bastón.mdx'))

    def test_parse_trialMDX(self):
        a = self.trialMDX()
        assert a.format == '0.1'
        assert a.sourceApp == 'Viper'

        assert a.trial
        assert not a.norm
        assert a.date == date(2000, 1, 1)
        assert a.time == time(0, 0, 0)
        assert a.label == '1477~ac~Walking 01.tdf'
        assert a.description == "SMART acquisition"

    def test_trial_markers(self):
        a = self.trialMDX()
        assert isinstance(a.markers, MarkerStream)
        assert len(a.markers) == 53 == len(a.markers.items)
        assert len(a.markers.references) == 16

        c7 = a.markers['c7']
        assert c7 == a.markers[0]
        assert c7.name == 'track'
        assert isinstance(c7.label, basestring)
        assert c7.nSegs == len(c7.data) == 2
        assert c7.nPoints == sum(len(i) for i in c7.data) == 532

        dc = c7.datac
        assert isinstance(dc, Segment)
        assert len(dc.X) == len(c7.data[-1].X) + c7.data[-1].frame
        assert len(dc.Y) == len(c7.data[-1].Y) + c7.data[-1].frame
        assert len(dc.Z) == len(c7.data[-1].Z) + c7.data[-1].frame

    def test_trial_emg(self):
        a = self.trialMDX()
        assert isinstance(a.emg, emgStream)
        assert a.emg[0] == a.emg['Left Rectus femoris']
        assert isinstance(a.emg[0].data, Segment)
        assert a.emg[0].data.frame == 0
        assert len(a.emg[0].data.V) == 10253

        # If single segment, data == datac
        assert a.emg[0].data.V == a.emg[0].datac.V

    def test_trial_events(self):
        a = self.trialMDX()
        assert a.static['eLHS'].data == [3.81, 4.73]
        assert a.static['eLTO'].data == 4.36
        assert a.static['eRTO'].data == 4.83

    def test_parseSessionMDX(self):
        a = self.sessionMDX()
        assert a.session.name == u'CACHO'
        assert a.session.lastname == u'CASTAÑA'
        assert a.session.birthday == date(1959, 12, 1)

    def test_Segment(self):
        # a = Segment()
        pass


@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')


# def test_content(response):
#     """Sample pytest test function with the pytest fixture as an argument."""
#     # from bs4 import BeautifulSoup
#     # assert 'GitHub' in BeautifulSoup(response.content).title.string


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'simplemdx.cli.main' in result.output
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output
