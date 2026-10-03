import csv
import datetime
import hashlib
import sqlite3
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

# --- Database Viewer Popup Class ---
class DatabaseViewerPopup(Popup):
    def __init__(self, db_name='expense_tracker.db', **kwargs):
        super(DatabaseViewerPopup, self).__init__(**kwargs)
        self.title = "Database Inspector"
        self.size_hint = (0.9, 0.9)
        self.db_name = db_name

        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Table Selector Dropdown
        tables = self.get_tables()
        self.spinner = Spinner(text=tables[0] if tables else 'No Tables', values=tables, size_hint_y=None, height=44)
        self.spinner.bind(text=lambda spinner, text: self.load_data(text))
        layout.add_widget(self.spinner)

        # Scrollable View for Data
        self.scroll = ScrollView()
        self.label = Label(text="", size_hint_x=None, width=800, size_hint_y=None, halign='left', valign='top', markup=True)
        self.label.bind(texture_size=self.label.setter('size'))
        self.scroll.add_widget(self.label)
        layout.add_widget(self.scroll)

        # Close Button
        close_btn = Button(text="Close", size_hint_y=None, height=44)
        close_btn.bind(on_release=self.dismiss)
        layout.add_widget(close_btn)

        self.content = layout
        if tables:
            self.load_data(tables[0])

    def get_tables(self):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            return tables
        except:
            return []

    def load_data(self, table_name):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            cols = [col[1] for col in cursor.fetchall()]
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                self.label.text = f"Table '{table_name}' is empty."
                return

            header = " | ".join([f"[b]{c}[/b]" for c in cols])
            body = "\n".join([" | ".join(str(v) for v in r) for r in rows])
            self.label.text = f"[b]{table_name.upper()}[/b]\n\n{header}\n" + "-"*40 + f"\n{body}"
        except Exception as e:
            self.label.text = f"Error: {e}"

