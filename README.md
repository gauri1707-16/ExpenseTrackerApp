Markdown
# Personal Expense Tracker

A modern, offline-first desktop application built with Python, KivyMD, and SQLite3 to help users efficiently manage their daily expenditures, monitor monthly budgets, and analyze financial habits through visual charts.

---

## Key Features
* **Material Design UI**: Clean, responsive, and intuitive interface powered by the KivyMD framework.
* **Local Data Persistence**: Secure, lightweight relational data storage using SQLite3.
* **Smart Budget Monitoring**: Configurable monthly budget limits with automated tracking.
* **Visual Analytics**: Integrated Matplotlib engine that dynamically generates categorical spending distribution charts.
* **Cross-Platform Compatibility**: Runs smoothly on desktop operating systems (Windows, Linux, macOS) with Android APK build support via Buildozer.

---

## Tech Stack
* **Language**: Python 3.8+
* **Frontend UI**: Kivy & KivyMD
* **Database**: SQLite3
* **Analytics**: Matplotlib

---

## Installation & Setup Guide

### Prerequisites
Ensure you have Python 3.8 or higher installed on your system along with the pip package manager.

### Step 1: Clone the Repository
```bash
git clone [https://github.com/your-username/personal-expense-tracker.git](https://github.com/your-username/personal-expense-tracker.git)
cd personal-expense-tracker
```

### Step 2: Install Dependencies
Run the following command in your terminal to install the required libraries:

```bash
pip install kivy kivymd matplotlib
```

Step 3: Run the Application
Execute the main script to launch the desktop application:

```bash
Bash
```

## Build and Install on Android

Buildozer runs on Linux. On Windows, use WSL2 with Ubuntu, then run:

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip buildozer cython
buildozer android debug
```

The first build downloads the Android SDK and NDK and can take several minutes. The APK is created in the `bin` folder. Install it on a connected phone with:

```bash
adb install -r bin/*.apk
```

The app stores its database and generated chart in Android's writable app-data directory, so data can be saved between launches.

python main.py
Usage Instructions
Dashboard Overview: View your current monthly totals and active budget constraints upon launching.

Add Expense: Enter the transaction amount, select a category, and optionally add a description to log your spending.

View Analytics: Click the analytics tab to inspect your spending breakdown via visual pie charts.
