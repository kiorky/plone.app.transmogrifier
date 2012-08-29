# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

from Products.CMFCore.utils import getToolByName
from plone.app.transmogrifier.testing import PAT_INTEGRATION_TESTING

import unittest2 as unittest

class TestObjSync(unittest.TestCase):
    layer = PAT_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

    def test_objsync(self):
        self.assertEquals(1,1)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromName(
            __name__))
    return suite


# vim:set et sts=4 ts=4 tw=80:
