import pytest

from pages.login import WokLoginPage
from utils import getBrowser

@pytest.fixture
def browser():
    browser = getBrowser()
    yield browser
    browser.quit()

def test_login(browser):
    assert WokLoginPage(browser).login(), "Cannot login to Wok"
