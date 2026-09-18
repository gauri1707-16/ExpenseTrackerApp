[app]
title = Expense Tracker
package.name = expensetracker
package.domain = org.finance
source.include_exts = py,png,jpg,kv,atlas
source.dir = .
version = 1.1
requirements = python3,kivy,kivymd,sqlite3,matplotlib,numpy,pillow
orientation = portrait
fullscreen = 0
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21

[buildozer]
log_level = 2
warn_root = 1