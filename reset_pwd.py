import hashlib
import sqlite3

# Apni database file se connect karein
conn = sqlite3.connect("expenses.db")
cursor = conn.cursor()

# Apna naya email aur naya secure password yahan daal dein (with special character, e.g., Gauri@123)
new_email = "gg647579@gmail.com"
new_password = "Gauri@123"

pwd_hash = hashlib.sha256(new_password.encode()).hexdigest()

# Database mein password update karna
cursor.execute(
    "UPDATE users SET password_hash = ? WHERE email = ?", (pwd_hash, new_email)
)
conn.commit()
conn.close()

print("Password successfully reset ho gaya hai!")