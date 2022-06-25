# -*- coding: utf-8 -*-
import os

import lcovparser


def test_parser():
    filename = os.path.join(os.path.dirname(__file__), "lcov.report")
    report = lcovparser.parse_file(filename)
    assert True
