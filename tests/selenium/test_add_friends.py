from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import uuid

BASE_URL = "http://127.0.0.1:5000"


def get_driver(position_index):
    """Launch headed Chrome, size 900×600, and position side‑by‑side."""
    opts = Options()
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.set_window_size(900, 600)
    driver.set_window_position(900 * position_index, 0)
    return driver


def random_creds():
    suffix = uuid.uuid4().hex[:6]
    username = f"user_{suffix}"
    email = f"{username}@example.com"
    password = f"P@ss{suffix}"
    return username, email, password


def register(driver, username, email, password):
    driver.get(f"{BASE_URL}/")
    time.sleep(1)
    driver.find_element(By.XPATH, "//button[contains(., 'Create an Account')]").click()
    time.sleep(1)
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.NAME, "confirm").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
    time.sleep(1)


def login(driver, email, password):
    driver.get(f"{BASE_URL}/")
    time.sleep(1)
    driver.find_element(By.XPATH, "//button[contains(., 'Login to Account')]").click()
    time.sleep(1)
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
    time.sleep(1)


def add_friend(driver, friend_username):
    driver.get(f"{BASE_URL}/friends")
    time.sleep(1)
    search = driver.find_element(By.ID, "user-search")
    search.clear()
    search.send_keys(friend_username)
    time.sleep(1)
    btn = driver.find_element(
        By.XPATH,
        f"//ul[@id='search-results']/li[contains(., '{friend_username}')]/button"
    )
    btn.click()
    time.sleep(0.5)
    assert "Friend ✓" in btn.text


def main():
    drivers = []
    creds = []

    # 1) Spin up 3 browsers, register & log in each
    for idx in range(3):
        d = get_driver(idx)
        u, e, p = random_creds()
        register(d, u, e, p)
        login(d, e, p)
        drivers.append(d)
        creds.append((u, e, p))

    # 2) For each user, add the other two as friends
    for idx, driver in enumerate(drivers):
        my_username = creds[idx][0]
        others = [creds[i][0] for i in range(3) if i != idx]
        for friend_username in others:
            add_friend(driver, friend_username)
        print(f"{my_username} is now friends with {others}")

    print("✅ Three‑way friendship setup complete. Press Enter to close all browsers.")
    input()

    for d in drivers:
        d.quit()


if __name__ == "__main__":
    main()
