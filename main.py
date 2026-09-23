import os
import sqlite3
import csv
from datetime import datetime, timedelta
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle

# --- DATABASE SETUP ---
import os
def get_db_path():
  db_name = 'expenses.db'
  return db_name    

def init_db():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            category TEXT,
            date TEXT,
            description TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            date TEXT,
            description TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value REAL
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('monthly_budget', 25000.0)")
    conn.commit()
    conn.close()

# --- STYLISH ROUNDED CONTAINER ---
class RoundedBox(BoxLayout):
    def __init__(self, bg_color=(1, 1, 1, 1), radius=12, **kwargs):
        super(RoundedBox, self).__init__(**kwargs)
        self.bg_color = bg_color
        self.radius = radius
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[self.radius])
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

# --- MAIN APPLICATION ROOT ---
class ExpenseTrackerRoot(BoxLayout):
    def __init__(self, **kwargs):
        super(ExpenseTrackerRoot, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 12

        # App Background: Soft Teal Shade
        with self.canvas.before:
            Color(0.86, 0.94, 0.92, 1)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[0])
        self.bind(size=self._update_rect, pos=self._update_rect)

        # Header Title
        title_layout = BoxLayout(size_hint_y=None, height=40)
        title_layout.add_widget(Label(
            text="[b]Expense & Budget Manager[/b]", 
            markup=True, 
            font_size=18, 
            color=(0.10, 0.22, 0.20, 1),
            halign='center'
        ))
        self.add_widget(title_layout)

        # Scrollable Content Area
        scroll = ScrollView(size_hint=(1, 1))
        self.main_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=14, padding=5)
        self.main_container.bind(minimum_height=self.main_container.setter('height'))
        scroll.add_widget(self.main_container)
        self.add_widget(scroll)

        self.refresh_dashboard()

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def clear_view(self):
        self.main_container.clear_widgets()

    # --- CUSTOM POPUP SYSTEM ---
    def show_popup(self, title, message):
      content = BoxLayout(orientation='vertical', padding=15, spacing=12)
      content.add_widget(
          Label(
              text=message,
              color=(1, 1, 1, 1),  # Pure Bright White text for clear visibility
              halign='center',
              font_size=14,
          )
      )

      close_btn = Button(
          text='OK',
          size_hint_y=None,
          height=42,
          background_normal='',
          background_color=(0.12, 0.45, 0.42, 1),
          color=(1, 1, 1, 1),
          bold=True,
      )

      popup = Popup(
          title=title, content=content, size_hint=(0.85, 0.3), auto_dismiss=True
      )
      close_btn.bind(on_press=popup.dismiss)
      content.add_widget(close_btn)
      popup.open()

    # --- 1. CORE DASHBOARD ---
    def refresh_dashboard(self):
        self.clear_view()

        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        now = datetime.now()
        current_month_str = now.strftime("%Y-%m")
        current_month_name = now.strftime("%B")
        
        first_day_current = now.replace(day=1)
        last_day_prev = first_day_current - timedelta(days=1)
        prev_month_str = last_day_prev.strftime("%Y-%m")
        prev_month_name = last_day_prev.strftime("%B")

        cursor.execute("SELECT SUM(amount) FROM income WHERE date LIKE ?", (f"{current_month_str}%",))
        inc_res = cursor.fetchone()[0]
        total_income = inc_res if inc_res else 0.0

        cursor.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE ?", (f"{current_month_str}%",))
        exp_res = cursor.fetchone()[0]
        total_expense = exp_res if exp_res else 0.0

        cursor.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE ?", (f"{prev_month_str}%",))
        prev_exp_res = cursor.fetchone()[0]
        prev_expense = prev_exp_res if prev_exp_res else 0.0

        cursor.execute("SELECT value FROM settings WHERE key='monthly_budget'")
        b_res = cursor.fetchone()
        monthly_budget = b_res[0] if b_res else 25000.0

        cursor.execute("SELECT category, SUM(amount) as total FROM expenses WHERE date LIKE ? GROUP BY category ORDER BY total DESC LIMIT 1", (f"{current_month_str}%",))
        top_cat_res = cursor.fetchone()
        conn.close()

        remaining_balance = total_income - total_expense
        budget_used_pct = (total_expense / monthly_budget * 100) if monthly_budget > 0 else 0.0
        if budget_used_pct > 100:
            budget_used_pct = 100.0

        filled_blocks = int(budget_used_pct / 6)
        empty_blocks = 16 - filled_blocks
        progress_bar_str = "[" + "=" * filled_blocks + "-" * empty_blocks + "]"

        diff = total_expense - prev_expense
        if diff > 0:
            comp_text = f"Change: ₹{diff:,.2f} more than {prev_month_name}"
            comp_color = (0.80, 0.25, 0.25, 1)
        elif diff < 0:
            comp_text = f"Change: ₹{abs(diff):,.2f} less than {prev_month_name}"
            comp_color = (0.08, 0.50, 0.25, 1)
        else:
            comp_text = f"Change: Same as {prev_month_name}"
            comp_color = (0.30, 0.38, 0.36, 1)

        dash_card = RoundedBox(bg_color=(1, 1, 1, 1), radius=16, orientation='vertical', size_hint_y=None, height=330, padding=14, spacing=6)
        
        dash_card.add_widget(Label(text=f"[b]Dashboard Summary ({current_month_name})[/b]", markup=True, font_size=15, color=(0.12, 0.20, 0.18, 1), size_hint_y=None, height=22))
        
        stats_layout_1 = GridLayout(cols=2, size_hint_y=None, height=38)
        stats_layout_1.add_widget(Label(text=f"Income\n[b]₹{total_income:,.2f}[/b]", markup=True, color=(0.08, 0.50, 0.25, 1), font_size=13, halign='center'))
        stats_layout_1.add_widget(Label(text=f"Expense\n[b]₹{total_expense:,.2f}[/b]", markup=True, color=(0.80, 0.20, 0.20, 1), font_size=13, halign='center'))
        dash_card.add_widget(stats_layout_1)

        stats_layout_2 = GridLayout(cols=2, size_hint_y=None, height=38)
        stats_layout_2.add_widget(Label(text=f"Balance\n[b]₹{remaining_balance:,.2f}[/b]", markup=True, color=(0.1, 0.35, 0.70, 1), font_size=13, halign='center'))
        stats_layout_2.add_widget(Label(text=f"Budget\n[b]₹{monthly_budget:,.2f}[/b]", markup=True, color=(0.75, 0.42, 0.1, 1), font_size=13, halign='center'))
        dash_card.add_widget(stats_layout_2)

        dash_card.add_widget(Label(text=f"Budget Used: {budget_used_pct:.0f}%", color=(0.3, 0.3, 0.3, 1), font_size=12, size_hint_y=None, height=18))
        dash_card.add_widget(Label(text=progress_bar_str, color=(0.12, 0.45, 0.42, 1), font_size=14, bold=True, size_hint_y=None, height=20))

        if total_expense > monthly_budget:
            status_text = "Status: Budget Exceeded!"
            status_color = (0.85, 0.15, 0.15, 1)
        elif budget_used_pct >= 85:
            status_text = "Warning: Budget nearly full"
            status_color = (0.80, 0.40, 0.1, 1)
        else:
            status_text = "Budget Normal & Safe"
            status_color = (0.08, 0.50, 0.25, 1)

        dash_card.add_widget(Label(text=status_text, color=status_color, bold=True, font_size=12, size_hint_y=None, height=20))
        dash_card.add_widget(Label(text=comp_text, color=comp_color, font_size=11, size_hint_y=None, height=18))

        if top_cat_res:
            insight_text = f"Insight: {top_cat_res[0]} is your highest category (₹{top_cat_res[1]:,.2f})"
        else:
            insight_text = "Insight: Add expenses to view category insights."
        dash_card.add_widget(Label(text=insight_text, color=(0.25, 0.35, 0.55, 1), font_size=11, size_hint_y=None, height=20))

        self.main_container.add_widget(dash_card)

        btn_grid = GridLayout(cols=2, size_hint_y=None, height=175, spacing=8)
        
        add_exp_btn = Button(text="+ Add Expense", background_normal='', background_color=(0.12, 0.45, 0.42, 1), bold=True, font_size=13)
        add_exp_btn.bind(on_press=lambda x: self.show_add_expense_screen())
        btn_grid.add_widget(add_exp_btn)

        add_inc_btn = Button(text="+ Add Income", background_normal='', background_color=(0.10, 0.55, 0.32, 1), bold=True, font_size=13)
        add_inc_btn.bind(on_press=lambda x: self.show_add_income_screen())
        btn_grid.add_widget(add_inc_btn)

        history_btn = Button(text="History & Filter", background_normal='', background_color=(0.35, 0.25, 0.65, 1), bold=True, font_size=13)
        history_btn.bind(on_press=lambda x: self.show_history_screen())
        btn_grid.add_widget(history_btn)

        analytics_btn = Button(text="Analytics (Past Months)", background_normal='', background_color=(0.20, 0.45, 0.65, 1), bold=True, font_size=12)
        analytics_btn.bind(on_press=lambda x: self.show_analytics_screen())
        btn_grid.add_widget(analytics_btn)

        budget_btn = Button(text="Set Budget", background_normal='', background_color=(0.75, 0.42, 0.1, 1), bold=True, font_size=13)
        budget_btn.bind(on_press=lambda x: self.show_budget_screen())
        btn_grid.add_widget(budget_btn)

        view_db_btn = Button(text="View Database (.db)", background_normal='', background_color=(0.5, 0.2, 0.6, 1), bold=True, font_size=13)
        view_db_btn.bind(on_press=lambda x: self.show_raw_database_screen())
        btn_grid.add_widget(view_db_btn)

        settings_btn = Button(text="Settings", background_normal='', background_color=(0.4, 0.4, 0.4, 1), bold=True, font_size=13)
        settings_btn.bind(on_press=lambda x: self.show_settings_screen())
        btn_grid.add_widget(settings_btn)

        btn_grid.add_widget(Label(text=""))
        self.main_container.add_widget(btn_grid)

        self.main_container.add_widget(Label(text="[b]Recent Transactions[/b]", markup=True, font_size=15, color=(0.15, 0.25, 0.22, 1), size_hint_y=None, height=28))
        
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT id, amount, category, date, description FROM expenses ORDER BY id DESC LIMIT 4")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            self.main_container.add_widget(Label(text="No transactions recorded yet.", color=(0.4, 0.4, 0.4, 1), size_hint_y=None, height=30))
        else:
            for row in rows:
                eid, amt, cat, dt, desc = row
                item_card = RoundedBox(bg_color=(1, 1, 1, 1), radius=8, size_hint_y=None, height=38, padding=8)
                item_card.add_widget(Label(text=f"[b]{dt}[/b] | {cat} | [color=#d93838]₹{amt:,.2f}[/color] | {desc}", markup=True, color=(0.2, 0.2, 0.2, 1), font_size=12))
                self.main_container.add_widget(item_card)

    # --- RAW DATABASE VIEWER SCREEN ---
    def show_raw_database_screen(self):
        self.clear_view()
        self.main_container.add_widget(Label(text="[b]SQLite Database Viewer (expenses.db)[/b]", markup=True, font_size=16, color=(0.12, 0.20, 0.18, 1), size_hint_y=None, height=35))

        db_scroll_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=8)
        db_scroll_box.bind(minimum_height=db_scroll_box.setter('height'))

        scroll_db = ScrollView(size_hint=(1, None), height=350)
        scroll_db.add_widget(db_scroll_box)
        self.main_container.add_widget(scroll_db)

        try:
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()

            db_scroll_box.add_widget(Label(text="[b]-- Table: expenses --[/b]", markup=True, color=(0.15, 0.45, 0.4, 1), size_hint_y=None, height=25))
            cursor.execute("SELECT id, amount, category, date, description FROM expenses")
            exp_rows = cursor.fetchall()
            
            if not exp_rows:
                db_scroll_box.add_widget(Label(text="Table 'expenses' is empty.", color=(0.4, 0.4, 0.4, 1), size_hint_y=None, height=30))
            else:
                for r in exp_rows:
                    card = RoundedBox(bg_color=(1, 1, 1, 1), radius=6, size_hint_y=None, height=36, padding=6)
                    card.add_widget(Label(text=f"ID:{r[0]} | ₹{r[1]} | {r[2]} | {r[3]} | {r[4]}", color=(0.2, 0.2, 0.2, 1), font_size=11))
                    db_scroll_box.add_widget(card)

            db_scroll_box.add_widget(Label(text="[b]-- Table: income --[/b]", markup=True, color=(0.1, 0.5, 0.3, 1), size_hint_y=None, height=25))
            cursor.execute("SELECT id, amount, date, description FROM income")
            inc_rows = cursor.fetchall()

            if not inc_rows:
                db_scroll_box.add_widget(Label(text="Table 'income' is empty.", color=(0.4, 0.4, 0.4, 1), size_hint_y=None, height=30))
            else:
                for r in inc_rows:
                    card = RoundedBox(bg_color=(1, 1, 1, 1), radius=6, size_hint_y=None, height=36, padding=6)
                    card.add_widget(Label(text=f"ID:{r[0]} | ₹{r[1]} | {r[2]} | {r[3]}", color=(0.2, 0.2, 0.2, 1), font_size=11))
                    db_scroll_box.add_widget(card)

            conn.close()
        except Exception as e:
            db_scroll_box.add_widget(Label(text=f"Error reading DB: {str(e)}", color=(0.8, 0.2, 0.2, 1), size_hint_y=None, height=35))

        back_btn = Button(text="Back to Dashboard", size_hint_y=None, height=45, background_normal='', background_color=(0.3, 0.38, 0.42, 1), bold=True)
        back_btn.bind(on_press=lambda x: self.refresh_dashboard())
        self.main_container.add_widget(back_btn)

    # --- ADD EXPENSE SCREEN ---
    def show_add_expense_screen(self):
        self.clear_view()
        self.main_container.add_widget(Label(text="[b]+ Add New Expense[/b]", markup=True, font_size=17, color=(0.12, 0.20, 0.18, 1), size_hint_y=None, height=35))

        self.exp_amt = TextInput(hint_text="Amount (e.g. 350)", multiline=False, input_filter='float', size_hint_y=None, height=45)
        self.exp_cat = Spinner(text='Food', values=('Food', 'Travel', 'Shopping', 'Bills', 'Entertainment', 'Health', 'Education', 'Other'), size_hint_y=None, height=45)
        self.exp_date = TextInput(text=datetime.now().strftime("%Y-%m-%d"), hint_text="Date (YYYY-MM-DD)", multiline=False, size_hint_y=None, height=45)
        self.exp_desc = TextInput(hint_text="Note / Description", multiline=False, size_hint_y=None, height=45)

        self.main_container.add_widget(Label(text="Amount (₹):", color=(0.15, 0.25, 0.22, 1), bold=True, size_hint_y=None, height=22))
        self.main_container.add_widget(self.exp_amt)
        self.main_container.add_widget(Label(text="Category:", color=(0.15, 0.25, 0.22, 1), bold=True, size_hint_y=None, height=22))
        self.main_container.add_widget(self.exp_cat)
        self.main_container.add_widget(Label(text="Select Custom Date (YYYY-MM-DD):", color=(0.15, 0.25, 0.22, 1), bold=True, size_hint_y=None, height=22))
        self.main_container.add_widget(self.exp_date)
        self.main_container.add_widget(Label(text="Note:", color=(0.15, 0.25, 0.22, 1), bold=True, size_hint_y=None, height=22))
        self.main_container.add_widget(self.exp_desc)

        save_btn = Button(text="Save Expense", size_hint_y=None, height=48, background_normal='', background_color=(0.12, 0.55, 0.3, 1), bold=True)
        save_btn.bind(on_press=self.save_expense_db)
        self.main_container.add_widget(save_btn)

        back_btn = Button(text="Back to Dashboard", size_hint_y=None, height=45, background_normal='', background_color=(0.3, 0.38, 0.42, 1), bold=True)
        back_btn.bind(on_press=lambda x: self.refresh_dashboard())
        self.main_container.add_widget(back_btn)

    def save_expense_db(self, instance):
        try:
            amt = float(self.exp_amt.text.strip())
            cat = self.exp_cat.text
            dt = self.exp_date.text.strip()
            desc = self.exp_desc.text.strip()
            if amt <= 0: raise ValueError()

            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            cursor.execute("INSERT INTO expenses (amount, category, date, description) VALUES (?, ?, ?, ?)", (amt, cat, dt, desc))
            conn.commit()
            conn.close()

            self.show_popup("Success", "Expense added successfully!")
            self.refresh_dashboard()
        except ValueError:
            self.show_popup("Invalid Input", "Please enter a valid numeric amount greater than 0.")

    # --- ADD INCOME SCREEN ---
    def show_add_income_screen(self):
        self.clear_view()
        self.main_container.add_widget(Label(text="[b]+ Add Income[/b]", markup=True, font_size=17, color=(0.12, 0.20, 0.18, 1), size_hint_y=None, height=35))

        self.inc_amt = TextInput(hint_text="Amount (e.g. 30000)", multiline=False, input_filter='float', size_hint_y=None, height=45)
        self.inc_date = TextInput(text=datetime.now().strftime("%Y-%m-%d"), hint_text="Date (YYYY-MM-DD)", multiline=False, size_hint_y=None, height=45)
        self.inc_desc = TextInput(hint_text="Description (e.g. Salary)", multiline=False, size_hint_y=None, height=45)

        self.main_container.add_widget(Label(text="Amount (₹):", color=(0.15, 0.25, 0.22, 1), bold=True, size_hint_y=None, height=22))
        self.main_container.add_widget(self.inc_amt)
        self.main_container.add_widget(Label(text="Date:", color=(0.15, 0.25, 0.22, 1), bold=True, size_hint_y=None, height=22))
        self.main_container.add_widget(self.inc_date)
        self.main_container.add_widget(Label(text="Description:", color=(0.15, 0.25, 0.22, 1), bold=True, size_hint_y=None, height=22))
        self.main_container.add_widget(self.inc_desc)

        save_btn = Button(text="Save Income", size_hint_y=None, height=48, background_normal='', background_color=(0.1, 0.5, 0.32, 1), bold=True)
        save_btn.bind(on_press=self.save_income_db)
        self.main_container.add_widget(save_btn)

        back_btn = Button(text="Back to Dashboard", size_hint_y=None, height=45, background_normal='', background_color=(0.3, 0.38, 0.42, 1), bold=True)
        back_btn.bind(on_press=lambda x: self.refresh_dashboard())
        self.main_container.add_widget(back_btn)

    def save_income_db(self, instance):
        try:
            amt = float(self.inc_amt.text.strip())
            dt = self.inc_date.text.strip()
            desc = self.inc_desc.text.strip()
            if amt <= 0: raise ValueError()

            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            cursor.execute("INSERT INTO income (amount, date, description) VALUES (?, ?, ?)", (amt, dt, desc))
            conn.commit()
            conn.close()

            self.show_popup("Success", "Income added successfully!")
            self.refresh_dashboard()
        except ValueError:
            self.show_popup("Invalid Input", "Please enter a valid numeric income amount.")

    # --- HISTORY & FILTER SCREEN ---
    def show_history_screen(self):
        self.clear_view()
        self.main_container.add_widget(Label(text="[b]Transaction History & Search[/b]", markup=True, font_size=17, color=(0.12, 0.20, 0.18, 1), size_hint_y=None, height=35))

        search_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=45, spacing=6)
        self.search_input = TextInput(hint_text="Search category or note...", multiline=False)
        search_btn = Button(text="Search", size_hint_x=None, width=85, background_normal='', background_color=(0.15, 0.42, 0.65, 1), bold=True)
        search_btn.bind(on_press=lambda x: self.load_filtered_history(self.search_input.text.strip()))
        search_box.add_widget(self.search_input)
        search_box.add_widget(search_btn)
        self.main_container.add_widget(search_box)

        self.history_list_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=6)
        self.history_list_box.bind(minimum_height=self.history_list_box.setter('height'))
        
        scroll_hist = ScrollView(size_hint=(1, None), height=320)
        scroll_hist.add_widget(self.history_list_box)
        self.main_container.add_widget(scroll_hist)

        self.load_filtered_history("")

        back_btn = Button(text="Back to Dashboard", size_hint_y=None, height=45, background_normal='', background_color=(0.3, 0.38, 0.42, 1), bold=True)
        back_btn.bind(on_press=lambda x: self.refresh_dashboard())
        self.main_container.add_widget(back_btn)

    def load_filtered_history(self, query):
        self.history_list_box.clear_widgets()
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()

        if query:
            cursor.execute("SELECT id, amount, category, date, description FROM expenses WHERE category LIKE ? OR description LIKE ? ORDER BY id DESC", 
                           (f"%{query}%", f"%{query}%"))
        else:
            cursor.execute("SELECT id, amount, category, date, description FROM expenses ORDER BY id DESC")
        
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            self.history_list_box.add_widget(Label(text="No matching transactions found.", color=(0.4, 0.4, 0.4, 1), size_hint_y=None, height=35))
        else:
            for row in rows:
                eid, amt, cat, dt, desc = row
                row_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=42, spacing=4)
                row_layout.add_widget(Label(text=f"[b]{dt}[/b] | {cat} | ₹{amt:,.2f}", markup=True, color=(0.2, 0.2, 0.2, 1), font_size=12))
                
                edit_btn = Button(text="Edit", size_hint_x=None, width=50, background_normal='', background_color=(0.2, 0.5, 0.8, 1), bold=True)
                edit_btn.bind(on_press=lambda x, r=row: self.show_edit_screen(r))
                row_layout.add_widget(edit_btn)

                del_btn = Button(text="Del", size_hint_x=None, width=50, background_normal='', background_color=(0.8, 0.2, 0.2, 1), bold=True)
                del_btn.bind(on_press=lambda x, i=eid: self.confirm_delete(i))
                row_layout.add_widget(del_btn)

                self.history_list_box.add_widget(row_layout)

    def show_edit_screen(self, row):
        eid, amt, cat, dt, desc = row
        self.clear_view()
        self.main_container.add_widget(Label(text="[b]Edit Transaction[/b]", markup=True, font_size=17, color=(0.12, 0.20, 0.18, 1), size_hint_y=None, height=35))

        self.edit_amt = TextInput(text=str(amt), hint_text="Amount", multiline=False, input_filter='float', size_hint_y=None, height=45)
        self.edit_cat = Spinner(text=cat, values=('Food', 'Travel', 'Shopping', 'Bills', 'Entertainment', 'Health', 'Education', 'Other'), size_hint_y=None, height=45)
        self.edit_date = TextInput(text=dt, hint_text="Date (YYYY-MM-DD)", multiline=False, size_hint_y=None, height=45)
        self.edit_desc = TextInput(text=desc, hint_text="Note", multiline=False, size_hint_y=None, height=45)

        self.main_container.add_widget(Label(text="Amount:", color=(0.15, 0.25, 0.22, 1), bold=True, size_hint_y=None, height=22))
        self.main_container.add_widget(self.edit_amt)
        self.main_container.add_widget(Label(text="Category:", color=(0.15, 0.25, 0.22, 1), bold=True, size_hint_y=None, height=22))
        self.main_container.add_widget(self.edit_cat)
        self.main_container.add_widget(Label(text="Date:", color=(0.15, 0.25, 0.22, 1), bold=True, size_hint_y=None, height=22))
        self.main_container.add_widget(self.edit_date)
        self.main_container.add_widget(Label(text="Note:", color=(0.15, 0.25, 0.22, 1), bold=True, size_hint_y=None, height=22))
        self.main_container.add_widget(self.edit_desc)

        update_btn = Button(text="Update Transaction", size_hint_y=None, height=48, background_normal='', background_color=(0.15, 0.5, 0.8, 1), bold=True)
        update_btn.bind(on_press=lambda x: self.save_edited_expense(eid))
        self.main_container.add_widget(update_btn)

        back_btn = Button(text="Cancel", size_hint_y=None, height=45, background_normal='', background_color=(0.3, 0.38, 0.42, 1), bold=True)
        back_btn.bind(on_press=lambda x: self.show_history_screen())
        self.main_container.add_widget(back_btn)

    def save_edited_expense(self, eid):
        try:
            amt = float(self.edit_amt.text.strip())
            cat = self.edit_cat.text
            dt = self.edit_date.text.strip()
            desc = self.edit_desc.text.strip()
            if amt <= 0: raise ValueError()

            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            cursor.execute("UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ?", (amt, cat, dt, desc, eid))
            conn.commit()
            conn.close()

            self.show_popup("Success", "Transaction updated successfully!")
            self.show_history_screen()
        except ValueError:
            self.show_popup("Invalid Input", "Please enter valid details.")

    # --- DELETE CONFIRMATION POPUP (Clean UI Theme) ---
   # --- MODERN DELETE CONFIRMATION POPUP WITH TRANSACTION DETAILS ---
    def confirm_delete(self, expense_id):
        # Database se specific transaction ki details fetch karein
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT amount, category, date, description FROM expenses WHERE id = ?", (expense_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return
        amt, cat, dt, desc = row

        # Date formatting (e.g., 2026-09-20 -> 20 September 2026)
        try:
            parsed_date = datetime.strptime(dt, "%Y-%m-%d")
            formatted_date = parsed_date.strftime("%d %B %Y")
        except Exception:
            formatted_date = dt

        # Modern white container with smooth rounded corners
        content = RoundedBox(bg_color=(1, 1, 1, 1), radius=20, orientation='vertical', padding=18, spacing=12)
        
        # Header / Title
        content.add_widget(Label(
            text="[b]Delete Transaction?[/b]", 
            markup=True, 
            color=(0.12, 0.15, 0.18, 1), 
            font_size=16,
            size_hint_y=None, height=26,
            halign='center'
        ))
        
        # Subtitle
        content.add_widget(Label(
            text="Are you sure you want to delete this transaction?", 
            markup=True, 
            color=(0.45, 0.50, 0.55, 1), 
            font_size=12,
            size_hint_y=None, height=20,
            halign='center'
        ))

        # Transaction Details Highlight Box
        details_box = RoundedBox(bg_color=(0.95, 0.96, 0.98, 1), radius=10, orientation='vertical', size_hint_y=None, height=52, padding=8, spacing=2)
        details_box.add_widget(Label(
            text=f"[b]{cat}[/b] • [color=#EF4444]₹{amt:,.2f}[/color]", 
            markup=True, 
            color=(0.2, 0.2, 0.2, 1), 
            font_size=13,
            halign='center'
        ))
        desc_text = f" • {desc}" if desc else ""
        details_box.add_widget(Label(
            text=f"{formatted_date}{desc_text}", 
            markup=True, 
            color=(0.55, 0.60, 0.65, 1), 
            font_size=11,
            halign='center'
        ))
        content.add_widget(details_box)
        
        # Action Buttons Layout (Cancel first, then Delete)
        btn_box = BoxLayout(spacing=12, size_hint_y=None, height=44)
        
        # Cancel Button (#64748B soft slate)
        no_btn = Button(
            text="Cancel", 
            background_normal='', 
            background_color=(0.39, 0.45, 0.55, 1), 
            color=(1, 1, 1, 1),
            bold=True,
            font_size=13
        )
        
        # Yes, Delete Button (#EF4444 red)
        yes_btn = Button(
            text="Yes, Delete", 
            background_normal='', 
            background_color=(0.937, 0.266, 0.266, 1), 
            color=(1, 1, 1, 1),
            bold=True,
            font_size=13
        )
        
        popup = Popup(
            title="", 
            separator_height=0,  # Removes default title bar for a clean card look
            content=content, 
            size_hint=(0.88, 0.42),
            auto_dismiss=False
        )
        
        def execute_delete(instance):
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            conn.commit()
            conn.close()
            popup.dismiss()
            self.load_filtered_history("")

        yes_btn.bind(on_press=execute_delete)
        no_btn.bind(on_press=popup.dismiss)
        
        btn_box.add_widget(no_btn)
        btn_box.add_widget(yes_btn)
        content.add_widget(btn_box)
        popup.open()

    # --- ANALYTICS SCREEN WITH PAST MONTH FILTER ---
    def show_analytics_screen(self):
        self.clear_view()
        self.main_container.add_widget(Label(text="[b]Past & Current Month Analytics[/b]", markup=True, font_size=16, color=(0.12, 0.20, 0.18, 1), size_hint_y=None, height=35))

        now = datetime.now()
        month_options = []
        for i in range(6):
            d = now - timedelta(days=i*30)
            month_options.append(d.strftime("%Y-%m"))
        
        selector_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=45, spacing=10)
        selector_box.add_widget(Label(text="Select Month:", color=(0.15, 0.25, 0.22, 1), bold=True, size_hint_x=None, width=110))
        
        self.month_spinner = Spinner(text=now.strftime("%Y-%m"), values=tuple(month_options))
        selector_box.add_widget(self.month_spinner)
        self.main_container.add_widget(selector_box)

        filter_btn = Button(text="Load Analytics for Selected Month", size_hint_y=None, height=42, background_normal='', background_color=(0.2, 0.45, 0.65, 1), bold=True)
        filter_btn.bind(on_press=lambda x: self.load_analytics_data(self.month_spinner.text))
        self.main_container.add_widget(filter_btn)

        self.analytics_results_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=8)
        self.analytics_results_box.bind(minimum_height=self.analytics_results_box.setter('height'))

        scroll_ana = ScrollView(size_hint=(1, None), height=270)
        scroll_ana.add_widget(self.analytics_results_box)
        self.main_container.add_widget(scroll_ana)

        self.load_analytics_data(now.strftime("%Y-%m"))

        back_btn = Button(text="Back to Dashboard", size_hint_y=None, height=45, background_normal='', background_color=(0.3, 0.38, 0.42, 1), bold=True)
        back_btn.bind(on_press=lambda x: self.refresh_dashboard())
        self.main_container.add_widget(back_btn)

    def load_analytics_data(self, month_str):
      self.analytics_results_box.clear_widgets()
      conn = sqlite3.connect(get_db_path())
      cursor = conn.cursor()

      # Flexible search using strftime or LIKE to match YYYY-MM
      cursor.execute(
          'SELECT SUM(amount) FROM expenses WHERE date LIKE ? OR substr(date,'
          ' 1, 7) = ?',
          (f'%{month_str}%', month_str),
      )
      exp_res = cursor.fetchone()[0]
      total_exp = exp_res if exp_res else 0.0

      cursor.execute(
          'SELECT SUM(amount) FROM income WHERE date LIKE ? OR substr(date, 1,'
          ' 7) = ?',
          (f'%{month_str}%', month_str),
      )
      inc_res = cursor.fetchone()[0]
      total_inc = inc_res if inc_res else 0.0

      cursor.execute(
          'SELECT category, SUM(amount) as total FROM expenses WHERE date LIKE ?'
          ' OR substr(date, 1, 7) = ? GROUP BY category ORDER BY total DESC',
          (f'%{month_str}%', month_str),
      )
      cat_rows = cursor.fetchall()
      conn.close()

      self.analytics_results_box.add_widget(
          Label(
              text=(
                  f'[b]Summary for {month_str}[/b]\nIncome: ₹{total_inc:,.2f} |'
                  f' Expense: ₹{total_exp:,.2f}'
              ),
              markup=True,
              color=(0.15, 0.25, 0.22, 1),
              font_size=13,
              size_hint_y=None,
              height=45,
          )
      )
      self.analytics_results_box.add_widget(
          Label(
              text='[b]Category Breakdown:[/b]',
              markup=True,
              color=(0.12, 0.20, 0.18, 1),
              font_size=12,
              size_hint_y=None,
              height=25,
          )
      )

      if not cat_rows:
        self.analytics_results_box.add_widget(
            Label(
                text=f'No expenses found for {month_str}.',
                color=(0.4, 0.4, 0.4, 1),
                size_hint_y=None,
                height=30,
            )
        )
      else:
        for c, t in cat_rows:
          card = RoundedBox(
              bg_color=(1, 1, 1, 1),
              radius=6,
              size_hint_y=None,
              height=36,
              padding=6,
          )
          card.add_widget(
              Label(
                  text=f'{c}: [color=#EF4444]₹{t:,.2f}[/color]',
                  markup=True,
                  color=(0.2, 0.2, 0.2, 1),
                  font_size=11,
              )
          )
          self.analytics_results_box.add_widget(card)

    # --- SET BUDGET SCREEN ---
    def show_budget_screen(self):
        self.clear_view()
        self.main_container.add_widget(Label(text="[b]Manage Monthly Budget[/b]", markup=True, font_size=17, color=(0.12, 0.20, 0.18, 1), size_hint_y=None, height=35))

        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key='monthly_budget'")
        res = cursor.fetchone()
        current_budget = res[0] if res else 25000.0
        conn.close()

        self.budget_input = TextInput(text=str(current_budget), hint_text="Enter new monthly budget", multiline=False, input_filter='float', size_hint_y=None, height=45)
        
        self.main_container.add_widget(Label(text="Set Monthly Budget Limit (₹):", color=(0.15, 0.25, 0.22, 1), bold=True, size_hint_y=None, height=25))
        self.main_container.add_widget(self.budget_input)

        save_btn = Button(text="Save Budget", size_hint_y=None, height=48, background_normal='', background_color=(0.75, 0.42, 0.1, 1), bold=True)
        save_btn.bind(on_press=self.save_budget_db)
        self.main_container.add_widget(save_btn)

        back_btn = Button(text="Back to Dashboard", size_hint_y=None, height=45, background_normal='', background_color=(0.3, 0.38, 0.42, 1), bold=True)
        back_btn.bind(on_press=lambda x: self.refresh_dashboard())
        self.main_container.add_widget(back_btn)

    def save_budget_db(self, instance):
        try:
            new_budget = float(self.budget_input.text.strip())
            if new_budget < 0: raise ValueError()

            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            cursor.execute("UPDATE settings SET value = ? WHERE key = 'monthly_budget'", (new_budget,))
            conn.commit()
            conn.close()

            self.show_popup("Success", "Monthly budget updated successfully!")
            self.refresh_dashboard()
        except ValueError:
            self.show_popup("Invalid Input", "Please enter a valid numeric budget amount.")

    # --- SETTINGS SCREEN (Backup / Export Data) ---
    def show_settings_screen(self):
        self.clear_view()
        self.main_container.add_widget(Label(text="[b]Settings & Data Export[/b]", markup=True, font_size=17, color=(0.12, 0.20, 0.18, 1), size_hint_y=None, height=35))

        self.main_container.add_widget(Label(text="Export your expense records to a CSV file for backup.", color=(0.3, 0.3, 0.3, 1), font_size=13, size_hint_y=None, height=30))

        export_btn = Button(text="Export Expenses to CSV", size_hint_y=None, height=48, background_normal='', background_color=(0.2, 0.5, 0.4, 1), bold=True)
        export_btn.bind(on_press=self.export_csv)
        self.main_container.add_widget(export_btn)

        back_btn = Button(text="Back to Dashboard", size_hint_y=None, height=45, background_normal='', background_color=(0.3, 0.38, 0.42, 1), bold=True)
        back_btn.bind(on_press=lambda x: self.refresh_dashboard())
        self.main_container.add_widget(back_btn)

    def export_csv(self, instance):
        try:
            file_path = os.path.join(get_db_path().replace("expenses.db", ""), "expenses_backup.csv")
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            cursor.execute("SELECT id, amount, category, date, description FROM expenses")
            rows = cursor.fetchall()
            conn.close()

            with open(file_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Amount", "Category", "Date", "Description"])
                writer.writerows(rows)

            self.show_popup("Export Successful", f"Backup saved successfully at:\n{file_path}")
        except Exception as e:
            self.show_popup("Export Failed", f"Error exporting data: {str(e)}")

# --- APP RUNNER ---
class ExpenseTrackerApp(App):
    def build(self):
        init_db()
        return ExpenseTrackerRoot()

if __name__ == '__main__':
    ExpenseTrackerApp().run()