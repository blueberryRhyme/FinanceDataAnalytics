from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import uuid

BASE_URL = "http://127.0.0.1:5000"


def get_driver(position_index):
    """Launch headed Chrome, size 900×600, and position side‑by‑side."""
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


def duplicate_registration_should_fail(driver, username, email, password):
    driver.get(f"{BASE_URL}/")
    time.sleep(1)
    driver.find_element(By.XPATH, "//button[contains(., 'Create an Account')]").click()
    time.sleep(1)
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.NAME, "confirm").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

    # Wait until the duplicate‑user error flash appears
    wait = WebDriverWait(driver, 5)
    error = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH,
             "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
             "'abcdefghijklmnopqrstuvwxyz'), 'already')]")
        )
    )
    assert error is not None, "Expected duplicate‑user error message but none appeared"

    # Keep the window idle for 5 seconds so you can read the error
    time.sleep(5)


def main():
    # Launch two browser windows
    driver1 = get_driver(0)
    driver2 = get_driver(1)

    # Generate a single set of credentials
    username, email, password = random_creds()

    # Window 1: successful registration
    register(driver1, username, email, password)
    print(f"✅ User '{username}' registered in window 1")

    # Window 2: attempt duplicate registration (should fail and pause 5 s)
    duplicate_registration_should_fail(driver2, username, email, password)
    print("✅ Duplicate registration error displayed for 5 seconds in window 2")

    # Window 2: now log in with the same credentials
    login(driver2, email, password)
    print(f"✅ User '{username}' successfully logged in via window 2")

    print("Press Enter to close both browsers.")
    input()

    driver1.quit()
    driver2.quit()


if __name__ == "__main__":
    main()
