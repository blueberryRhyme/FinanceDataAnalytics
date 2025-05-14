import pytest
import random
from tests.selenium.helpers import get_driver, random_creds, register, login, view_dashboard, set_budget, add_friend, create_transaction, split_bill
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_split_bill_only_flow(flask_server):
    drivers = []
    creds = []
    for i in range(3):
        d = get_driver(i)
        u, e, p = random_creds()
        register(d, u, e, p)
        login(d, e, p)
        set_budget(d)
        view_dashboard(d)
        drivers.append(d)
        creds.append((u, e, p))
    for idx, driver in enumerate(drivers):
        others = [c[0] for j, c in enumerate(creds) if j != idx]
        for friend in others:
            add_friend(driver, friend)
    for driver in drivers:
        create_transaction(driver)
    for idx, driver in enumerate(drivers):
        others = [c[0] for j, c in enumerate(creds) if j != idx]
        split_bill(driver, others)
    for d in drivers:
        d.quit()
    return
