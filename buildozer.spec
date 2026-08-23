[app]

# (str) Title of your application
title = Expense Tracker App

# (str) Source directory where your application resides
source.dir = .

# (str) Package name
package.name = expensetracker

# (str) Package domain (needed for android packaging)
package.domain = org.gauri

# (list) Source files to include (let it empty to include all files)
source.include_exts = py,png,jpg,kv,atlas,db

# (list) Source files to exclude (let it empty to exclude nothing)
source.exclude_exts = spec

# (list) List of inclusion/exclusion patterns
source.exclude_patterns = license,images/*.jpg

# (str) Application versioning (method 1)
version = 1.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy

# (list) Permissions
#android.permissions = INTERNET

# (str) Supported orientations
orientation = portrait

# (list) List of service to declare
#services = NAME:ENTRYPOINT_TO_PY,NAME2:ENTRYPOINT2_TO_PY

#
# OSX Specific
#

#
# Android specific
#

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support
android.min_api = 21

# (int) Android SDK version to use
android.sdk = 33

# (str) Android NDK version to use
# android.ndk = 25b

# (bool) Use Android sdk snapshot version
# android.sdk_snapshot = False

# (str) Android entry point interface
# android.entrypoint = org.renpy.android.PythonActivity

# (bool) Skip byte-compiling python files for android
# android.skip_byte_compile = False

# (str) The format used to package the app for store (apk or aab)
android.format = apk

# (bool) Automatically accept android SDK license agreement
android.accept_sdk_license = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_root = 1

# (str) Path to build artifact, storage for the APK
bin_dir = ./bin

# (str) Path to build directory (default to .buildozer)
#build_path = .build_path

# (str) Directory to store shared state across builds
# android.allow_sdk_license = True
