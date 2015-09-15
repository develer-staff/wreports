""" wreports/__init__.py """
# -*- coding: utf-8 -*


from . import test_wreports


def suite():
    import unittest
    suite = unittest.TestSuite()
    suite.addTests(test_wreports.suite())

    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())