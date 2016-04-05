#!/usr/bin/env python2
# encoding: utf-8
from __future__ import print_function, absolute_import, division

class WreportsException(Exception):
    '''root for Wreports Exceptions, only used to except any Wreports error, never raised'''
    pass


class TagError(WreportsException):
    pass


class NoEnvError(WreportsException):
    pass


class RenderError(WreportsException):
    pass


class ParseError(WreportsException):
    pass
