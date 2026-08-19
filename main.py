import os
import sqlite3
from datetime import date
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Soft light background
Window.clearcolor = (0.97, 0.97, 0.98, 1)

class ExpenseTracker(MDApp):

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Purple"
        
        if os.path.exists("app_icon.png"):
            self.icon = "app_icon.png"

        self.create_database()
        
        Window.bind(on_keyboard=self.on_back_button)

        self.current_screen_name = "home"
        self.screen = MDScreen(md_bg_color=(0.97, 0.97, 0.98, 1))
        self.show_home()
        return self.screen

    def on_back_button(self, window, key, *args):
        if key == 27:
            if self.current_screen_name != "home":
                self.show_home()
                return True
        return False

    def create_top_bar(self, title_text, show_back=True):
        top_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height="48dp",
            padding=["4dp", "2dp", "4dp", "2dp"],
            spacing="4dp",
            md_bg_color=(0.92, 0.92, 0.94, 1)
        )
        if show_back:
            back_btn = MDIconButton(
                icon="arrow-left",
                pos_hint={"center_y": 0.5}
            )
            back_btn.bind(on_release=lambda x: self.show_home())
            top_bar.add_widget(back_btn)
        else:
            spacer = MDBoxLayout(size_hint_x=None, width="40dp")
            top_bar.add_widget(spacer)

        title_lbl = MDLabel(
            text=title_text,
            bold=True,
            halign="center",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.1, 0.1, 0.1, 1)
        )
        top_bar.add_widget(title_lbl)
        
        right_spacer = MDBoxLayout(size_hint_x=None, width="40dp")
        top_bar.add_widget(right_spacer)

        return top_bar

    def create_mobile_card(self):
        scroll = ScrollView(size_hint=(1, 1))
        container = MDBoxLayout(
            orientation="vertical",
            padding=["16dp", "12dp", "16dp", "16dp"],
            spacing="14dp",
            size_hint_y=None,
            md_bg_color=(0.97, 0.97, 0.98, 1)
        )
        container.bind(minimum_height=container.setter('height'))
        scroll.add_widget(container)
        return scroll, container

    # ---------------- DATABASE ----------------
    def create_database(self):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.db")
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value REAL
            )
        """)
        self.cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('monthly_budget', 30000.0)")
        self.connection.commit()

    def get_budget(self):
        self.cursor.execute("SELECT value FROM settings WHERE key='monthly_budget'")
        res = self.cursor.fetchone()
        return res[0] if res else 30000.0

    def set_budget(self, amount):
        self.cursor.execute("UPDATE settings SET value = ? WHERE key='monthly_budget'", (amount,))
        self.connection.commit()

    def get_total_expense(self):
        self.cursor.execute("SELECT SUM(amount) FROM expenses")
        res = self.cursor.fetchone()[0]
        return res if res else 0.0

    # ---------------- HOME SCREEN ----------------
    def show_home(self):
        self.current_screen_name = "home"
        self.screen.clear_widgets()

        main_layout = MDBoxLayout(orientation="vertical", md_bg_color=(0.97, 0.97, 0.98, 1))
        top_bar = self.create_top_bar("Expense Tracker", show_back=False)
        scroll, container = self.create_mobile_card()

        budget = self.get_budget()
        subtitle = MDLabel(
            text=f"Monthly Budget: ₹{budget:,.2f}",
            halign="center",
            font_style="Body",
            role="medium",
            theme_text_color="Custom",
            text_color=(0.2, 0.2, 0.2, 1),
            size_hint_y=None,
            height="20dp"
        )
        container.add_widget(subtitle)

        # Overview Card
        total_spent = self.get_total_expense()
        percent_used = (total_spent / budget * 100) if budget > 0 else 0.0

        spent_card = MDCard(
            orientation="vertical",
            padding="12dp",
            spacing="6dp",
            style="elevated",
            size_hint=(1, None),
            height="105dp",
            radius=[12, 12, 12, 12],
            md_bg_color=(1, 1, 1, 1)
        )
        spent_title = MDLabel(
            text="Total Spent:",
            font_style="Title",
            role="small",
            size_hint_y=None,
            height="16dp",
            theme_text_color="Custom",
            text_color=(0.1, 0.1, 0.1, 1)
        )
        spent_amount = MDLabel(
            text=f"₹{total_spent:,.2f}",
            bold=True,
            font_style="Headline",
            role="small",
            size_hint_y=None,
            height="28dp",
            theme_text_color="Custom",
            text_color=(0.4, 0.1, 0.5, 1)
        )
        
        progress = ProgressBar(max=100, value=min(percent_used, 100), size_hint_y=None, height="6dp")
        
        status_text = f"Used: {percent_used:.1f}%"
        if percent_used >= 80:
            status_text += " | Near Limit"
        status_label = MDLabel(
            text=status_text,
            font_style="Body",
            role="small",
            theme_text_color="Custom",
            text_color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None,
            height="14dp"
        )

        spent_card.add_widget(spent_title)
        spent_card.add_widget(spent_amount)
        spent_card.add_widget(progress)
        spent_card.add_widget(status_label)

        # Quick Actions
        nav_layout = MDBoxLayout(orientation="horizontal", spacing="6dp", size_hint=(1, None), height="40dp")
        
        analytics_btn = MDButton(MDButtonText(text="Analytics"), style="filled", size_hint_x=0.33)
        analytics_btn.bind(on_release=lambda x: self.show_analytics())
        
        history_btn = MDButton(MDButtonText(text="History"), style="filled", size_hint_x=0.33)
        history_btn.bind(on_release=lambda x: self.show_history())
        
        budget_btn = MDButton(MDButtonText(text="Budget"), style="filled", size_hint_x=0.33)
        budget_btn.bind(on_release=lambda x: self.show_update_budget())

        nav_layout.add_widget(analytics_btn)
        nav_layout.add_widget(history_btn)
        nav_layout.add_widget(budget_btn)

        # Recent Items
        recent_title = MDLabel(
            text="Recent Transactions",
            font_style="Title",
            role="small",
            size_hint_y=None,
            height="24dp",
            theme_text_color="Custom",
            text_color=(0.1, 0.1, 0.1, 1)
        )
        
        transactions_layout = MDBoxLayout(orientation="vertical", spacing="6dp", size_hint_y=None)
        transactions_layout.bind(minimum_height=transactions_layout.setter('height'))

        self.cursor.execute("SELECT category, amount, date, description FROM expenses ORDER BY id DESC LIMIT 3")
        recent_items = self.cursor.fetchall()

        if not recent_items:
            empty_lbl = MDLabel(
                text="No recent transactions.",
                halign="center",
                theme_text_color="Custom",
                text_color=(0.4, 0.4, 0.4, 1),
                size_hint_y=None,
                height="32dp"
            )
            transactions_layout.add_widget(empty_lbl)
        else:
            for cat, amt, dt, desc in recent_items:
                item_card = MDCard(
                    orientation="vertical",
                    padding="10dp",
                    style="elevated",
                    size_hint=(1, None),
                    height="54dp",
                    radius=[10, 10, 10, 10],
                    md_bg_color=(1, 1, 1, 1)
                )
                lbl1 = MDLabel(text=f"{cat} - ₹{amt:,.2f}", bold=True, font_style="Body", role="medium", theme_text_color="Custom", text_color=(0.1, 0.1, 0.1, 1))
                lbl2 = MDLabel(text=f"{dt} | {desc if desc else 'N/A'}", font_style="Body", role="small", theme_text_color="Custom", text_color=(0.3, 0.3, 0.3, 1))
                item_card.add_widget(lbl1)
                item_card.add_widget(lbl2)
                transactions_layout.add_widget(item_card)

        add_btn_layout = MDBoxLayout(orientation="horizontal", size_hint=(1, None), height="50dp", padding=[0, "4dp", 0, 0])
        add_btn = MDButton(MDButtonText(text="+ Add Expense", font_style="Title", role="medium"), style="filled", pos_hint={"center_x": 0.5}, size_hint_x=1)
        add_btn.bind(on_release=lambda x: self.show_add_expense())
        add_btn_layout.add_widget(add_btn)

        container.add_widget(spent_card)
        container.add_widget(nav_layout)
        container.add_widget(recent_title)
        container.add_widget(transactions_layout)
        container.add_widget(add_btn_layout)

        main_layout.add_widget(top_bar)
        main_layout.add_widget(scroll)

        self.screen.add_widget(main_layout)

    # ---------------- HISTORY SCREEN ----------------
    def show_history(self):
        self.current_screen_name = "history"
        self.screen.clear_widgets()

        main_layout = MDBoxLayout(orientation="vertical", md_bg_color=(0.97, 0.97, 0.98, 1))
        top_bar = self.create_top_bar("Transaction History", show_back=True)
        scroll, container = self.create_mobile_card()

        self.cursor.execute("SELECT id, category, amount, date, description FROM expenses ORDER BY id DESC")
        records = self.cursor.fetchall()

        if not records:
            empty_lbl = MDLabel(
                text="No transactions found.", 
                halign="center", 
                size_hint_y=None, 
                height="50dp", 
                theme_text_color="Custom", 
                text_color=(0.4, 0.4, 0.4, 1)
            )
            container.add_widget(empty_lbl)
        else:
            for eid, cat, amt, dt, desc in records:
                card = MDCard(
                    orientation="vertical",
                    padding=["12dp", "10dp", "12dp", "10dp"],
                    spacing="6dp",
                    style="elevated",
                    size_hint=(1, None),
                    height="110dp",
                    radius=[12, 12, 12, 12],
                    md_bg_color=(1, 1, 1, 1)
                )
                
                lbl1 = MDLabel(
                    text=f"{cat} - ₹{amt:,.2f}", 
                    bold=True, 
                    size_hint_y=None, 
                    height="22dp", 
                    theme_text_color="Custom", 
                    text_color=(0.1, 0.1, 0.1, 1)
                )
                
                lbl2 = MDLabel(
                    text=f"Date: {dt} | Note: {desc if desc else 'N/A'}", 
                    font_style="Body", 
                    role="small", 
                    theme_text_color="Custom", 
                    text_color=(0.35, 0.35, 0.35, 1), 
                    size_hint_y=None, 
                    height="18dp"
                )
                
                btn_box = MDBoxLayout(
                    orientation="horizontal", 
                    spacing="10dp", 
                    size_hint=(1, None), 
                    height="32dp"
                )
                
                edit_btn = MDButton(MDButtonText(text="Edit"), style="outlined", size_hint_x=0.5)
                edit_btn.bind(on_release=lambda x, id_val=eid: self.edit_expense(id_val))

                delete_btn = MDButton(MDButtonText(text="Delete"), style="outlined", size_hint_x=0.5)
                delete_btn.bind(on_release=lambda x, id_val=eid: self.delete_expense(id_val))

                btn_box.add_widget(edit_btn)
                btn_box.add_widget(delete_btn)

                card.add_widget(lbl1)
                card.add_widget(lbl2)
                card.add_widget(btn_box)
                container.add_widget(card)

        main_layout.add_widget(top_bar)
        main_layout.add_widget(scroll)

        self.screen.add_widget(main_layout)

    # ---------------- ANALYTICS ----------------
    def show_analytics(self):
        self.current_screen_name = "analytics"
        self.screen.clear_widgets()

        main_layout = MDBoxLayout(orientation="vertical", md_bg_color=(0.97, 0.97, 0.98, 1))
        top_bar = self.create_top_bar("Spending Analytics", show_back=True)
        scroll, container = self.create_mobile_card()

        self.cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
        data = self.cursor.fetchall()

        if data:
            categories = [row[0] for row in data]
            amounts = [row[1] for row in data]

            fig, ax = plt.subplots(figsize=(4, 4))
            fig.patch.set_facecolor('#F8F9FA')
            ax.set_facecolor('#F8F9FA')
            
            wedges, texts, autotexts = ax.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=140)
            for text in texts + autotexts:
                text.set_color('#1C1B1F')

            plt.tight_layout()
            
            chart_path = "temp_chart.png"
            plt.savefig(chart_path, transparent=True)
            plt.close()

            chart_img = Image(source=chart_path, size_hint=(1, None), height="280dp")
            container.add_widget(chart_img)
        else:
            no_data = MDLabel(text="No data available for analytics.", halign="center", size_hint_y=None, height="80dp", theme_text_color="Custom", text_color=(0.4, 0.4, 0.4, 1))
            container.add_widget(no_data)

        main_layout.add_widget(top_bar)
        main_layout.add_widget(scroll)

        self.screen.add_widget(main_layout)

    # ---------------- UPDATE BUDGET ----------------
    def show_update_budget(self):
        self.current_screen_name = "budget"
        self.screen.clear_widgets()

        main_layout = MDBoxLayout(orientation="vertical", md_bg_color=(0.97, 0.97, 0.98, 1))
        top_bar = self.create_top_bar("Update Budget", show_back=True)
        scroll, container = self.create_mobile_card()

        self.budget_input = MDTextField(
            MDTextFieldHintText(text="New Budget Limit (₹)"),
            mode="outlined",
            size_hint=(1, None),
            height="56dp"
        )

        btn_box = MDBoxLayout(orientation="horizontal", spacing="12dp", size_hint=(1, None), height="48dp")
        
        save_btn = MDButton(MDButtonText(text="Save Budget"), style="filled", size_hint_x=0.5)
        save_btn.bind(on_release=lambda x: self.save_new_budget())

        back_btn = MDButton(MDButtonText(text="Cancel"), style="outlined", size_hint_x=0.5)
        back_btn.bind(on_release=lambda x: self.show_home())

        btn_box.add_widget(save_btn)
        btn_box.add_widget(back_btn)

        container.add_widget(self.budget_input)
        container.add_widget(btn_box)

        main_layout.add_widget(top_bar)
        main_layout.add_widget(scroll)

        self.screen.add_widget(main_layout)

    def save_new_budget(self):
        val = self.budget_input.text.strip()
        if val:
            self.set_budget(float(val))
            self.show_home()

    # ---------------- ADD EXPENSE (NO WARNINGS) ----------------
    def show_add_expense(self):
        self.current_screen_name = "add_expense"
        self.screen.clear_widgets()

        main_layout = MDBoxLayout(orientation="vertical", md_bg_color=(0.97, 0.97, 0.98, 1))
        top_bar = self.create_top_bar("Add New Expense", show_back=True)
        scroll, container = self.create_mobile_card()

        self.amt_in = MDTextField(
            MDTextFieldHintText(text="Amount (₹)"),
            mode="outlined",
            size_hint=(1, None),
            height="56dp"
        )

        self.cat_in = MDTextField(
            MDTextFieldHintText(text="Select Category"),
            mode="outlined",
            readonly=True,
            size_hint=(1, None),
            height="56dp"
        )

        categories = ["Food", "Travel", "Shopping", "Bills", "Education", "Entertainment", "Health", "Other"]
        menu_items = [
            {
                "text": cat,
                "on_release": lambda x=cat: self.set_category_add(x),
            } for cat in categories
        ]
        
        # Removed width_mult to fix KivyMD warning
        self.cat_menu = MDDropdownMenu(
            caller=self.cat_in,
            items=menu_items,
            position="bottom"
        )
        self.cat_in.bind(focus=lambda instance, focused: self.cat_menu.open() if focused else None)

        self.desc_in = MDTextField(
            MDTextFieldHintText(text="Note / Description (Optional)"),
            mode="outlined",
            size_hint=(1, None),
            height="56dp"
        )

        save_btn = MDButton(
            MDButtonText(text="Save Expense", font_style="Title", role="medium"), 
            style="filled", 
            pos_hint={"center_x": 0.5}, 
            size_hint=(1, None),
            height="48dp"
        )
        save_btn.bind(on_release=lambda x: self.save_expense())

        container.add_widget(self.amt_in)
        container.add_widget(self.cat_in)
        container.add_widget(self.desc_in)
        container.add_widget(MDBoxLayout(size_hint_y=None, height="10dp"))
        container.add_widget(save_btn)

        main_layout.add_widget(top_bar)
        main_layout.add_widget(scroll)

        self.screen.add_widget(main_layout)

    def set_category_add(self, text_item):
        self.cat_in.text = text_item
        self.cat_menu.dismiss()

    def save_expense(self):
        amt = self.amt_in.text.strip()
        cat = self.cat_in.text.strip()
        desc = self.desc_in.text.strip()

        if amt and cat and cat != "Select Category":
            today = date.today().strftime("%Y-%m-%d")
            self.cursor.execute("INSERT INTO expenses (amount, category, date, description) VALUES (?, ?, ?, ?)",
                                (float(amt), cat, today, desc))
            self.connection.commit()
            self.show_home()

    # ---------------- EDIT EXPENSE (NO WARNINGS) ----------------
    def edit_expense(self, expense_id):
        self.current_screen_name = "edit_expense"
        self.cursor.execute("SELECT amount, category, description FROM expenses WHERE id = ?", (expense_id,))
        record = self.cursor.fetchone()
        if not record:
            return

        self.screen.clear_widgets()

        main_layout = MDBoxLayout(orientation="vertical", md_bg_color=(0.97, 0.97, 0.98, 1))
        top_bar = self.create_top_bar("Edit Expense", show_back=True)
        scroll, container = self.create_mobile_card()

        self.edit_amt_in = MDTextField(
            MDTextFieldHintText(text="Amount (₹)"),
            mode="outlined",
            text=str(record[0]),
            size_hint=(1, None),
            height="56dp"
        )

        self.edit_cat_in = MDTextField(
            MDTextFieldHintText(text="Category"),
            mode="outlined",
            text=record[1],
            readonly=True,
            size_hint=(1, None),
            height="56dp"
        )

        categories = ["Food", "Travel", "Shopping", "Bills", "Education", "Entertainment", "Health", "Other"]
        menu_items = [
            {
                "text": cat,
                "on_release": lambda x=cat: self.set_category_edit(x),
            } for cat in categories
        ]
        self.edit_cat_menu = MDDropdownMenu(
            caller=self.edit_cat_in,
            items=menu_items,
            position="bottom"
        )
        self.edit_cat_in.bind(focus=lambda instance, focused: self.edit_cat_menu.open() if focused else None)

        self.edit_desc_in = MDTextField(
            MDTextFieldHintText(text="Note / Description"),
            mode="outlined",
            text=record[2] if record[2] else "",
            size_hint=(1, None),
            height="56dp"
        )

        update_btn = MDButton(
            MDButtonText(text="Update Expense", font_style="Title", role="medium"), 
            style="filled", 
            pos_hint={"center_x": 0.5}, 
            size_hint=(1, None),
            height="48dp"
        )
        update_btn.bind(on_release=lambda x: self.update_expense(expense_id, self.edit_amt_in.text, self.edit_cat_in.text, self.edit_desc_in.text))

        container.add_widget(self.edit_amt_in)
        container.add_widget(self.edit_cat_in)
        container.add_widget(self.edit_desc_in)
        container.add_widget(MDBoxLayout(size_hint_y=None, height="10dp"))
        container.add_widget(update_btn)

        main_layout.add_widget(top_bar)
        main_layout.add_widget(scroll)

        self.screen.add_widget(main_layout)

    def set_category_edit(self, text_item):
        self.edit_cat_in.text = text_item
        self.edit_cat_menu.dismiss()

    def update_expense(self, expense_id, amount, category, description):
        if amount:
            self.cursor.execute("""
                UPDATE expenses
                SET amount = ?, category = ?, description = ?
                WHERE id = ?
            """, (float(amount), category, description, expense_id))
            self.connection.commit()
            self.show_history()

    def delete_expense(self, expense_id):
        self.cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        self.connection.commit()
        self.show_history()

if __name__ == "__main__":
    ExpenseTracker().run()