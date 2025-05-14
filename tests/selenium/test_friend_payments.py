from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import time
import uuid
import random
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:5000"


def get_driver(position_index):
    """Launch headed Chrome, size 900×600, and position side-by-side."""
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
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Create an Account')]")
    )).click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.NAME, "confirm").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
    WebDriverWait(driver, 10).until(
        EC.url_contains("/login")
    )


def login(driver, email, password):
    driver.get(f"{BASE_URL}/")
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Login to Account')]")
    )).click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
    WebDriverWait(driver, 10).until(
        lambda d: any(p in d.current_url for p in ["/dashboard", "/profile", "/transactionForm"])
    )


def set_currency_and_budget(driver, currency):
    """On profile, select currency and set a random budget."""
    driver.get(f"{BASE_URL}/profile")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "currency-select"))
    )
    Select(driver.find_element(By.ID, "currency-select")).select_by_value(currency)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "budget-input"))
    )
    amount = random.randint(2000, 12000)
    budget_el = driver.find_element(By.ID, "budget-input")
    budget_el.clear()
    budget_el.send_keys(str(amount))
    driver.find_element(By.ID, "save-settings").click()
    WebDriverWait(driver, 10).until(
        EC.text_to_be_present_in_element((By.ID, "current-budget"), str(amount))
    )
    time.sleep(1)


def view_dashboard(driver):
    driver.get(f"{BASE_URL}/dashboard")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "summary-cards"))
    )
    time.sleep(1)


def add_friend(driver, friend_username):
    driver.get(f"{BASE_URL}/friends")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "user-search"))
    )
    search = driver.find_element(By.ID, "user-search")
    search.clear()
    search.send_keys(friend_username)
    WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, f"//ul[@id='search-results']/li[contains(., '{friend_username}')]/button"))
    )
    btn = driver.find_element(By.XPATH, f"//ul[@id='search-results']/li[contains(., '{friend_username}')]/button")
    btn.click()
    time.sleep(0.5)


def create_transaction(driver):
    """Random transaction with realistic date via JS picker."""
    driver.get(f"{BASE_URL}/transactionForm")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "type"))
    )
    txn_type = random.choice(["Expense", "Income"] if random.random() < 0.7 else ["Transfer"])
    Select(driver.find_element(By.NAME, "type")).select_by_visible_text(txn_type)
    WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.ID, "category-container" if txn_type != "Transfer" else "transfer-direction-container"))
    )
    if txn_type in ("Expense", "Income"):
        categories = ["Food", "Groceries", "Travel", "Shopping", "Health"] if txn_type == "Expense" else ["Salary", "Savings", "Refund"]
        category = random.choice(categories)
        Select(driver.find_element(By.NAME, "category")).select_by_visible_text(category)
    else:
        directions = ["Incoming (into this account)", "Outgoing (from this account)"]
        category = random.choice(directions)
        Select(driver.find_element(By.NAME, "transfer_direction")).select_by_visible_text(category)
    rand_date = (datetime.today() - timedelta(days=random.randint(0, 90))).strftime("%Y-%m-%d")
    date_el = driver.find_element(By.ID, "date")
    driver.execute_script("arguments[0].value = arguments[1];", date_el, rand_date)
    amount = round(random.uniform(10, 500), 2)
    desc = f"{txn_type} - {category} ${amount}"
    driver.find_element(By.NAME, "amount").clear()
    driver.find_element(By.NAME, "amount").send_keys(str(amount))
    driver.find_element(By.NAME, "description").send_keys(desc)
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Recorded')]"))
    )
    time.sleep(0.5)


def split_bill(driver, friend_usernames):
    driver.get(f"{BASE_URL}/splitBill")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="checkbox"][data-id]'))
    )
    boxes = driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"][data-id]')
    for cb in boxes[:2]:
        driver.execute_script("arguments[0].scrollIntoView(true);", cb)
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable(cb))
        cb.click()
        time.sleep(0.3)
    for friend in friend_usernames:
        s = driver.find_element(By.ID, "user-search")
        s.clear()
        s.send_keys(friend)
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, f"//ul[@id='search-results']/li[contains(., '{friend}')]/button"))
        )
        driver.find_element(By.XPATH, f"//ul[@id='search-results']/li[contains(., '{friend}')]/button").click()
        time.sleep(0.3)
    driver.find_element(By.ID, "split-btn").click()
    while True:
        try:
            WebDriverWait(driver, 2).until(EC.alert_is_present())
            driver.switch_to.alert.accept()
            time.sleep(0.3)
        except TimeoutException:
            break


def view_forecast(driver):
    driver.get(f"{BASE_URL}/forecast")
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "simulateBtn")))
    driver.find_element(By.ID, "simulateBtn").click()
    WebDriverWait(driver, 10).until(lambda d: 'chart' in d.page_source.lower())
    time.sleep(1)


def main():
    # Pick consistent currency for all users
    currency = random.choice(["AUD", "USD", "EUR"] )
    drivers = []
    creds = []
    # Register, login, set budget/currency, view dashboard
    for i in range(3):
        d = get_driver(i)
        u, e, p = random_creds()
        register(d, u, e, p)
        login(d, e, p)
        set_currency_and_budget(d, currency)
        view_dashboard(d)
        drivers.append(d)
        creds.append(u)
    # Mutual friendships
    for idx, d in enumerate(drivers):
        others = [c for c in creds if c != creds[idx]]
        for friend in others:
            add_friend(d, friend)
    # Multiple transactions per user
    for d in drivers:
        for _ in range(random.randint(11, 20)):
            create_transaction(d)
    # Split bills
    for idx, d in enumerate(drivers):
        others = [c for c in creds if c != creds[idx]]
        split_bill(d, others)
    # Forecast & dashboard
    for d in drivers:
        view_forecast(d)
        view_dashboard(d)
    input("Flows done - press Enter to close...")
    for d in drivers:
        d.quit()

if __name__ == "__main__":
    main()