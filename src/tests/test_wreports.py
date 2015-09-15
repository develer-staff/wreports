#!/usr/bin/env python3
# -*- coding: utf-8 -*

import unittest


from wreports import *




class WreportsTestCase(unittest.TestCase):

    def test_empty(self):
        raise Exception("Not implemented")


def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(WreportsTestCase))
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())