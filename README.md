# LibraVerse — Virtual Library Management System

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/framework-Flask%203.1+-9B51E0.svg)](https://flask.palletsprojects.com/)
[![Pandas](https://img.shields.io/badge/analytics-Pandas%20%26%20NumPy-22D3EE.svg)](https://pandas.pydata.org/)
[![Database](https://img.shields.io/badge/database-SQLite3%20Persistent-003B57.svg)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/tests-19%20Passing%20(Pytest)-10B981.svg)](https://docs.pytest.org/)

**LibraVerse** is a modern, full-stack Virtual Library Management System crafted with a dark cybernetic aesthetic (deep purple and electric cyan), interactive 3D book physics, floating 3D volumes, mouse parallax, and Python data analytics powered by **Pandas** and **NumPy**.

Designed as a college software engineering project and portfolio showcase, LibraVerse provides a fully working web application with real database persistence, transaction safety, administrative command dashboards, and CSV/Excel exports.

---

## 🌟 Key System Features

### 1. Futuristic 3D Visual Experience
- **Interactive 3D Book Cards**: Tilt realistically according to cursor position with perspective transforms (`rotateX`, `rotateY`, `translateZ`), dynamic glare overlays, and soft directional shadows.
- **Floating 3D Hero Books**: Layered 3D book models featuring front covers, spine depth, page leaf textures, and back covers oscillating on floating keyframe physics.
- **Space Mouse Parallax**: Multi-plane depth simulation that responds smoothly to mouse movement without disrupting clickable controls.
- **Scroll Reveal**: Viewport-triggered animations powered by native `IntersectionObserver`.
- **Accessibility Ready**: Full support for `prefers-reduced-motion` with seamless touch fallbacks on mobile.

### 2. Comprehensive Library Operations
- **Book Catalog & Deep Search**: Case-insensitive multi-field search across titles, authors, ISBNs, and categories. Filter by taxonomy and real-time shelf availability.
- **Administrative Inventory Control**: Complete CRUD capabilities for books with ISBN uniqueness checks, publication year validation, and active loan deletion protection.
- **Member Directory**: Register, edit, and track readers with verified email formats and individual loan history summaries.
- **Circulation Desk (Issue & Return)**:
  - Atomic transactions: Checkouts decrement available stock; returns increment stock.
  - Due date calculation (defaults to +14 days).
  - Automated overdue detection calculating overdue days and late fines ($1.50/day).
  - Protection against duplicate returns and zero-stock checkouts.
- **Historical Ledger**: Full transaction log with multi-column sorting and status filtering (`Issued`, `Returned`, `Overdue`).

### 3. Meaningful Pandas & NumPy Data Engine
- **Pandas**:
  - `DataFrame.groupby('category').agg(...)` for category volume, inventory balance, and circulation rate analytics.
  - Multi-table merges to compute popularity scores and most frequently checked-out titles.
  - One-click UTF-8 CSV exports and multi-sheet formatted Excel workbooks via `openpyxl`.
- **NumPy**:
  - `np.mean()`, `np.std()`, and `np.median()` for monthly checkout distribution.
  - `np.polyfit()` linear regression to calculate month-over-month circulation growth slopes.
  - `np.histogram()` to bin completed loan durations into discrete intervals (0–7 days, 8–14 days, 15–21 days, 22–30 days, 30+ days).

### 4. Security & Architecture
- **Authentication**: Administrator session management with `scrypt` password hashing via Werkzeug.
- **CSRF Protection**: Tokenized verification on all state-changing `POST` requests.
- **Route Authorization**: View decorators redirecting unauthenticated traffic.
- **ACID Transactions**: Relational integrity with SQLite foreign key enforcement (`PRAGMA foreign_keys = ON;`).

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.10+** (Tested and optimized on Python 3.13)
- Windows, macOS, or Linux

### 2. Create and Activate Virtual Environment (Windows)
Open PowerShell in the project directory:

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment on Windows PowerShell
.\venv\Scripts\Activate.ps1

# (Optional: If PowerShell execution policy restricts scripts, run:)
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

*On macOS / Linux:*
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Initialize Database and Seed Sample Data
Initialize the SQLite schema, create the administrator account, and seed over 20 books and realistic borrowing records:

```bash
python seed.py
```

> **Note on Resetting Data:** To reset the database cleanly to default seed state during development, run:
> ```bash
> python seed.py --reset
> ```

### 5. Launch the Web Application
```bash
python app.py
```

The application will start on the local development server:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔑 Administrator Credentials

To access the Command Console and administrative tools:
1. Navigate to [http://127.0.0.1:5000/login](http://127.0.0.1:5000/login) or click **Admin Login** in the top navigation bar.
2. Enter the default administrator credentials:
   - **Username:** `admin` (or `admin@libraverse.io`)
   - **Password:** `Admin@LibraVerse2026`

Once authenticated, you gain access to:
- Overview KPI Dashboard with Chart.js analytics
- Book Inventory Management
- Member Directory
- Circulation Desk (Issue & Return)
- Transaction History
- Deep Analytics Console
- CSV and Excel Master Exports

---

## 🌐 Deployment Guide (GitHub & Render)

LibraVerse is fully pre-configured for production hosting on **Render** backed by **GitHub**.

### Step 1: Push Code to GitHub

Open PowerShell or Terminal in the project root:

```bash
# 1. Initialize git repository (if not already initialized)
git init

# 2. Stage all files (.gitignore automatically excludes virtual environments and temporary files)
git add .

# 3. Commit the changes
git commit -m "Deploy LibraVerse to Render with gunicorn and production config"

# 4. Set the default branch to main
git branch -M main

# 5. Connect to your GitHub repository (replace with your repository URL)
git remote add origin https://github.com/<your-github-username>/libraverse.git

# 6. Push to GitHub
git push -u origin main
```

---

### Step 2: Deploy as a Web Service on Render

1. Log into your account at [dashboard.render.com](https://dashboard.render.com).
2. Click **New +** and select **Web Service**.
3. Choose **Build and deploy from a Git repository** and select your `libraverse` repository.
4. Fill in the following deployment configuration:

| Setting | Value |
| :--- | :--- |
| **Name** | `libraverse` |
| **Region** | Choose your closest region (e.g. Frankfurt, Oregon, Singapore) |
| **Branch** | `main` |
| **Root Directory** | *(Leave blank - root)* |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt && python seed.py` |
| **Start Command** | `gunicorn app:app` |
| **Instance Type** | `Free` (or `Starter` for persistent disk) |

5. Under **Environment Variables**, add the following key-value pairs:

| Key | Recommended Value | Notes |
| :--- | :--- | :--- |
| `PYTHON_VERSION` | `3.11.8` | Ensures consistent Python environment on Render |
| `FLASK_ENV` | `production` | Enables production security and disables debug mode |
| `SECRET_KEY` | *(Generate a 32+ character random string)* | Used for cryptographic session signing and CSRF tokens |
| `ADMIN_PASSWORD` | *(Optional: your custom strong password)* | Sets the default administrator login password on initial seed |

6. Click **Create Web Service**. Render will install all dependencies, seed the initial database, and bind the Gunicorn server to the cloud port.

---

### ⚠️ SQLite Database Persistence on Render Explained

Render instances handle file storage differently depending on your plan:

- **Free Tier (Ephemeral Storage)**:
  - On the Free tier, Render instances have an **ephemeral disk**. 
  - Every time the application is redeployed or restarts after idling, the filesystem is replaced with a fresh build from GitHub.
  - The build command (`python seed.py`) will automatically initialize and seed the catalog with the sample books and members on each deploy.
  - However, **any dynamic additions or checkouts created during runtime will be reset** when the container restarts or redeploys.
  
- **Production Persistence (Render Persistent Disks)**:
  - For continuous data persistence with SQLite across redeploys, attach a **Persistent Disk** (available on paid plans, e.g. Starter at $7/mo + $1/mo for 1GB disk):
    1. In your Render Web Service settings, navigate to the **Disks** tab and click **Add Disk**.
    2. Set **Mount Path** to: `/var/data`
    3. Set **Size** to: `1 GB`
    4. In the **Environment Variables** tab, add:
       - `DATABASE_PATH` = `/var/data/library.db`
       - `EXPORTS_DIR` = `/var/data/exports`
  - With a Persistent Disk attached, the SQLite database resides outside the ephemeral container and will **never** be erased during code updates, restarts, or redeployments.

---

## 🧪 Running Automated Tests

A comprehensive suite of 19 automated tests is included using `pytest`, testing all services, validation constraints, authentication, transactions, and analytics on a dedicated isolated test database:

```bash
python -m pytest -v
```

### Test Coverage Highlights:
- **`test_books.py`**: Adding books, updating records, searching, filtering by category, preventing duplicate ISBNs, and blocking deletion when books have active loans.
- **`test_members.py`**: Registering readers, validating email format, preventing duplicate emails, and editing details.
- **`test_borrowing.py`**: Issuing available books, preventing checkout when 0 copies remain, recording returns, preventing duplicate returns, and calculating overdue fines.
- **`test_auth.py`**: Password hash verification, invalid login rejection, unauthorized route redirection, and session teardown.
- **`test_analytics_and_export.py`**: Pandas DataFrame generation, NumPy statistical metrics, CSV streaming, and multi-tab Excel creation.

---

## 📁 Project Architecture

```
libraverse/
├── app.py                      # Flask application factory, routing & controllers
├── config.py                   # Environment, security & database configuration
├── database.py                 # SQLite connection manager, schema DDL & triggers
├── requirements.txt            # Project dependencies
├── seed.py                     # Idempotent database seeder with --reset option
├── README.md                   # Complete system documentation
│
├── services/                   # Modular Python business logic layer
│   ├── auth_service.py         # Passwords, sessions & CSRF protection
│   ├── book_service.py         # Catalog queries, search, add, edit, delete
│   ├── member_service.py       # Member CRUD, email validation, profile stats
│   ├── borrowing_service.py    # Atomic loans, returns, overdue calculations
│   ├── analytics_service.py    # Pandas aggregations & NumPy statistical matrix
│   └── export_service.py       # CSV generation & openpyxl multi-tab Excel workbooks
│
├── templates/                  # Jinja2 HTML templates
│   ├── base.html               # Master glassmorphism layout, navbar & modal
│   ├── index.html              # 3D Hero, floating books, live stats & catalog
│   ├── books.html              # Searchable, filterable, paginated 3D book grid
│   ├── book_details.html       # Dedicated volume inspection & 3D model
│   ├── about.html              # Architecture & technology blueprint
│   ├── login.html              # Cyber administrator authentication portal
│   ├── dashboard.html          # Command console with Chart.js visualizations
│   ├── manage_books.html       # Inventory table with Add/Edit/Delete modals
│   ├── manage_members.html     # Member registry with registration modal
│   ├── member_history.html     # Individual member loan history
│   ├── issue_return.html       # Circulation desk (checkout & return forms)
│   ├── borrowing_history.html  # Complete transaction audit ledger
│   ├── analytics.html          # Deep analytics & NumPy statistical matrix
│   └── error.html              # Futuristic error boundary (400, 403, 404, 500)
│
├── static/                     # Static web assets
│   ├── css/
│   │   ├── style.css           # Glassmorphism, colors, tables & typography
│   │   └── animations.css      # 3D transforms, book models, keyframes & parallax
│   └── js/
│       ├── main.js             # Navigation, counters, modals & scroll reveals
│       ├── book-3d.js          # Interactive 3D tilt engine & space parallax
│       └── dashboard.js        # Chart.js dark purple & cyan visual themes
│
├── instance/
│   └── library.db              # Persistent SQLite database
│
└── tests/                      # Automated test suite
    ├── conftest.py             # Isolated test database fixture & app setup
    ├── test_books.py           # Book management tests
    ├── test_members.py         # Member management tests
    ├── test_borrowing.py       # Loan transaction tests
    ├── test_auth.py            # Security & login tests
    └── test_analytics_and_export.py # Pandas, NumPy & export tests
```

---

## 📊 Technologies Used

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | Flask 3.1+ | Application routing, Jinja2 template rendering, HTTP handlers, session management |
| **Data Analytics** | Pandas 3.0+ | Relational aggregations, category grouping, popularity calculations, and tabular exports |
| **Numerical Computing** | NumPy 2.5+ | Descriptive statistics (mean, std, median, 90th percentile), linear fit trend slopes, and duration binning |
| **Database** | SQLite 3 | Persistent relational storage with foreign key constraints and transactional integrity |
| **Spreadsheet Engine** | openpyxl 3.1+ | Multi-sheet styled Excel workbook generation |
| **Data Visualizations**| Chart.js 4.4+ | Interactive dark purple/cyan charts (Doughnut, Bar, Area Line, Horizontal Bar) |
| **3D & Spatial UI** | CSS 3D Transforms | Perspective depths, 3D book construction, floating keyframes, and mouse tilt |
| **Styling** | Bootstrap 5 + CSS3 | Responsive glassmorphism interface, custom gradients, and flexbox grids |
| **Test Framework** | Pytest 9.1+ | Automated test execution with isolated test databases |

---

## 🛡️ License & Academic Integrity
Engineered for demonstration as a college software engineering capstone and professional full-stack development showcase. All rights reserved.
