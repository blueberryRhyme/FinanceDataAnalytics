import pytest
from tests.selenium.helpers import get_driver, random_creds, register, login, add_friend


def test_add_friends_flow(flask_server):
    drivers, creds = [], []
    for i in range(3):
        d = get_driver(i)
        u, e, p = random_creds()
        register(d, u, e, p)
        login(d, e, p)
        drivers.append(d)
        creds.append(u)
    for idx, d in enumerate(drivers):
        others = [c for j, c in enumerate(creds) if j != idx]
        for friend in others:
            add_friend(d, friend)
    for d in drivers:
        d.quit()
