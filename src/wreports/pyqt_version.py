#!/usr/bin/env python2
# encoding: utf-8

PYQt4, PYQt5 = range(2)
PYQT_VERSION = PYQt4

try:
    import PyQt5
    PYQT_VERSION = PYQt5
except ImportError:
    PYQT_VERSION = PYQt4

__all__ = ["PYQt4", "PYQt5", "PYQT_VERSION"]
