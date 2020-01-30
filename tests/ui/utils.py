from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.wait import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from pygeckodriver import geckodriver_path
from chromedriver_binary import chromedriver_filename

import logging as log
import os

logging = log.getLogger(__name__)

WAIT = 10

def getBrowser(headless=True):
    # chrome: set browser class and options
    if os.environ.get("BROWSER").upper() == "CHROME":
        options = ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        browser = webdriver.Chrome
        path = chromedriver_filename

    # firefox: set browser class and options
    elif os.environ.get("BROWSER").upper() == "FIREFOX":
        options = FirefoxOptions()
        browser = webdriver.Firefox
        path = geckodriver_path

    # headless
    if "DEBUG" not in os.environ:
        options.add_argument('--headless')
        #options.headless = True
    else:
        logging.info("Headless mode deactivated")

    # error: browser not found
    try:
        driver = browser(options=options, executable_path=path)
    except Exception as e:
        logging.info(f"Browser or driver not found: {e}")

    driver.set_page_load_timeout(WAIT * 2)
    return driver

def waitElementByCondition(browser, condition, searchMethod, searchString, errorMessage, time=WAIT):
    try:
        element = WebDriverWait(browser, time).until(
            condition((searchMethod, searchString))
        )
    except TimeoutException as e:
        logging.error(f"Element {searchString} {errorMessage}")
        return False
    return True


def waitElementIsVisibleById(browser, elementId, time=WAIT):
    return waitElementByCondition(browser,
                                  EC.visibility_of_element_located,
                                  By.ID,
                                  elementId,
                                  "is not visibile",
                                  time)

def waitElementIsVisibleByXpath(browser, xpath):
    return waitElementByCondition(browser,
                                  EC.visibility_of_element_located,
                                  By.XPATH,
                                  xpath,
                                  "is not visibile")

def waitElementIsClickableById(browser, elementId):
    return waitElementByCondition(browser,
                                  EC.element_to_be_clickable,
                                  By.ID,
                                  elementId,
                                  "is not clickable")

def waitElementIsClickableByXpath(browser, xpath):
    return waitElementByCondition(browser,
                                  EC.element_to_be_clickable,
                                  By.XPATH,
                                  xpath,
                                  "is not clickable")

def clickIfElementIsVisibleByXpath(browser, xpath):
    try:
        assert(waitElementIsVisibleByXpath(browser, xpath))
        assert(waitElementIsClickableByXpath(browser, xpath))
        browser.find_element_by_xpath(xpath).click()

    except Exception as e:
        logging.error(f"Cannot click on element {xpath}: {e}")
        return False

    return True

def clickIfElementIsVisibleById(browser, elementId):
    try:
        assert(waitElementIsVisibleById(browser, elementId))
        assert(waitElementIsClickableById(browser, elementId))
        browser.find_element_by_id(elementId).click()

    except Exception as e:
        logging.error(f"Cannot click on element {elementId}: {e}")
        return False

    return True

def fillTextIfElementIsVisibleById(browser, elementId, text):
    try:
        assert(waitElementIsVisibleById(browser, elementId))
        browser.find_element_by_id(elementId).send_keys(text)

    except Exception as e:
        logging.error(f"Cannot type {text} on element {elementId}: {e}")
        return False

    return True

