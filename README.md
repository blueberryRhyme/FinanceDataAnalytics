# 💸 Finance Data Analytics Platform

This web-based financial dashboard provides users with the ability to register, log in, track transactions, analyze financial data, and generate monthly statements. The platform is built using Flask and integrates unit tests and Selenium end-to-end tests to ensure robust functionality.

---

## 📦 Features

- Secure user registration and login
- Add, edit, and delete financial transactions
- Real-time transaction history and analytics
- Monthly statement generation
- Responsive UI and mobile compatibility
- Persistent user data using SQLite
- Unit and Selenium tests for reliability

---

## 🧠 Application Design & Architecture

The application follows a **Model-View-Controller (MVC)** architecture:

- **Models (`models.py`)**: Handle data representation (e.g., `User`, `Transaction`)
- **Views (`templates/`)**: HTML templates rendered via Jinja2
- **Controllers (`routes.py`)**: Define business logic and route handling
- **Helpers**: Encapsulated utility functions to simplify route logic and data formatting
- **Selenium Scripts (`tests/selenium/`)**: Automate browser interactions for end-to-end tests
- **Unit tests (`tests/unit/`)**: Unit tests to ensure key functions of website operate correctly

The app is modular, enabling scalability and straightforward maintenance.

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

**🚀 Running the Application**
**You can launch the app in one of two ways:**


### Option 1: Python Script

```
python run.py
```

### Option 2: Running Flask with Flask CLI

**Windows (PowerShell):**

```
$env:FLASK_APP = "run.py"
$env:SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"
flask run
```

**Linux/macOS (bash):**

```
export FLASK_APP=run.py
export SQLALCHEMY_DATABASE_URI="sqlite:///app.db"
flask run
```

**Once the server is running, navigate to:**

```
http://127.0.0.1:5000
```

### ✅ Running Tests

The platform includes 12 unit tests and 5 Selenium tests to ensure correctness and prevent regressions.

**Run all tests using:**

```
pytest
```

**📁 Test Structure**

```
tests/
├── unit/
│   └── test_models.py
│   └── test_auth.py
│   └── test_routes.py
├── selenium/
│   └── helpers.py
│   └── test_registration.py
│   └── test_login_flow.py
│   └── test_monthly_statements.py
│   └── test_duplicate_accounts.py
│   └── test_split_bill_only.py
```

**🧪 Example Selenium Use**

Example test case: test_duplicate_accounts.py verifies that duplicate user registration is blocked and handled gracefully.

```
# Inside tests/selenium/test_duplicate_accounts.py
def test_duplicate_registration():
    # Attempts to register the same user twice and checks for error message
```

### 📚 Notes for Assessors

This project follows best practices for structure, testing, and modularization.

Git commits are structured by task/module, demonstrating collaborative workflow and Agile practices.

Detailed inline comments and docstrings are provided throughout the codebase.

README includes full setup instructions for replication and assessment.

**👨‍💻 Authors**

```
Developed by blueberryRhyme Jia Qi Lam (23751337), gilbertting03 Gilbert Xiang Yi Ting (23957541), armaanjosann Armaan Josan (24001588), fishymate Mark Tanel (23660033)

CITS3403 — The University of Western Australia

Semester 1, 2025
```
