"""
LibraVerse - Administrator Password Reset Utility
Run this script anytime to reset or verify the administrator password.
Usage:
    python reset_admin.py [optional_new_password]
"""

import sys
from services.auth_service import hash_password, get_connection

def reset_password(new_password='Admin@LibraVerse2026'):
    conn = get_connection('instance/library.db')
    cursor = conn.cursor()
    
    # Check if admin exists
    cursor.execute("SELECT id, username, email FROM admins WHERE username = 'admin'")
    admin = cursor.fetchone()
    
    hashed = hash_password(new_password)
    
    if admin:
        cursor.execute("UPDATE admins SET password_hash = ? WHERE id = ?", (hashed, admin['id']))
        conn.commit()
        print(f"[OK] Password updated for administrator '{admin['username']}' ({admin['email']})")
    else:
        cursor.execute("""
            INSERT INTO admins (username, email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        """, ('admin', 'admin@libraverse.io', hashed, 'Chief Librarian Lyra', 'admin'))
        conn.commit()
        print("[OK] Created default administrator 'admin' with new password.")
        
    conn.close()
    print(f"Username: admin")
    print(f"Password: {new_password}")

if __name__ == '__main__':
    pwd = sys.argv[1] if len(sys.argv) > 1 else 'Admin@LibraVerse2026'
    reset_password(pwd)
