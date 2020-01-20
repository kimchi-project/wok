import pytest

from pages.login import KimchiLoginPage
from utils import getBrowser

@pytest.fixture
def browser():
    browser = getBrowser()
    yield browser
    browser.quit()

def test_login(browser):
    assert KimchiLoginPage(browser).login(), "Cannot login to Kimchi"
