from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import time
import uuid
import random
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:5000"

def get_driver_fullscreen():
    """Launch headed Chrome in fullscreen."""
    opts = Options()
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.maximize_window()
    return driver

def random_creds():
    suffix = uuid.uuid4().hex[:6]
    username = f"user_{suffix}"
    email = f"{username}@example.com"
    password = f"P@ss{suffix}"
    return username, email, password

def register_and_login(driver, username, email, password):
    # Register
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
    # Wait for login page
    WebDriverWait(driver, 10).until(lambda d: "/login" in d.current_url)

    # Login
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
    # Wait for profile page
    WebDriverWait(driver, 10).until(lambda d: "/profile" in d.current_url)

def set_random_budget_and_currency(driver):
    """On profile page, choose random currency and set random monthly budget."""
    driver.get(f"{BASE_URL}/profile")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "currency-select"))
    )
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "budget-input"))
    )
    currency = random.choice(["AUD", "USD", "EUR"])
    Select(driver.find_element(By.ID, "currency-select")).select_by_value(currency)
    budget_amt = random.randint(2000, 12000)
    budget_input = driver.find_element(By.ID, "budget-input")
    budget_input.clear()
    budget_input.send_keys(str(budget_amt))
    driver.find_element(By.ID, "save-settings").click()
    WebDriverWait(driver, 10).until(
        EC.text_to_be_present_in_element((By.ID, "current-budget"), str(budget_amt))
    )
    time.sleep(1)
    return currency, budget_amt

def create_dated_transaction(driver, date_str, txn_type, category, amount, description):
    """Create a transaction at a specific date via the date picker."""
    driver.get(f"{BASE_URL}/transactionForm")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "type"))
    )
    # Select transaction type
    Select(driver.find_element(By.NAME, "type")).select_by_visible_text(txn_type)
    WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.ID, "category-container"))
    )
    # Select category
    Select(driver.find_element(By.NAME, "category")).select_by_visible_text(category)
    # Set date via JS to avoid formatting issues
    date_el = driver.find_element(By.ID, "date")
    driver.execute_script("arguments[0].scrollIntoView(true);", date_el)
    driver.execute_script("arguments[0].value = arguments[1];", date_el, date_str)
    # Fill amount & description
    amt_el = driver.find_element(By.NAME, "amount")
    amt_el.clear()
    amt_el.send_keys(str(amount))
    driver.find_element(By.NAME, "description").send_keys(description)
    # Submit
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
    # Confirm via submission header text
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Recorded')]")
    ))
    time.sleep(0.5)

def run_monthly_transactions(driver, months=6):
    """Generate transactions over past months."""
    today = datetime.today()
    for m in range(months, 0, -1):
        first_of_month = (today.replace(day=1) - timedelta(days=(m-1)*30)).replace(day=1)
        for _ in range(random.randint(2, 5)):
            rand_day = first_of_month + timedelta(days=random.randint(0, 27))
            date_str = rand_day.strftime("%Y-%m-%d")
            txn_type = random.choice(["Expense", "Income"])
            if txn_type == "Expense":
                cat = random.choice(["Food", "Groceries", "Travel", "Shopping", "Health"])
            else:
                cat = random.choice(["Salary", "Savings", "Refund"])
            amt = round(random.uniform(50, 500), 2)
            desc = f"{txn_type} on {date_str}"
            create_dated_transaction(driver, date_str, txn_type, cat, amt, desc)

def main():
    driver = get_driver_fullscreen()
    try:
        u, e, p = random_creds()
        register_and_login(driver, u, e, p)
        currency, budget_amt = set_random_budget_and_currency(driver)
        print(f"Settings: currency={currency}, budget={budget_amt}")
        run_monthly_transactions(driver, months=6)
        driver.get(f"{BASE_URL}/dashboard")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "summary-cards"))
        )
        time.sleep(2)
        print("Monthly statements test complete.")
        input("Press Enter to close browser…")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
