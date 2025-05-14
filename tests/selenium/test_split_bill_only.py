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
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Create an Account')]") )
    )
    driver.find_element(By.XPATH, "//button[contains(., 'Create an Account')]").click()
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
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Login to Account')]") )
    )
    driver.find_element(By.XPATH, "//button[contains(., 'Login to Account')]").click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
    WebDriverWait(driver, 10).until(
        lambda d: any(x in d.current_url for x in ("/dashboard", "/profile", "/transactionForm"))
    )

def set_budget(driver):
    """Navigate to profile and set a random monthly budget between 2000 and 12000."""
    driver.get(f"{BASE_URL}/profile")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "budget-input"))
    )
    amount = random.randint(2000, 12000)
    budget_input = driver.find_element(By.ID, "budget-input")
    budget_input.clear()
    budget_input.send_keys(str(amount))
    driver.find_element(By.ID, "save-settings").click()
    # wait for displayed budget update
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
    WebDriverWait(driver, 5).until(
        lambda d: "Friend ✓" in btn.text
    )

def create_transaction(driver):
    driver.get(f"{BASE_URL}/transactionForm")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "type"))
    )
    txn_type = random.choice(["expense", "income", "transfer"])
    Select(driver.find_element(By.NAME, "type")).select_by_value(txn_type)
    if txn_type in ("expense", "income"):
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, "category-container"))
        )
        labels = (["Food", "Groceries", "Travel", "Shopping", "Health"]
                  if txn_type == "expense"
                  else ["Salary", "Savings", "Refund"])
        label = random.choice(labels)
        Select(driver.find_element(By.NAME, "category")).select_by_visible_text(label)
    else:
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, "transfer-direction-container"))
        )
        direction = random.choice(["Incoming (into this account)", "Outgoing (from this account)"])
        Select(driver.find_element(By.NAME, "transfer_direction")).select_by_visible_text(direction)
    amount = round(random.uniform(5, 200), 2)
    desc = f"{txn_type.title()} - {(label if txn_type != 'transfer' else direction)} ${amount}"
    driver.find_element(By.NAME, "amount").clear()
    driver.find_element(By.NAME, "amount").send_keys(str(amount))
    driver.find_element(By.NAME, "description").send_keys(desc)
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
    WebDriverWait(driver, 10).until(
        EC.url_contains("/submission")
    )

def split_bill(driver, friend_usernames):
    driver.get(f"{BASE_URL}/splitBill")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="checkbox"][data-id]'))
    )
    checkboxes = driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"][data-id]')
    for cb in checkboxes[:2]:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", cb)
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable(cb))
        cb.click()
    for friend in friend_usernames:
        search = driver.find_element(By.ID, "user-search")
        search.clear()
        search.send_keys(friend)
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, f"//ul[@id='search-results']/li[contains(., '{friend}')]/button"))
        )
        driver.find_element(By.XPATH, f"//ul[@id='search-results']/li[contains(., '{friend}')]/button").click()
    driver.find_element(By.ID, "split-btn").click()
    while True:
        try:
            WebDriverWait(driver, 2).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.accept()
            time.sleep(0.5)
        except TimeoutException:
            break

def view_forecast(driver):
    driver.get(f"{BASE_URL}/forecast")
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "simulateBtn")))
    driver.find_element(By.ID, "simulateBtn").click()
    WebDriverWait(driver, 10).until(lambda d: 'chart' in d.page_source.lower())
    time.sleep(1)

def main():
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
    for driver in drivers:
        view_forecast(driver)
        view_dashboard(driver)
    input("Flows complete: press Enter to close browsers…")
    for d in drivers:
        d.quit()

if __name__ == "__main__":
    main()

