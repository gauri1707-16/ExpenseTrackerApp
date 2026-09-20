# (str) Title of your application
title = Expense Tracker

# (str) Package name
package.name = expensetracker

# (str) Package domain (needed for android packaging)
package.domain = org.expense

# (list) Source files to include (let it include python files, images, db)
source.include_exts = py,png,jpg,kv,atlas

# (list) Application requirements
# Yahan sqlite3 aur matplotlib/pillow ka hona zaroori hai agar app mein charts aur database hain
requirements = python3,kivy,kivymd,sqlite3,matplotlib,pillow

# (str) Supported orientations
orientation = portrait