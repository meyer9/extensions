# -*- coding: utf-8 -*-
"""
Created on Sun May 19 07:58:10 2013

@author: matt
"""

import array
import logging
import unittest
import StringIO

import numpy

import parse_dm3
import dm3_image_utils

from nion.swift.model import Calibration


class TestDM3ImportExportClass(unittest.TestCase):

    def check_write_then_read_matches(self, data, func, _assert=True):
        # we confirm that reading a written element returns the same value
        s = StringIO.StringIO()
        header = func(s, outdata=data)
        s.seek(0)
        if header is not None:
            r, hy = func(s)
        else:
            r = func(s)
        if _assert:
            self.assertEqual(r, data)
        return r

    def test_dm_read_struct_types(self):
        s = StringIO.StringIO()
        types = [2, 2, 2]
        parse_dm3.dm_read_struct_types(s, outtypes=types)
        s.seek(0)
        in_types, headerlen = parse_dm3.dm_read_struct_types(s)
        self.assertEqual(in_types, types)

    def test_simpledata(self):
        self.check_write_then_read_matches(45, parse_dm3.dm_types[parse_dm3.get_dmtype_for_name('long')])
        self.check_write_then_read_matches(2**30, parse_dm3.dm_types[parse_dm3.get_dmtype_for_name('uint')])
        self.check_write_then_read_matches(34.56, parse_dm3.dm_types[parse_dm3.get_dmtype_for_name('double')])

    def test_read_string(self):
        data = "MyString"
        ret = self.check_write_then_read_matches(data, parse_dm3.dm_types[parse_dm3.get_dmtype_for_name('array')], False)
        self.assertEqual(data, ret)

    def test_array_simple(self):
        dat = array.array('b', [0]*256)
        self.check_write_then_read_matches(dat, parse_dm3.dm_types[parse_dm3.get_dmtype_for_name('array')])

    def test_array_struct(self):
        dat = parse_dm3.structarray(['h', 'h', 'h'])
        dat.raw_data = '0x00'*(3*20)
        self.check_write_then_read_matches(dat, parse_dm3.dm_types[parse_dm3.get_dmtype_for_name('array')])

    def test_tagdata(self):
        for d in [45, 2**30, 34.56, array.array('b', [0]*256)]:
            self.check_write_then_read_matches(d, parse_dm3.parse_dm_tag_data)

    def test_tagroot_dict(self):
        mydata = {}
        self.check_write_then_read_matches(mydata, parse_dm3.parse_dm_tag_root)
        mydata = {"Bob": 45, "Henry": 67, "Joe": 56}
        self.check_write_then_read_matches(mydata, parse_dm3.parse_dm_tag_root)

    def test_tagroot_dict_complex(self):
        mydata = {"Bob": 45, "Henry": 67, "Joe": {
                  "hi": [34, 56, 78, 23], "Nope": 56.7, "d": array.array('I', [0] * 32)}}
        self.check_write_then_read_matches(mydata, parse_dm3.parse_dm_tag_root)

    def test_tagroot_list(self):
        # note any strings here get converted to 'H' arrays!
        mydata = []
        self.check_write_then_read_matches(mydata, parse_dm3.parse_dm_tag_root)
        mydata = [45,  67,  56]
        self.check_write_then_read_matches(mydata, parse_dm3.parse_dm_tag_root)

    def test_struct(self):
        # note any strings here get converted to 'H' arrays!
        mydata = tuple()
        f = parse_dm3.dm_types[parse_dm3.get_dmtype_for_name('struct')]
        self.check_write_then_read_matches(mydata, f)
        mydata = (3, 4, 56.7)
        self.check_write_then_read_matches(mydata, f)

    def test_image(self):
        im = array.array('h')
        im.fromstring(numpy.random.random(16))
        im_tag = {"Data": im,
                  "Dimensions": [23, 45]}
        s = StringIO.StringIO()
        parse_dm3.parse_dm_tag_root(s, outdata=im_tag)
        s.seek(0)
        ret = parse_dm3.parse_dm_tag_root(s)
        self.assertEqual(im_tag["Data"], ret["Data"])
        self.assertEqual(im_tag["Dimensions"], ret["Dimensions"])
        self.assert_((im_tag["Data"] == ret["Data"]))

    def test_data_write_read_round_trip(self):
        dtypes = (numpy.float32, numpy.float64, numpy.complex64, numpy.complex128, numpy.int16, numpy.uint16, numpy.int32, numpy.uint32)
        for dtype in dtypes:
            s = StringIO.StringIO()
            data_in = numpy.ones((6, 4), dtype)
            dimensional_calibrations_in = [Calibration.Calibration(1, 2, "nm"), Calibration.Calibration(2, 3, u"µm")]
            intensity_calibration_in = Calibration.Calibration(4, 5, "six")
            metadata_in = dict()
            dm3_image_utils.save_image(data_in, dimensional_calibrations_in, intensity_calibration_in, metadata_in, s)
            s.seek(0)
            data_out, _, _, _, _ = dm3_image_utils.load_image(s)
            self.assertTrue(numpy.array_equal(data_in, data_out))

    def test_calibrations_write_read_round_trip(self):
        s = StringIO.StringIO()
        data_in = numpy.ones((6, 4), numpy.float32)
        dimensional_calibrations_in = [Calibration.Calibration(1, 2, "nm"), Calibration.Calibration(2, 3, u"µm")]
        intensity_calibration_in = Calibration.Calibration(4, 5, "six")
        metadata_in = dict()
        dm3_image_utils.save_image(data_in, dimensional_calibrations_in, intensity_calibration_in, metadata_in, s)
        s.seek(0)
        data_out, dimensional_calibrations_out, intensity_calibration_out, title_out, metadata_out = dm3_image_utils.load_image(s)
        dimensional_calibrations_out = [Calibration.Calibration(*d) for d in dimensional_calibrations_out]
        self.assertTrue(numpy.array_equal(dimensional_calibrations_in, dimensional_calibrations_out))
        intensity_calibration_out = Calibration.Calibration(*intensity_calibration_out)
        self.assertTrue(numpy.array_equal(intensity_calibration_in, intensity_calibration_out))

    def test_metadata_write_read_round_trip(self):
        s = StringIO.StringIO()
        data_in = numpy.ones((6, 4), numpy.float32)
        dimensional_calibrations_in = [Calibration.Calibration(1, 2, "nm"), Calibration.Calibration(2, 3, u"µm")]
        intensity_calibration_in = Calibration.Calibration(4, 5, "six")
        metadata_in = {"abc": 1, "def": "abc", "efg": { "one": 1, "two": "TWO", "three": [3, 4, 5] }}
        dm3_image_utils.save_image(data_in, dimensional_calibrations_in, intensity_calibration_in, metadata_in, s)
        s.seek(0)
        data_out, dimensional_calibrations_out, intensity_calibration_out, title_out, metadata_out = dm3_image_utils.load_image(s)
        imported_metadata = metadata_out.get("imported_properties", dict())
        self.assertTrue(numpy.array_equal(metadata_in, imported_metadata))

# some functions for processing multiple files.
# useful for testing reading and writing a large number of files.
import os


def process_dm3(path, mode):
    opath = path + ".out.dm3"
    data = odata = None
    if mode == 0 or mode == 1:  # just open source
        # path=opath
        with open(path, 'rb') as f:
            data = parse_dm3.parse_dm_header(f)
    if mode == 1:  # open source, write to out
        with open(opath, 'wb') as f:
            parse_dm3.parse_dm_header(f, outdata=data)
    elif mode == 2:  # open both
        with open(path, 'rb') as f:
            data = parse_dm3.parse_dm_header(f)
        with open(opath, 'rb') as f:
            odata = parse_dm3.parse_dm_header(f)
        # this ensures keys in root only are the same
        assert(sorted(odata) == sorted(data))
    return data, odata


def process_all(mode):
    for f in [x for x in os.listdir(".")
              if x.endswith(".dm3")
              if not x.endswith("out.dm3")]:
        print "reading", f, "..."
        data, odata = process_dm3(f, mode)

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()
    # process_all(1)
