import utils
from pages.login import KimchiLoginPage

import logging as log

class TestWokLogin():

    def setup(self):
        self.browser = utils.getBrowser()

    def test_login(self):
        assert KimchiLoginPage(self.browser).login(), "Cannot login to Kimchi"

    def tearDown(self):
        self.browser.close()
