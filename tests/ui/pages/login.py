import logging as log
import os
import utils
import pytest
from selenium.common.exceptions import TimeoutException

logging = log.getLogger(__name__)

# locators by ID
USERNAME = "username"
PASSWORD = "password"
LOGIN_BUTTON = "btn-login"
LOGIN_BAR = "user-login"

# environment variables
ENV_USER = "USERNAME"
ENV_PASS = "PASSWORD"
ENV_PORT = "PORT"
ENV_HOST = "HOST"


class KimchiLoginPage():
    """
    Page object to Login

    Expect environment variables:
    KIMCHI_USERNAME: username for the host
    KIMCHI_PASSWORD: password for the host
    KIMCHI_HOST: host for kimchi
    KIMCHI_PORT: port for kimchi
    """

    def __init__(self, browser):
        self.browser = browser

        # assert envs
        for var in [ENV_USER, ENV_PASS, ENV_PORT, ENV_HOST]:
            assert var in os.environ, f"{var} is a required environment var"

        # get values
        self.host = os.environ.get(ENV_HOST)
        self.port = os.environ.get(ENV_PORT)
        self.user = os.environ.get(ENV_USER)
        self.password = os.environ.get(ENV_PASS)

    def login(self):
        try:
            url = f"https://{self.host}:{self.port}/login.html"
            self.browser.get(url)
        except TimeoutException as e:
            logging.error(f"Cannot reach kimchi at {url}")
            return False

        # fill user and password
        logging.info(f"Loging in {url}")
        utils.fillTextIfElementIsVisibleById(self.browser,
                                             USERNAME,
                                             self.user)
        utils.fillTextIfElementIsVisibleById(self.browser,
                                             PASSWORD,
                                             self.password)

        # press login
        utils.clickIfElementIsVisibleById(self.browser, LOGIN_BUTTON)

        # login bar not found: return error
        if utils.waitElementIsVisibleById(self.browser, LOGIN_BAR) == False:
            logging.error(f"Invalid credentials")
            return False

        logging.info(f"Logged in {url}")
        return True