# --- DATABASE MANAGER ---
class DatabaseManager:

  def __init__(self, db_name="expenses.db"):
    self.conn = sqlite3.connect(db_name)
    self.cursor = self.conn.cursor()
    self.create_tables()

  def create_tables(self):
    self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_verified INTEGER DEFAULT 1,
                budget REAL DEFAULT 25000.0
            )
        """)
    self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT
            )
        """)
    self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL NOT NULL,
                source TEXT NOT NULL,
                date TEXT NOT NULL
            )
        """)

    for col_query in [
        "ALTER TABLE expenses ADD COLUMN user_id INTEGER",
        "ALTER TABLE income ADD COLUMN user_id INTEGER",
        "ALTER TABLE income ADD COLUMN source TEXT",
        "ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 1",
        "ALTER TABLE users ADD COLUMN budget REAL DEFAULT 25000.0",
    ]:
      try:
        self.cursor.execute(col_query)
      except sqlite3.OperationalError:
        pass

    self.conn.commit()

  def register_user(self, username, email, password):
    try:
      pwd_hash = hashlib.sha256(password.encode()).hexdigest()
      self.cursor.execute(
          "INSERT INTO users (username, email, password_hash, is_verified,"
          " budget) VALUES (?, ?, ?, ?, ?)",
          (username, email, pwd_hash, 1, 25000.0),
      )
      self.conn.commit()
      return True, "Registration successful! Please login."
    except sqlite3.IntegrityError:
      return False, "Email or Username already registered!"

  def login_user(self, identifier, password):
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    self.cursor.execute(
        "SELECT user_id, username, is_verified FROM users WHERE (email = ?"
        " OR username = ?) AND password_hash = ?",
        (identifier, identifier, pwd_hash),
    )
    return self.cursor.fetchone()

  def get_user_budget(self, user_id):
    self.cursor.execute(
        "SELECT budget FROM users WHERE user_id = ?", (user_id,)
    )
    res = self.cursor.fetchone()
    return res[0] if res and res[0] is not None else 25000.0

  def update_user_budget(self, user_id, new_budget):
    self.cursor.execute(
        "UPDATE users SET budget = ? WHERE user_id = ?", (new_budget, user_id)
    )
    self.conn.commit()

  def add_expense(self, user_id, amount, category, date_str, description):
    self.cursor.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description)"
        " VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, category, date_str, description),
    )
    self.conn.commit()

  def update_expense(self, expense_id, amount, category, date_str, description):
    self.cursor.execute(
        "UPDATE expenses SET amount = ?, category = ?, date = ?, description ="
        " ? WHERE id = ?",
        (amount, category, date_str, description, expense_id),
    )
    self.conn.commit()

  def delete_expense(self, expense_id):
    self.cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    self.conn.commit()

  def add_income(self, user_id, amount, source, date_str):
    self.cursor.execute(
        "INSERT INTO income (user_id, amount, source, date) VALUES (?, ?, ?,"
        " ?)",
        (user_id, amount, source, date_str),
    )
    self.conn.commit()

  def get_user_data(self, user_id):
    current_month = datetime.datetime.now().strftime("%Y-%m")
    self.cursor.execute(
        "SELECT SUM(amount) FROM expenses WHERE user_id = ? AND"
        " strftime('%Y-%m', date) = ?",
        (user_id, current_month),
    )
    res = self.cursor.fetchone()
    total_expense = res[0] if res and res[0] else 0.0

    self.cursor.execute(
        "SELECT SUM(amount) FROM income WHERE user_id = ? AND"
        " strftime('%Y-%m', date) = ?",
        (user_id, current_month),
    )
    res_inc = self.cursor.fetchone()
    total_income = res_inc[0] if res_inc and res_inc[0] else 0.0

    self.cursor.execute(
        "SELECT date, category, amount, description FROM expenses WHERE"
        " user_id = ? ORDER BY date DESC LIMIT 2",
        (user_id,),
    )
    recent = self.cursor.fetchall()
    return total_income, total_expense, recent

  def get_user_expenses_raw(self, user_id):
    self.cursor.execute(
        "SELECT id, amount, category, date, description FROM expenses WHERE"
        " user_id = ? ORDER BY date DESC",
        (user_id,),
    )
    return self.cursor.fetchall()

  def get_monthly_breakdown(self, user_id):
    self.cursor.execute(
        "SELECT strftime('%Y-%m', date) as month, SUM(amount) FROM expenses"
        " WHERE user_id = ? GROUP BY month ORDER BY month DESC",
        (user_id,),
    )
    return self.cursor.fetchall()

  def export_expenses_to_csv(self, user_id, filename="expenses_export.csv"):
    try:
      rows = self.get_user_expenses_raw(user_id)
      with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Amount", "Category", "Date", "Description"])
        for r in rows:
          writer.writerow(r)
      return True, f"Saved successfully as {filename}"
    except Exception as e:
      return False, str(e)


db = DatabaseManager()
current_user = {"id": None, "name": ""}


def show_popup(title, text):
  content = BoxLayout(orientation="vertical", padding=15, spacing=15)
  with content.canvas.before:
    Color(0.82, 0.88, 0.83, 1)
    rect = Rectangle(pos=content.pos, size=content.size)
  content.bind(
      pos=lambda s, w: setattr(rect, "pos", s.pos),
      size=lambda s, w: setattr(rect, "size", s.size),
  )

  lbl = Label(
      text=text,
      font_size="15sp",
      color=(0.1, 0.3, 0.2, 1),
      halign="center",
      valign="middle",
  )
  lbl.bind(size=lambda s, w: setattr(s, "text_size", (int(w[0]), None)))
  content.add_widget(lbl)

  btn = Button(
      text="OK", size_hint=(1, 0.5), background_color=(0.1, 0.5, 0.3, 1)
  )
  popup = Popup(
      title=title,
      content=content,
      size_hint=(0.7, 0.35),
      auto_dismiss=True,
      background="",
      background_color=(0.82, 0.88, 0.83, 1),
  )
  btn.bind(on_release=popup.dismiss)
  content.add_widget(btn)
  popup.open()


# --- LOGIN SCREEN ---
class LoginScreen(MDScreen):

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.md_bg_color = (0.82, 0.88, 0.83, 1)

    self.add_widget(
        Label(
            text="Personal Expense Tracker - Login",
            font_size="22sp",
            bold=True,
            color=(0.1, 0.3, 0.5, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.82},
        )
    )

    self.identifier_input = TextInput(
        hint_text="Enter email or username",
        multiline=False,
        size_hint=(0.8, 0.06),
        pos_hint={"center_x": 0.5, "center_y": 0.65},
    )
    self.pwd_input = TextInput(
        hint_text="Enter password",
        password=True,
        multiline=False,
        size_hint=(0.8, 0.06),
        pos_hint={"center_x": 0.5, "center_y": 0.53},
    )

    login_btn = Button(
        text="Login",
        size_hint=(0.4, 0.07),
        pos_hint={"center_x": 0.5, "center_y": 0.38},
        background_color=(0.1, 0.5, 0.8, 1),
    )
    login_btn.bind(on_release=self.verify_login)

    signup_btn = Button(
        text="Don't have an account? Sign Up",
        size_hint=(0.7, 0.06),
        pos_hint={"center_x": 0.5, "center_y": 0.25},
        background_color=(0.3, 0.3, 0.3, 1),
    )
    signup_btn.bind(
        on_release=lambda x: setattr(self.manager, "current", "signup")
    )

    self.add_widget(self.identifier_input)
    self.add_widget(self.pwd_input)
    self.add_widget(login_btn)
    self.add_widget(signup_btn)

  def verify_login(self, instance):
    identifier = self.identifier_input.text.strip()
    pwd = self.pwd_input.text.strip()

    if not identifier or not pwd:
      show_popup("Error", "Please fill all fields.")
      return

    user = db.login_user(identifier, pwd)
    if user:
      if user[2] == 0:
        show_popup(
            "Verification Required",
            "Please verify your email address before logging in.",
        )
        return
      current_user["id"] = user[0]
      current_user["name"] = user[1]
      self.identifier_input.text = ""
      self.pwd_input.text = ""
      Clock.schedule_once(self.switch_to_dashboard, 0.1)
    else:
      show_popup("Failed", "Invalid email/username or password!")

  def switch_to_dashboard(self, dt):
    self.manager.get_screen("dashboard").load_dashboard_data()
    self.manager.current = "dashboard"


# --- SIGNUP SCREEN ---
class SignupScreen(MDScreen):

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.md_bg_color = (0.82, 0.88, 0.83, 1)

    self.add_widget(
        Label(
            text="Create New Account",
            font_size="22sp",
            bold=True,
            color=(0.1, 0.3, 0.5, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.85},
        )
    )

    self.username_input = TextInput(
        hint_text="Username",
        multiline=False,
        size_hint=(0.8, 0.05),
        pos_hint={"center_x": 0.5, "center_y": 0.72},
    )
    self.email_input = TextInput(
        hint_text="Email Address",
        multiline=False,
        size_hint=(0.8, 0.05),
        pos_hint={"center_x": 0.5, "center_y": 0.60},
    )
    self.pwd_input = TextInput(
        hint_text="Password (min 8 chars & 1 special char)",
        password=True,
        multiline=False,
        size_hint=(0.8, 0.05),
        pos_hint={"center_x": 0.5, "center_y": 0.48},
    )

    reg_btn = Button(
        text="Sign Up",
        size_hint=(0.4, 0.06),
        pos_hint={"center_x": 0.5, "center_y": 0.35},
        background_color=(0.1, 0.7, 0.3, 1),
    )
    reg_btn.bind(on_release=self.register_user)

    back_btn = Button(
        text="Already have an account? Login",
        size_hint=(0.7, 0.05),
        pos_hint={"center_x": 0.5, "center_y": 0.23},
        background_color=(0.3, 0.3, 0.3, 1),
    )
    back_btn.bind(
        on_release=lambda x: setattr(self.manager, "current", "signup")
    )

    self.add_widget(self.username_input)
    self.add_widget(self.email_input)
    self.add_widget(self.pwd_input)
    self.add_widget(reg_btn)
    self.add_widget(back_btn)

  def register_user(self, instance):
    username = self.username_input.text.strip()
    email = self.email_input.text.strip()
    pwd = self.pwd_input.text.strip()

    if not username or not email or not pwd:
      show_popup("Error", "Please fill all fields.")
      return

    special_chars = "!@#$%^&*(),.?\":{}|<>-"
    if len(pwd) < 8 or not any(char in special_chars for char in pwd):
      show_popup(
          "Validation Error",
          "Password must be at least 8 chars long and contain 1 special"
          " character.",
      )
      return

    success, message = db.register_user(username, email, pwd)
    show_popup("Result", message)
    if success:
      self.manager.current = "login"


# --- DASHBOARD SCREEN ---
class DashboardScreen(MDScreen):

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.md_bg_color = (0.82, 0.88, 0.83, 1)

    self.header_label = Label(
        text="Expense & Budget Manager",
        font_size="22sp",
        bold=True,
        color=(0.1, 0.3, 0.2, 1),
        pos_hint={"center_x": 0.5, "center_y": 0.95},
    )
    
    self.summary_label = Label(
        text=(
            "Dashboard Summary (Current Month)\n\nIncome: ₹0.00        Expense:"
            " ₹0.00\nBalance: ₹0.00        Budget: ₹25,000.00"
        ),
        font_size="13sp",
        color=(0.1, 0.3, 0.2, 1),
        halign="center",
        valign="middle",
        pos_hint={"center_x": 0.5, "center_y": 0.78},
    )
    self.summary_label.bind(
        size=lambda s, w: setattr(s, "text_size", (int(w[0]), None))
    )

    add_exp_btn = Button(
        text="+ Add Expense",
        size_hint=(0.48, 0.05),
        pos_hint={"center_x": 0.26, "center_y": 0.62},
        background_color=(0.1, 0.5, 0.3, 1),
    )
    add_exp_btn.bind(on_release=self.open_add_expense_popup)

    add_inc_btn = Button(
        text="+ Add Income",
        size_hint=(0.48, 0.05),
        pos_hint={"center_x": 0.74, "center_y": 0.62},
        background_color=(0.1, 0.5, 0.3, 1),
    )
    add_inc_btn.bind(on_release=self.open_add_income_popup)

    history_btn = Button(
        text="History & Filter",
        size_hint=(0.48, 0.05),
        pos_hint={"center_x": 0.26, "center_y": 0.56},
        background_color=(0.3, 0.2, 0.6, 1),
    )
    history_btn.bind(on_release=self.open_history_popup)

    analytics_btn = Button(
        text="Analytics (Past Months)",
        size_hint=(0.48, 0.05),
        pos_hint={"center_x": 0.74, "center_y": 0.56},
        background_color=(0.2, 0.4, 0.7, 1),
    ) 
    analytics_btn.bind(on_release=self.open_analytics_popup)

    budget_btn = Button(
        text="Set Budget",
        size_hint=(0.48, 0.05),
        pos_hint={"center_x": 0.26, "center_y": 0.50},
        background_color=(0.8, 0.4, 0.1, 1),
    )
    budget_btn.bind(on_release=self.open_set_budget_popup)

    settings_btn = Button(
        text="Settings & CSV Export",
        size_hint=(0.48, 0.05),
        pos_hint={"center_x": 0.74, "center_y": 0.50},
        background_color=(0.5, 0.2, 0.6, 1),
    )
    settings_btn.bind(on_release=self.open_settings_popup)

     
    logout_btn = Button(
        text="Logout",
        size_hint=(0.96, 0.05),
        pos_hint={"center_x": 0.5, "center_y": 0.44},
        background_color=(0.7, 0.1, 0.1, 1),
    )
    logout_btn.bind(on_release=self.logout)

    self.trans_title = Label(
        text="Recent Transactions",
        font_size="15sp",
        bold=True,
        color=(0.1, 0.3, 0.2, 1),
        pos_hint={"center_x": 0.5, "center_y": 0.32},
    )

    self.trans_1 = Label(
        text="No recent transactions.",
        font_size="12sp",
        color=(0.2, 0.2, 0.2, 1),
        pos_hint={"center_x": 0.5, "center_y": 0.24},
    )
    self.trans_2 = Label(
        text="",
        font_size="12sp",
        color=(0.2, 0.2, 0.2, 1),
        pos_hint={"center_x": 0.5, "center_y": 0.18},
    )
    def open_database_viewer(self, instance):
      viewer = DatabaseViewerPopup()
      viewer.open()

    view_db_btn = Button(
        text="View Database (Debug)",
        size_hint=(0.96, 0.05),
        pos_hint={"center_x": 0.5, "center_y": 0.10},
        background_color=(0.3, 0.3, 0.3, 1),
    )
    view_db_btn.bind(on_release=lambda x: DatabaseViewerPopup().open())
    
    self.add_widget(self.header_label)
    self.add_widget(self.summary_label)
    self.add_widget(add_exp_btn)
    self.add_widget(add_inc_btn)
    self.add_widget(history_btn)
    self.add_widget(analytics_btn)
    self.add_widget(budget_btn)
    self.add_widget(settings_btn)
    self.add_widget(logout_btn)
    self.add_widget(self.trans_title)
    self.add_widget(self.trans_1)
    self.add_widget(self.trans_2)
    self.add_widget(view_db_btn)

  def open_add_expense_popup(self, instance):
    content = BoxLayout(orientation="vertical", padding=12, spacing=12)
    with content.canvas.before:
      Color(0.82, 0.88, 0.83, 1)
      rect = Rectangle(pos=content.pos, size=content.size)
    content.bind(
        pos=lambda s, w: setattr(rect, "pos", s.pos),
        size=lambda s, w: setattr(rect, "size", s.size),
    )

    amt_input = TextInput(hint_text="Amount (₹)", multiline=False)
    cat_spinner = Spinner(
        text="Select Category",
        values=(
            "Food",
            "Travel",
            "Bills",
            "Shopping",
            "Health",
            "Education",
            "Entertainment",
            "Other",
        ),
        size_hint=(1, 1),
        background_color=(0.1, 0.5, 0.3, 1),
    )
    date_input = TextInput(
        text=datetime.date.today().strftime("%Y-%m-%d"),
        hint_text="Date (YYYY-MM-DD)",
        multiline=False,
    )
    desc_input = TextInput(hint_text="Description / Note", multiline=False)

    submit_btn = Button(
        text="Save Expense",
        size_hint=(1, 1),
        background_color=(0.1, 0.6, 0.3, 1),
    )
    popup = Popup(
        title="Add New Expense",
        content=content,
        size_hint=(0.8, 0.65),
        auto_dismiss=True,
        background="",
        background_color=(0.82, 0.88, 0.83, 1),
    )

    def save(btn):
      try:
        amt = float(amt_input.text.strip())
        cat = cat_spinner.text
        date_str = date_input.text.strip()
        desc = desc_input.text.strip()

        if cat == "Select Category" or not cat:
          show_popup("Error", "Please select a valid category.")
          return

        datetime.datetime.strptime(date_str, "%Y-%m-%d")

        db.add_expense(current_user["id"], amt, cat, date_str, desc)
        popup.dismiss()
        self.load_dashboard_data()
        show_popup("Success", f"Expense added for date {date_str} successfully!")
      except ValueError:
        show_popup(
            "Error",
            "Please enter a valid amount and ensure date is in YYYY-MM-DD"
            " format.",
        )

    submit_btn.bind(on_release=save)
    content.add_widget(amt_input)
    content.add_widget(cat_spinner)
    content.add_widget(date_input)
    content.add_widget(desc_input)
    content.add_widget(submit_btn)
    popup.open()

  def open_add_income_popup(self, instance):
    content = BoxLayout(orientation="vertical", padding=12, spacing=12)
    with content.canvas.before:
      Color(0.82, 0.88, 0.83, 1)
      rect = Rectangle(pos=content.pos, size=content.size)
    content.bind(
        pos=lambda s, w: setattr(rect, "pos", s.pos),
        size=lambda s, w: setattr(rect, "size", s.size),
    )

    amt_input = TextInput(hint_text="Amount (₹)", multiline=False)
    source_input = TextInput(
        hint_text="Source (Salary, Freelance)", multiline=False
    )

    submit_btn = Button(
        text="Save Income",
        size_hint=(1, 1),
        background_color=(0.1, 0.6, 0.3, 1),
    )
    popup = Popup(
        title="Add New Income",
        content=content,
        size_hint=(0.8, 0.45),
        auto_dismiss=True,
        background="",
        background_color=(0.82, 0.88, 0.83, 1),
    )

    def save(btn):
      try:
        amt = float(amt_input.text.strip())
        src = source_input.text.strip()
        if not src:
          raise ValueError
        date_str = datetime.date.today().strftime("%Y-%m-%d")
        db.add_income(current_user["id"], amt, src, date_str)
        popup.dismiss()
        self.load_dashboard_data()
        show_popup("Success", "Income added successfully!")
      except ValueError:
        show_popup("Error", "Please enter valid amount and source.")

    submit_btn.bind(on_release=save)
    content.add_widget(amt_input)
    content.add_widget(source_input)
    content.add_widget(submit_btn)
    popup.open()

  def open_set_budget_popup(self, instance):
    content = BoxLayout(orientation="vertical", padding=15, spacing=12)
    with content.canvas.before:
      Color(0.82, 0.88, 0.83, 1)
      rect = Rectangle(pos=content.pos, size=content.size)
    content.bind(
        pos=lambda s, w: setattr(rect, "pos", s.pos),
        size=lambda s, w: setattr(rect, "size", s.size),
    )

    current_b = db.get_user_budget(current_user["id"])
    info_lbl = Label(
        text=f"Current Budget: ₹{current_b:,.2f}",
        font_size="14sp",
        color=(0.1, 0.3, 0.2, 1),
        size_hint_y=None,
        height=35,
    )
    budget_input = TextInput(
        hint_text="Enter new monthly budget (₹)",
        multiline=False,
        size_hint_y=None,
        height=45,
    )

    submit_btn = Button(
        text="Update Budget",
        size_hint=(1, 1),
        background_color=(0.8, 0.4, 0.1, 1),
    )
    popup = Popup(
        title="Set / Update Budget",
        content=content,
        size_hint=(0.8, 0.45),
        auto_dismiss=True,
        background="",
        background_color=(0.82, 0.88, 0.83, 1),
    )

    def update_budget(btn):
      try:
        new_b = float(budget_input.text.strip())
        if new_b <= 0:
          raise ValueError
        db.update_user_budget(current_user["id"], new_b)
        popup.dismiss()
        self.load_dashboard_data()
        show_popup("Success", f"Budget updated to ₹{new_b:,.2f} successfully!")
      except ValueError:
        show_popup("Error", "Please enter a valid numeric budget amount.")

    submit_btn.bind(on_release=update_budget)
    content.add_widget(info_lbl)
    content.add_widget(budget_input)
    content.add_widget(submit_btn)
    popup.open()

  def open_settings_popup(self, instance):
    content = BoxLayout(orientation="vertical", padding=15, spacing=15)
    with content.canvas.before:
      Color(0.82, 0.88, 0.83, 1)
      rect = Rectangle(pos=content.pos, size=content.size)
    content.bind(
        pos=lambda s, w: setattr(rect, "pos", s.pos),
        size=lambda s, w: setattr(rect, "size", s.size),
    )

    info_lbl = Label(
        text=(
            "Settings & Data Management\n\nExport your transaction history"
            " securely to CSV format."
        ),
        font_size="14sp",
        color=(0.1, 0.3, 0.2, 1),
        halign="center",
        valign="middle",
    )
    info_lbl.bind(size=lambda s, w: setattr(s, "text_size", (int(w[0]), None)))

    export_btn = Button(
        text="Export Data to CSV",
        size_hint=(1, 0.5),
        background_color=(0.3, 0.2, 0.6, 1),
    )

    def export_csv(btn):
      success, msg = db.export_expenses_to_csv(current_user["id"])
      if success:
        show_popup("Export Successful", msg)
      else:
        show_popup("Export Failed", msg)

    export_btn.bind(on_release=export_csv)

    close_btn = Button(
        text="Close",
        size_hint=(1, 0.5),
        background_color=(0.8, 0.2, 0.2, 1),
    )
    popup = Popup(
        title="Settings",
        content=content,
        size_hint=(0.8, 0.5),
        auto_dismiss=True,
        background="",
        background_color=(0.82, 0.88, 0.83, 1),
    )
    close_btn.bind(on_release=popup.dismiss)

    content.add_widget(info_lbl)
    content.add_widget(export_btn)
    content.add_widget(close_btn)
    popup.open()

  def open_history_popup(self, instance):
    content = BoxLayout(orientation="vertical", padding=15, spacing=10)
    with content.canvas.before:
      Color(0.82, 0.88, 0.83, 1)
      rect = Rectangle(pos=content.pos, size=content.size)
    content.bind(
        pos=lambda s, w: setattr(rect, "pos", s.pos),
        size=lambda s, w: setattr(rect, "size", s.size),
    )

    scroll = ScrollView(size_hint=(1, 0.8))
    hist_layout = BoxLayout(
        orientation="vertical", size_hint_y=None, spacing=10, padding=5
    )
    hist_layout.bind(minimum_height=hist_layout.setter("height"))

    def refresh_history(popup_to_refresh):
      hist_layout.clear_widgets()
      rows = db.get_user_expenses_raw(current_user["id"])
      if not rows:
        hist_layout.add_widget(
            Label(
                text="No transaction history found.",
                font_size="14sp",
                color=(0.2, 0.2, 0.2, 1),
                size_hint_y=None,
                height=40,
            )
        )
      else:
        for r in rows:
          row_box = BoxLayout(
              orientation="horizontal",
              size_hint_y=None,
              height=45,
              spacing=10,
          )

          row_text = f"Date: {r[3]} | Cat: {r[2]} | Amt: ₹{r[1]} | Note: {r[4] or ''}"
          lbl = Label(
              text=row_text,
              font_size="12sp",
              color=(0.2, 0.2, 0.2, 1),
              size_hint_x=0.6,
              halign="left",
              valign="middle",
          )
          lbl.bind(size=lambda s, w: setattr(s, "text_size", (int(w[0]), None)))

          edit_btn = Button(
              text="Edit",
              size_hint_x=0.2,
              background_color=(0.2, 0.5, 0.8, 1),
          )
          del_btn = Button(
              text="Delete",
              size_hint_x=0.2,
              background_color=(0.8, 0.2, 0.2, 1),
          )

          def make_edit_action(
              exp_id, cur_amt, cur_cat, cur_date, cur_desc
          ):
            return lambda x: self.open_edit_expense_popup(
                exp_id,
                cur_amt,
                cur_cat,
                cur_date,
                cur_desc,
                popup_to_refresh,
                refresh_history,
            )

          def make_del_action(exp_id):
            return lambda x: self.confirm_delete_expense(
                exp_id, popup_to_refresh, refresh_history
            )

          edit_btn.bind(on_release=make_edit_action(r[0], r[1], r[2], r[3], r[4]))
          del_btn.bind(on_release=make_del_action(r[0]))

          row_box.add_widget(lbl)
          row_box.add_widget(edit_btn)
          row_box.add_widget(del_btn)
          hist_layout.add_widget(row_box)

    close_btn = Button(
        text="Close",
        size_hint=(1, 0.18),
        background_color=(0.8, 0.2, 0.2, 1),
    )
    popup = Popup(
        title="Transaction History (Edit / Delete)",
        content=content,
        size_hint=(0.9, 0.8),
        auto_dismiss=True,
        background="",
        background_color=(0.82, 0.88, 0.83, 1),
    )
    close_btn.bind(on_release=popup.dismiss)

    refresh_history(popup)

    scroll.add_widget(hist_layout)
    content.add_widget(scroll)
    content.add_widget(close_btn)
    popup.open()

  def confirm_delete_expense(self, exp_id, parent_popup, refresh_callback):
    """Are you sure you want to delete this transaction? confirmation popup"""
    content = BoxLayout(orientation="vertical", padding=15, spacing=15)
    with content.canvas.before:
      Color(0.82, 0.88, 0.83, 1)
      rect = Rectangle(pos=content.pos, size=content.size)
    content.bind(
        pos=lambda s, w: setattr(rect, "pos", s.pos),
        size=lambda s, w: setattr(rect, "size", s.size),
    )

    lbl = Label(
        text="Are you sure you want to delete this transaction?",
        font_size="15sp",
        color=(0.1, 0.3, 0.2, 1),
        halign="center",
        valign="middle",
    )
    lbl.bind(size=lambda s, w: setattr(s, "text_size", (int(w[0]), None)))
    content.add_widget(lbl)

    btn_layout = BoxLayout(
        orientation="horizontal", size_hint=(1, 0.5), spacing=10
    )
    yes_btn = Button(
        text="Yes, Delete",
        background_color=(0.8, 0.2, 0.2, 1),
    )
    no_btn = Button(
        text="Cancel",
        background_color=(0.5, 0.5, 0.5, 1),
    )

    conf_popup = Popup(
        title="Confirm Deletion",
        content=content,
        size_hint=(0.7, 0.35),
        auto_dismiss=True,
        background="",
        background_color=(0.82, 0.88, 0.83, 1),
    )

    def do_delete(instance):
      db.delete_expense(exp_id)
      conf_popup.dismiss()
      refresh_callback(parent_popup)
      self.load_dashboard_data()
      show_popup("Deleted", "Transaction removed successfully.")

    yes_btn.bind(on_release=do_delete)
    no_btn.bind(on_release=conf_popup.dismiss)

    btn_layout.add_widget(yes_btn)
    btn_layout.add_widget(no_btn)
    content.add_widget(btn_layout)
    conf_popup.open()

  def open_edit_expense_popup(
      self, exp_id, amt, cat, date_val, desc, parent_popup, refresh_callback
  ):
    content = BoxLayout(orientation="vertical", padding=12, spacing=12)
    with content.canvas.before:
      Color(0.82, 0.88, 0.83, 1)
      rect = Rectangle(pos=content.pos, size=content.size)
    content.bind(
        pos=lambda s, w: setattr(rect, "pos", s.pos),
        size=lambda s, w: setattr(rect, "size", s.size),
    )

    amt_input = TextInput(
        text=str(amt), hint_text="Amount (₹)", multiline=False
    )
    cat_spinner = Spinner(
        text=cat,
        values=(
            "Food",
            "Travel",
            "Bills",
            "Shopping",
            "Health",
            "Education",
            "Entertainment",
            "Other",
        ),
        size_hint=(1, 1),
        background_color=(0.1, 0.5, 0.3, 1),
    )
    date_input = TextInput(
        text=str(date_val), hint_text="Date (YYYY-MM-DD)", multiline=False
    )
    desc_input = TextInput(
        text=str(desc or ""), hint_text="Description / Note", multiline=False
    )

    update_btn = Button(
        text="Update Expense",
        size_hint=(1, 1),
        background_color=(0.1, 0.6, 0.3, 1),
    )
    popup = Popup(
        title="Edit Expense",
        content=content,
        size_hint=(0.75, 0.55),
        auto_dismiss=True,
        background="",
        background_color=(0.82, 0.88, 0.83, 1),
    )

    def save_update(btn):
      try:
        new_amt = float(amt_input.text.strip())
        new_cat = cat_spinner.text
        new_date = date_input.text.strip()
        new_desc = desc_input.text.strip()

        datetime.datetime.strptime(new_date, "%Y-%m-%d")

        db.update_expense(exp_id, new_amt, new_cat, new_date, new_desc)
        popup.dismiss()
        refresh_callback(parent_popup)
        self.load_dashboard_data()
        show_popup("Success", "Expense updated successfully!")
      except ValueError:
        show_popup(
            "Error",
            "Please check values. Date must be in YYYY-MM-DD format.",
        )

    update_btn.bind(on_release=save_update)
    content.add_widget(amt_input)
    content.add_widget(cat_spinner)
    content.add_widget(date_input)
    content.add_widget(desc_input)
    content.add_widget(update_btn)
    popup.open()

  def open_analytics_popup(self, instance):
    content = BoxLayout(orientation="vertical", padding=15, spacing=10)
    with content.canvas.before:
      Color(0.82, 0.88, 0.83, 1)
      rect = Rectangle(pos=content.pos, size=content.size)
    content.bind(
        pos=lambda s, w: setattr(rect, "pos", s.pos),
        size=lambda s, w: setattr(rect, "size", s.size),
    )

    scroll = ScrollView(size_hint=(1, 0.8))
    anal_layout = BoxLayout(
        orientation="vertical", size_hint_y=None, spacing=8, padding=5
    )
    anal_layout.bind(minimum_height=anal_layout.setter("height"))

    breakdown = db.get_monthly_breakdown(current_user["id"])
    if not breakdown:
      anal_layout.add_widget(
          Label(
              text="No monthly analytics available yet.",
              font_size="14sp",
              color=(0.2, 0.2, 0.2, 1),
              size_hint_y=None,
              height=40,
          )
      )
    else:
      anal_layout.add_widget(
          Label(
              text="Month-wise Expense Breakdown:",
              font_size="14sp",
              bold=True,
              color=(0.1, 0.3, 0.2, 1),
              size_hint_y=None,
              height=35,
          )
      )
      for b in breakdown:
        row_text = f"Month: {b[0]}  --->  Total Spent: ₹{b[1]:,.2f}"
        lbl = Label(
            text=row_text,
            font_size="13sp",
            color=(0.1, 0.3, 0.2, 1),
            size_hint_y=None,
            height=35,
            halign="left",
            valign="middle",
        )
        lbl.bind(size=lambda s, w: setattr(s, "text_size", (int(w[0]), None)))
        anal_layout.add_widget(lbl)

    scroll.add_widget(anal_layout)
    close_btn = Button(
        text="Close",
        size_hint=(1, 0.18),
        background_color=(0.8, 0.2, 0.2, 1),
    )
    popup = Popup(
        title="Monthly Analytics",
        content=content,
        size_hint=(0.85, 0.75),
        auto_dismiss=True,
        background="",
        background_color=(0.82, 0.88, 0.83, 1),
    )
    close_btn.bind(on_release=popup.dismiss)

    content.add_widget(scroll)
    content.add_widget(close_btn)
    popup.open()

  def load_dashboard_data(self, *args):
    self.header_label.text = (
        f"Expense & Budget Manager ({current_user['name']})"
    )
    inc, exp, recent = db.get_user_data(current_user["id"])
    user_budget = db.get_user_budget(current_user["id"])
    balance = inc - exp
    pct = int((exp / user_budget) * 100) if user_budget > 0 else 0

    status_msg = "Budget Normal & Safe"
    if pct > 100:
      status_msg = "Warning: Budget Exceeded!"
    elif pct > 80:
      status_msg = "Alert: Close to Budget Limit!"

    self.summary_label.text = (
        f"Dashboard Summary (Current Month)\n\nIncome: ₹{inc:,.2f}        Expense:"
        f" ₹{exp:,.2f}\nBalance: ₹{balance:,.2f}        Budget:"
        f" ₹{user_budget:,.2f}\n\nBudget Used: {pct}%\n{status_msg}"
    )

    if len(recent) > 0:
      self.trans_1.text = (
          f"Date: {recent[0][0]} | {recent[0][1]} | ₹{recent[0][2]} |"
          f" {recent[0][3] or ''}"
      )
    else:
      self.trans_1.text = "No recent transactions."

    if len(recent) > 1:
      self.trans_2.text = (
          f"Date: {recent[1][0]} | {recent[1][1]} | ₹{recent[1][2]} |"
          f" {recent[1][3] or ''}"
      )
    else:
      self.trans_2.text = ""

  def logout(self, instance):
    current_user["id"] = None
    current_user["name"] = ""
    self.manager.current = "login"




# --- MAIN APP ---
class ExpenseApp(MDApp):

  def build(self):
    self.theme_cls.theme_style = "Light"
    self.theme_cls.primary_palette = "Green"
    sm = ScreenManager()
    sm.add_widget(LoginScreen(name="login"))
    sm.add_widget(SignupScreen(name="signup"))
    sm.add_widget(DashboardScreen(name="dashboard"))
    return sm


if __name__ == "__main__":
  ExpenseApp().run()