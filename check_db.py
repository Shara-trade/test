import sqlite3

conn = sqlite3.connect('asteroid_miner.db')
cursor = conn.cursor()

# Список всех таблиц
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('=== ТАБЛИЦЫ В БД ===')
for t in tables:
    print(f'  - {t[0]}')

# Проверяем таблицу admins
print('\n=== ТАБЛИЦА admins ===')
try:
    cursor.execute('SELECT * FROM admins')
    admins = cursor.fetchall()
    if admins:
        for a in admins:
            print(f'  admin_id={a[0]}, user_id={a[1]}, role={a[2]}')
    else:
        print('  ПУСТАЯ!')
except Exception as e:
    print(f'  ОШИБКА: {e}')

# ADMIN_IDS из config.py
print('\n=== ADMIN_IDS из config.py ===')
print('  [7852152665, 7014140645, 8126985873]')

conn.close()
