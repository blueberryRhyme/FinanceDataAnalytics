import pytest
import random
from tests.selenium.helpers import get_driver, random_creds, register, login, set_currency_and_budget, view_dashboard, add_friend, create_transaction, split_bill, view_forecast


def test_full_friend_payments_flow(flask_server):
    currency = random.choice(["AUD", "USD", "EUR"])
    drivers = []
    creds = []

    for i in range(3):
        d = get_driver(i)
        u, e, p = random_creds()
        register(d, u, e, p)
        login(d, e, p)
        set_currency_and_budget(d, currency)
        view_dashboard(d)
        drivers.append(d)
        creds.append(u)

    for idx, d in enumerate(drivers):
        others = [c for c in creds if c != creds[idx]]
        for friend in others:
            add_friend(d, friend)

    for d in drivers:
        for _ in range(random.randint(11, 20)):
            create_transaction(d)

    for idx, d in enumerate(drivers):
        others = [c for c in creds if c != creds[idx]]
        split_bill(d, others)

    for d in drivers:
        view_forecast(d)
        view_dashboard(d)
        d.quit()
