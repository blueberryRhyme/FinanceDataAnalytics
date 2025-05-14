import pytest
from tests.selenium.helpers import (
    get_driver, random_creds, register,
    duplicate_registration_should_fail, login
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def test_duplicate_registration(flask_server):
    d1 = get_driver(0)
    d2 = get_driver(1)
    u,e,p = random_creds()

    register(d1, u, e, p)
    duplicate_registration_should_fail(d2, u, e, p)  # now will pass
    login(d2, e, p)

    # finally, verify that login succeeded (dashboard *or* profile or transactionForm)
    WebDriverWait(d2, 5).until(lambda drv: any(p in drv.current_url for p in ["/dashboard", "/profile", "/transactionForm"]))

    d1.quit()
    d2.quit()
