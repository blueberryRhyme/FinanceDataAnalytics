import pytest
import random
from tests.selenium.helpers import get_driver, random_creds, register, login, set_currency_and_budget, run_monthly_transactions

def test_monthly_statements_flow(flask_server):
    d = get_driver(0)
    u,e,p=random_creds(); register(d,u,e,p); login(d,e,p)
    set_currency_and_budget(d, random.choice(["AUD","USD","EUR"]))
    run_monthly_transactions(d, months=6)
    BASE_URL = "http://127.0.0.1:5000"
    d.get(f"{BASE_URL}/dashboard")
    d.quit()