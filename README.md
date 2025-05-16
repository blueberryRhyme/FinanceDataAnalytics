# 💸 Finance Data Analytics Platform

This web-based financial dashboard provides users with the ability to register, log in, track transactions, analyze financial data, and generate monthly statements. The platform is built using Flask and integrates unit tests and Selenium end-to-end tests to ensure robust functionality.

---

## 📦 Features

- **Secure user authentication**  
  User registration, login, and session management with encrypted passwords.  

- **Flexible transaction management**  
  Add, edit, or delete transactions manually _or_ upload a CSV of your transaction history.  

- **Powerful analytics & visualizations**  
  View your transaction history on interactive graphs, enjoy automatic categorization, and get simple forecasts of future spending trends.  

- **Easy bill splitting**  
  Split bills with friends, track who owes what, and apply payments with just a few clicks — no more awkward reminders.

---


## 🖥️ Local Development Setup

### ✅ Requirements

Ensure the following are installed:
- Python 3.10 or higher
- pip

### 📥 Installation

**Clone the repository and navigate into the project folder:**

```
git clone https://github.com/blueberryRhyme/FinanceDataAnalytics.git
cd FinanceDataAnalytics
```

**Install all required libraries:**

```
pip install -r requirements.txt
```

**Create a .env file in your project root:**

Create a file named `.env` in your project root with the following contents:

```
FLASK_APP=run.py
SECRET_KEY=3403-secret-key
TEST_SECRET_KEY=test-secret-key
SQLALCHEMY_DATABASE_URI=sqlite:///database.db
```

Alternatively, set variables in your shell.

**Windows (PowerShell):**
```
$env:FLASK_APP = "run.py"
$env:SECRET_KEY = "3403-secret-key"
$env:TEST_SECRET_KEY = "test-secret-key"
$env:SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"
```

**Linux/macOS (bash):**

```
export FLASK_APP="run.py"
export SECRET_KEY="3403-secret-key"
export TEST_SECRET_KEY="test-secret-key"
export SQLALCHEMY_DATABASE_URI="sqlite:///database.db"

```

**Initalize the database**

```
flask db upgrade
```

**🚀 Running the Application**

**You can launch the app in one of two ways:**


### Option 1: Python Script

```
python run.py
```

### Option 2: Running Flask with Flask CLI

```
flask run (Make sure your environment is configured (either via your .env file or by exporting vars)
```

**Once the server is running, navigate to:**

```
http://127.0.0.1:5000
```

---

### ✅ Running Tests

The platform includes 27 unit tests and 5 Selenium tests to ensure correctness and prevent regressions.

**Run all tests using:**

```
pytest
```

**Run unit tests only using:**

```
pytest tests/unit
```

**Run selenium tests only using:**

```
pytest tests/selenium
```


**🧪 Example Selenium Use**

Example test case: test_duplicate_accounts.py verifies that duplicate user registration is blocked and handled gracefully.

```
# Inside tests/selenium/test_duplicate_accounts.py
def test_duplicate_registration():
    # Attempts to register the same user twice and checks for error message
```

---

**👨‍💻 Authors**

```
Developed by blueberryRhyme Jia Qi Lam (23751337), gilbertting03 Gilbert Xiang Yi Ting (23957541), armaanjosann Armaan Josan (24001588), fishymate Mark Tanel (23660033)

CITS3403 — The University of Western Australia

Semester 1, 2025
```
